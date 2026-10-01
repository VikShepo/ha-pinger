package main

import (
	"context"
	"crypto/ecdh"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"net/http/httptest"
	"net/netip"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func keys(t *testing.T) (string, string) {
	t.Helper()
	key, err := ecdh.X25519().GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	return base64.StdEncoding.EncodeToString(key.Bytes()), base64.StdEncoding.EncodeToString(key.PublicKey().Bytes())
}
func fixture(private, public, address string, port int) string {
	return fmt.Sprintf("[Interface]\nPrivateKey = %s\nAddress = %s/24\n[Peer]\nPublicKey = %s\nEndpoint = 127.0.0.1:%d\nAllowedIPs = 10.240.0.0/24\nPersistentKeepalive = 0\n", private, address, public, port)
}
func freePort(t *testing.T) int {
	t.Helper()
	c, err := net.ListenPacket("udp4", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer c.Close()
	return c.LocalAddr().(*net.UDPAddr).Port
}

func TestRealWireGuardPingAndHTTP(t *testing.T) {
	privateA, publicA := keys(t)
	privateB, publicB := keys(t)
	portA, portB := freePort(t), freePort(t)
	a, err := openTunnel(fixture(privateA, publicB, "10.240.0.1", portB))
	if err != nil {
		t.Fatal(err)
	}
	defer a.close()
	b, err := openTunnel(fixture(privateB, publicA, "10.240.0.2", portA))
	if err != nil {
		t.Fatal(err)
	}
	defer b.close()
	if err = a.dev.IpcSet(fmt.Sprintf("listen_port=%d\n", portA)); err != nil {
		t.Fatal(err)
	}
	if err = b.dev.IpcSet(fmt.Sprintf("listen_port=%d\n", portB)); err != nil {
		t.Fatal(err)
	}
	listener, err := b.net.ListenTCPAddrPort(netip.MustParseAddrPort("10.240.0.2:8080"))
	if err != nil {
		t.Fatal(err)
	}
	server := &http.Server{Handler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/status" {
			t.Errorf("Unexpected path %s", r.URL.Path)
		}
		w.WriteHeader(202)
	})}
	go server.Serve(listener)
	defer server.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	target := target{Host: "10.240.0.2", Method: "both", Scheme: "http", WebPort: 8080, Path: "/status", VerifyTLS: true, Mode: "all"}
	result := a.probe(ctx, target, checkSettings{Timeout: 3, Attempts: 2})
	if result.Online == nil || !*result.Online {
		t.Fatalf("Real tunnel check failed: %+v", result)
	}
	if result.Checks["ping"].Online == nil || !*result.Checks["ping"].Online {
		t.Fatal("ICMP through tunnel failed")
	}
	if result.Checks["web"].HTTPStatus != 202 {
		t.Fatal("HTTP did not cross WireGuard tunnel")
	}
}

func TestProfilePersistenceAndAuthenticatedAPI(t *testing.T) {
	private, _ := keys(t)
	_, public := keys(t)
	directory := t.TempDir()
	m, err := newManager(directory)
	if err != nil {
		t.Fatal(err)
	}
	token := strings.Repeat("x", 40)
	api := handler(m, token)
	unauthorized := httptest.NewRecorder()
	api.ServeHTTP(unauthorized, httptest.NewRequest("GET", "/health", nil))
	if unauthorized.Code != 401 {
		t.Fatal("Missing authentication")
	}
	body, _ := json.Marshal(profile{Name: "Office", Config: fixture(private, public, "10.240.0.1", freePort(t))})
	request := httptest.NewRequest("POST", "/profiles", strings.NewReader(string(body)))
	request.Header.Set("Authorization", "Bearer "+token)
	response := httptest.NewRecorder()
	api.ServeHTTP(response, request)
	if response.Code != 200 {
		t.Fatal(response.Body.String())
	}
	if strings.Contains(response.Body.String(), private) || strings.Contains(response.Body.String(), "config") {
		t.Fatal("API exposed configuration secrets")
	}
	var saved profile
	json.Unmarshal(response.Body.Bytes(), &saved)
	if len(m.tunnels) != 0 {
		t.Fatal("Saving a profile must not activate its tunnel")
	}
	activate := httptest.NewRequest("POST", "/active", strings.NewReader(`{"profile_id":"`+saved.ID+`"}`))
	activate.Header.Set("Authorization", "Bearer "+token)
	activation := httptest.NewRecorder()
	api.ServeHTTP(activation, activate)
	if activation.Code != 200 || m.activeID != saved.ID || len(m.tunnels) != 1 {
		t.Fatal("Activation failed")
	}
	raw, err := os.ReadFile(filepath.Join(directory, "profiles.json"))
	if err != nil || !strings.Contains(string(raw), private) {
		t.Fatal("Configuration not persisted")
	}
	m.close()
	restored, err := newManager(directory)
	if err != nil {
		t.Fatal(err)
	}
	defer restored.close()
	if restored.profiles[saved.ID].Name != "Office" {
		t.Fatal("Profile not restored")
	}
	restored.tunnels[saved.ID].close()
	delete(restored.tunnels, saved.ID)
	restored.refresh()
	if restored.tunnels[saved.ID] == nil {
		t.Fatal("Inactive profile was not retried")
	}
	if _, err = restored.save(profile{ID: saved.ID, Name: "Renamed"}); err != nil {
		t.Fatal(err)
	}
	first := restored.tunnels[saved.ID]
	second, err := restored.save(profile{Name: "Other", Config: fixture(private, public, "10.240.0.5", freePort(t))})
	if err != nil {
		t.Fatal(err)
	}
	if len(restored.tunnels) != 1 {
		t.Fatal("Inactive profile opened a tunnel")
	}
	if err = restored.activate(second.ID); err != nil {
		t.Fatal(err)
	}
	if !first.closed || len(restored.tunnels) != 1 {
		t.Fatal("Old tunnel was not closed")
	}
	secondTunnel := restored.tunnels[second.ID]
	if err = restored.activate(""); err != nil {
		t.Fatal(err)
	}
	if !secondTunnel.closed || len(restored.tunnels) != 0 {
		t.Fatal("Home must disconnect all tunnels")
	}
	restored.refresh()
	if len(restored.tunnels) != 0 {
		t.Fatal("Refresh restarted an inactive tunnel")
	}
	if err = restored.remove(second.ID); err != nil {
		t.Fatal(err)
	}
	if err = restored.remove(saved.ID); err != nil {
		t.Fatal(err)
	}
	if len(restored.profiles) != 0 {
		t.Fatal("Profile not removed")
	}
}

func TestConfigRejectsHooksAndInvalidKeys(t *testing.T) {
	private, _ := keys(t)
	_, public := keys(t)
	valid := fixture(private, public, "10.240.0.1", 51820)
	if _, err := parseConfig(valid); err != nil {
		t.Fatal(err)
	}
	for _, raw := range []string{strings.Replace(valid, "Address =", "PostUp = echo hello\nAddress =", 1), strings.Replace(valid, private, "invalid", 1), strings.Replace(valid, "10.240.0.0/24", "bad", 1)} {
		if _, err := parseConfig(raw); err == nil {
			t.Fatal("Invalid config accepted")
		}
	}
}
