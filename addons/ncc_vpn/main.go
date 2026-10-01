// Network Control Center's optional, unprivileged WireGuard probe service.
package main

import (
	"context"
	"crypto/rand"
	"crypto/subtle"
	"encoding/hex"
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"syscall"
	"time"
)

type profile struct {
	ID     string `json:"id"`
	Name   string `json:"name"`
	Config string `json:"config"`
}
type manager struct {
	mutex     sync.RWMutex
	directory string
	profiles  map[string]profile
	tunnels   map[string]*tunnel
	closed    bool
	activeID  string
}

var validID = regexp.MustCompile(`^[0-9a-f]{32}$`)

func newManager(directory string) (*manager, error) {
	if err := os.MkdirAll(directory, 0700); err != nil {
		return nil, err
	}
	m := &manager{directory: directory, profiles: map[string]profile{}, tunnels: map[string]*tunnel{}}
	raw, err := os.ReadFile(filepath.Join(directory, "profiles.json"))
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return nil, err
	}
	if err == nil {
		if json.Unmarshal(raw, &m.profiles) != nil || m.profiles == nil {
			return nil, errors.New("Gespeicherte Profile konnten nicht gelesen werden.")
		}
	}
	for id := range m.profiles {
		if !validID.MatchString(id) {
			return nil, errors.New("Ungültige gespeicherte Profil-ID.")
		}
	}
	active, err := os.ReadFile(filepath.Join(directory, "active-profile.json"))
	if err == nil {
		if json.Unmarshal(active, &m.activeID) != nil {
			return nil, errors.New("Aktives Netz konnte nicht gelesen werden.")
		}
	} else if !errors.Is(err, os.ErrNotExist) {
		return nil, err
	}
	if m.activeID != "" {
		p, exists := m.profiles[m.activeID]
		if !exists {
			return nil, errors.New("Aktives Profil fehlt.")
		}
		if t, err := openTunnel(p.Config); err == nil {
			m.tunnels[m.activeID] = t
		}
	}
	return m, nil
}
func (m *manager) persist(profiles map[string]profile) error {
	raw, err := json.Marshal(profiles)
	if err != nil {
		return err
	}
	return m.persistBytes("profiles.json", raw)
}
func (m *manager) persistBytes(name string, raw []byte) error {
	f, err := os.CreateTemp(m.directory, ".profiles-*")
	if err != nil {
		return err
	}
	temporary := f.Name()
	defer os.Remove(temporary)
	if err = f.Chmod(0600); err == nil {
		_, err = f.Write(raw)
	}
	if err == nil {
		err = f.Sync()
	}
	closeErr := f.Close()
	if err == nil {
		err = closeErr
	}
	if err != nil {
		return err
	}
	return os.Rename(temporary, filepath.Join(m.directory, name))
}
func copyProfiles(source map[string]profile) map[string]profile {
	out := map[string]profile{}
	for id, p := range source {
		out[id] = p
	}
	return out
}
func (m *manager) save(p profile) (profile, error) {
	p.Name = strings.TrimSpace(p.Name)
	if len([]rune(p.Name)) < 1 || len([]rune(p.Name)) > 80 {
		return p, errors.New("Netzname muss 1 bis 80 Zeichen enthalten.")
	}
	m.mutex.Lock()
	if p.ID == "" {
		if len(m.profiles) >= 16 {
			m.mutex.Unlock()
			return p, errors.New("Maximal 16 WireGuard-Netze möglich.")
		}
		id := make([]byte, 16)
		rand.Read(id)
		p.ID = hex.EncodeToString(id)
	} else if !validID.MatchString(p.ID) {
		m.mutex.Unlock()
		return p, errors.New("Ungültige Profil-ID.")
	}
	old, exists := m.profiles[p.ID]
	if !exists && len(m.profiles) >= 16 {
		m.mutex.Unlock()
		return p, errors.New("Maximal 16 WireGuard-Netze möglich.")
	}
	if p.Config == "" && exists {
		p.Config = old.Config
	}
	_, err := parseConfig(p.Config)
	if err != nil {
		m.mutex.Unlock()
		return p, err
	}
	var t *tunnel
	if p.ID == m.activeID {
		t, err = openTunnel(p.Config)
		if err != nil {
			m.mutex.Unlock()
			return p, err
		}
	}
	updated := copyProfiles(m.profiles)
	updated[p.ID] = p
	if err = m.persist(updated); err != nil {
		m.mutex.Unlock()
		if t != nil {
			t.close()
		}
		return p, errors.New("Konfiguration konnte nicht gespeichert werden.")
	}
	previous := m.tunnels[p.ID]
	m.profiles = updated
	if t != nil {
		m.tunnels[p.ID] = t
	}
	m.mutex.Unlock()
	if previous != nil {
		previous.close()
	}
	return p, nil
}
func (m *manager) remove(id string) error {
	m.mutex.Lock()
	if id == m.activeID {
		m.mutex.Unlock()
		return errors.New("Bitte zuerst ins Heimnetz wechseln.")
	}
	if _, ok := m.profiles[id]; !ok {
		m.mutex.Unlock()
		return errors.New("Netz nicht gefunden.")
	}
	updated := copyProfiles(m.profiles)
	delete(updated, id)
	if err := m.persist(updated); err != nil {
		m.mutex.Unlock()
		return errors.New("Netz konnte nicht gelöscht werden.")
	}
	t := m.tunnels[id]
	delete(m.tunnels, id)
	m.profiles = updated
	m.mutex.Unlock()
	if t != nil {
		t.close()
	}
	return nil
}
func (m *manager) close() {
	m.mutex.Lock()
	defer m.mutex.Unlock()
	m.closed = true
	for _, t := range m.tunnels {
		t.close()
	}
}
func (m *manager) refresh() {
	m.mutex.RLock()
	profiles := copyProfiles(m.profiles)
	tunnels := map[string]*tunnel{}
	for id, t := range m.tunnels {
		tunnels[id] = t
	}
	m.mutex.RUnlock()
	for id, p := range profiles {
		m.mutex.RLock()
		active := !m.closed && m.activeID == id
		m.mutex.RUnlock()
		if !active {
			continue
		}
		if t := tunnels[id]; t != nil {
			t.refresh(p.Config)
			continue
		}
		// Retry profiles that could not resolve their endpoint during startup.
		t, err := openTunnel(p.Config)
		if err != nil {
			continue
		}
		m.mutex.Lock()
		current, exists := m.profiles[id]
		keep := !m.closed && m.activeID == id && exists && current == p && m.tunnels[id] == nil
		if keep {
			m.tunnels[id] = t
		}
		m.mutex.Unlock()
		if !keep {
			t.close()
		}
	}
}
func (m *manager) activate(id string) error {
	m.mutex.Lock()
	defer m.mutex.Unlock()
	if m.closed {
		return errors.New("App wird beendet.")
	}
	if id == m.activeID && (id == "" || m.tunnels[id] != nil) {
		return nil
	}
	var next *tunnel
	if id != "" {
		p, exists := m.profiles[id]
		if !exists {
			return errors.New("Netz nicht gefunden.")
		}
		var err error
		next, err = openTunnel(p.Config)
		if err != nil {
			return err
		}
	}
	raw, _ := json.Marshal(id)
	if err := m.persistBytes("active-profile.json", raw); err != nil {
		if next != nil {
			next.close()
		}
		return errors.New("Netzwechsel konnte nicht gespeichert werden.")
	}
	for _, previous := range m.tunnels {
		previous.close()
	}
	m.tunnels = map[string]*tunnel{}
	if next != nil {
		m.tunnels[id] = next
	}
	m.activeID = id
	return nil
}
func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(value)
}
func failure(w http.ResponseWriter, status int, message string) {
	writeJSON(w, status, map[string]string{"error": message})
}

func handler(m *manager, token string) http.Handler {
	slots := make(chan struct{}, 16)
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		expected := "Bearer " + token
		if subtle.ConstantTimeCompare([]byte(r.Header.Get("Authorization")), []byte(expected)) != 1 {
			failure(w, 401, "Zugriffsschlüssel erforderlich.")
			return
		}
		if r.Method == "GET" && r.URL.Path == "/health" {
			m.mutex.RLock()
			active := m.activeID
			m.mutex.RUnlock()
			writeJSON(w, 200, map[string]any{"ready": true, "version": "1.4.1", "isolated": true, "active_profile": active})
			return
		}
		if r.Method == "POST" && r.URL.Path == "/active" {
			var value struct {
				ID *string `json:"profile_id"`
			}
			if json.NewDecoder(http.MaxBytesReader(w, r.Body, 1024)).Decode(&value) != nil || value.ID == nil {
				failure(w, 400, "Profil-ID erforderlich.")
				return
			}
			if err := m.activate(*value.ID); err != nil {
				failure(w, 400, err.Error())
				return
			}
			writeJSON(w, 200, map[string]string{"active_profile": *value.ID})
			return
		}
		if r.Method == "POST" && r.URL.Path == "/profiles" {
			var p profile
			if json.NewDecoder(http.MaxBytesReader(w, r.Body, 65536)).Decode(&p) != nil {
				failure(w, 400, "Ungültige oder zu große Konfiguration.")
				return
			}
			saved, err := m.save(p)
			if err != nil {
				failure(w, 400, err.Error())
				return
			}
			writeJSON(w, 200, map[string]string{"id": saved.ID, "name": saved.Name})
			return
		}
		if r.Method == "DELETE" && strings.HasPrefix(r.URL.Path, "/profiles/") {
			id := strings.TrimPrefix(r.URL.Path, "/profiles/")
			if !validID.MatchString(id) {
				failure(w, 400, "Ungültige Profil-ID.")
				return
			}
			if err := m.remove(id); err != nil {
				failure(w, 400, err.Error())
				return
			}
			writeJSON(w, 200, map[string]bool{"deleted": true})
			return
		}
		if r.Method != "POST" || r.URL.Path != "/check" {
			failure(w, 404, "Nicht gefunden.")
			return
		}
		var raw json.RawMessage
		if json.NewDecoder(http.MaxBytesReader(w, r.Body, 8192)).Decode(&raw) != nil {
			failure(w, 400, "Ungültige Anfrage.")
			return
		}
		var profileID struct {
			ID string `json:"profile_id"`
		}
		json.Unmarshal(raw, &profileID)
		config, settings, err := validateCheck(raw)
		if err != nil {
			failure(w, 400, err.Error())
			return
		}
		m.mutex.RLock()
		t := m.tunnels[profileID.ID]
		m.mutex.RUnlock()
		if t == nil {
			failure(w, 400, "WireGuard-Netz nicht aktiv. Endpoint prüfen; erneuter Verbindungsversuch erfolgt automatisch.")
			return
		}
		ctx, cancel := context.WithTimeout(r.Context(), 70*time.Second)
		defer cancel()
		select {
		case slots <- struct{}{}:
			defer func() { <-slots }()
		case <-ctx.Done():
			failure(w, 503, "Prüfkapazität belegt.")
			return
		}
		writeJSON(w, 200, t.probe(ctx, config, settings))
	})
}

func main() {
	directory := os.Getenv("NCC_DATA")
	if directory == "" {
		directory = "/data"
	}
	token := os.Getenv("NCC_TOKEN")
	if token == "" {
		var options struct {
			Token string `json:"api_token"`
		}
		raw, _ := os.ReadFile(filepath.Join(directory, "options.json"))
		json.Unmarshal(raw, &options)
		token = options.Token
	}
	if len(token) < 32 || len(token) > 256 || strings.ContainsAny(token, " \r\n\t") {
		log.Fatal("Bitte in der App-Konfiguration api_token mit mindestens 32 Zeichen setzen. Derselbe Schlüssel gehört in die Integration unter Netze > App verbinden.")
	}
	m, err := newManager(directory)
	if err != nil {
		log.Fatal("Gespeicherte WireGuard-Konfigurationen konnten nicht geladen werden.")
	}
	defer m.close()
	refreshContext, stopRefresh := context.WithCancel(context.Background())
	defer stopRefresh()
	go func() {
		ticker := time.NewTicker(2 * time.Minute)
		defer ticker.Stop()
		for {
			select {
			case <-refreshContext.Done():
				return
			case <-ticker.C:
				m.refresh()
			}
		}
	}()
	address := os.Getenv("NCC_LISTEN")
	if address == "" {
		address = ":8099"
	}
	server := &http.Server{Addr: address, Handler: handler(m, token), ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 10 * time.Second, WriteTimeout: 85 * time.Second, IdleTimeout: 60 * time.Second, MaxHeaderBytes: 8192}
	stopped := make(chan os.Signal, 1)
	signal.Notify(stopped, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-stopped
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		server.Shutdown(ctx)
	}()
	log.Print("Network Control Center WireGuard bereit. HA- und Host-Routen bleiben unverändert.")
	if err = server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		log.Fatal("API konnte nicht gestartet werden.")
	}
}
