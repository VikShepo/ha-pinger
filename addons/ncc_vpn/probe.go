package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"crypto/tls"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/http"
	"net/netip"
	"strconv"
	"strings"
	"sync"
	"time"

	"golang.org/x/net/icmp"
	"golang.org/x/net/ipv4"
	"golang.org/x/net/ipv6"
	"golang.zx2c4.com/wireguard/conn"
	"golang.zx2c4.com/wireguard/device"
	"golang.zx2c4.com/wireguard/tun/netstack"
)

type result struct {
	Online     *bool    `json:"online"`
	Latency    *float64 `json:"latency_ms,omitempty"`
	Detail     string   `json:"detail,omitempty"`
	Error      string   `json:"error,omitempty"`
	HTTPStatus int      `json:"http_status,omitempty"`
	URL        string   `json:"url,omitempty"`
}
type checkResult struct {
	result
	Checks   map[string]result `json:"checks"`
	Resolved []string          `json:"resolved_ips"`
}
type target struct {
	Host      string `json:"host"`
	Method    string `json:"method"`
	Port      int    `json:"port"`
	Scheme    string `json:"web_scheme"`
	WebPort   int    `json:"web_port"`
	Path      string `json:"web_path"`
	VerifyTLS bool   `json:"verify_tls"`
	Mode      string `json:"availability_mode"`
}
type checkSettings struct {
	Timeout  int `json:"timeout_seconds"`
	Attempts int `json:"attempts"`
}
type tunnel struct {
	dev    *device.Device
	net    *netstack.Net
	hasDNS bool
	closed bool
	mutex  sync.RWMutex
}

func openTunnel(config string) (*tunnel, error) {
	parsed, err := parseConfig(config)
	if err != nil {
		return nil, err
	}
	tun, stack, err := netstack.CreateNetTUN(parsed.addresses, parsed.dns, parsed.mtu)
	if err != nil {
		return nil, errors.New("WireGuard-Netz konnte nicht erstellt werden.")
	}
	dev := device.NewDevice(tun, conn.NewDefaultBind(), device.NewLogger(device.LogLevelSilent, ""))
	if err = dev.IpcSet(parsed.ipc); err != nil {
		dev.Close()
		return nil, errors.New("WireGuard-Konfiguration wurde abgelehnt.")
	}
	if err = dev.Up(); err != nil {
		dev.Close()
		return nil, errors.New("WireGuard konnte nicht gestartet werden.")
	}
	return &tunnel{dev: dev, net: stack, hasDNS: len(parsed.dns) > 0}, nil
}
func (t *tunnel) close() {
	t.mutex.Lock()
	defer t.mutex.Unlock()
	if !t.closed {
		t.closed = true
		t.dev.Close()
	}
}
func (t *tunnel) refresh(config string) {
	parsed, err := parseConfig(config)
	if err != nil {
		return
	}
	t.mutex.RLock()
	defer t.mutex.RUnlock()
	if !t.closed {
		t.dev.IpcSet(parsed.refresh)
	}
}
func boolean(value bool) *bool { return &value }
func reachable(start time.Time) result {
	ms := float64(time.Since(start).Microseconds()) / 1000
	return result{Online: boolean(true), Latency: &ms}
}

func (t *tunnel) probe(ctx context.Context, config target, settings checkSettings) checkResult {
	t.mutex.RLock()
	defer t.mutex.RUnlock()
	out := checkResult{Checks: map[string]result{}, Resolved: []string{}}
	if t.closed {
		out.Error = "WireGuard-Profil wurde geändert. Bei der nächsten Prüfung erneut versuchen."
		return out
	}
	timeout := time.Duration(settings.Timeout) * time.Second
	if addr, err := netip.ParseAddr(config.Host); err == nil {
		out.Resolved = []string{addr.String()}
	} else if t.hasDNS {
		lookup, cancel := context.WithTimeout(ctx, timeout)
		addresses, err := t.net.LookupContextHost(lookup, config.Host)
		cancel()
		if err == nil {
			out.Resolved = addresses
		}
	}
	var mutex sync.Mutex
	var wait sync.WaitGroup
	run := func(name string, fn func() result) {
		wait.Add(1)
		go func() { defer wait.Done(); value := fn(); mutex.Lock(); out.Checks[name] = value; mutex.Unlock() }()
	}
	if config.Method == "icmp" || config.Method == "both" || config.Method == "tcp" {
		name := "ping"
		if config.Method == "tcp" {
			name = "tcp"
		}
		run(name, func() result {
			if len(out.Resolved) == 0 {
				return result{Online: boolean(false), Detail: "DNS-Auflösung im WireGuard-Netz fehlgeschlagen. DNS in der Konfiguration prüfen."}
			}
			type response struct{ r result }
			responses := make(chan response, 8)
			addresses := out.Resolved
			if len(addresses) > 8 {
				addresses = addresses[:8]
			}
			for _, address := range addresses {
				go func(address string) {
					var r result
					if config.Method == "tcp" {
						r = t.tcp(ctx, address, config.Port, settings)
					} else {
						r = t.ping(ctx, address, settings)
					}
					responses <- response{r}
				}(address)
			}
			final := result{Online: boolean(false), Detail: "Keine Antwort über WireGuard."}
			for range addresses {
				r := (<-responses).r
				if r.Online != nil && *r.Online {
					final = r
				}
			}
			return final
		})
	}
	if config.Method == "web" || config.Method == "both" {
		run("web", func() result { return t.web(ctx, config, settings) })
	}
	wait.Wait()
	yes, no, unknown := false, false, false
	for _, r := range out.Checks {
		if r.Online == nil {
			unknown = true
		} else if *r.Online {
			yes = true
			if out.Latency == nil || (r.Latency != nil && *r.Latency < *out.Latency) {
				out.Latency = r.Latency
			}
		} else {
			no = true
		}
	}
	if config.Method == "both" && config.Mode == "all" {
		if no {
			out.Online = boolean(false)
		} else if !unknown {
			out.Online = boolean(true)
		}
	} else {
		if yes {
			out.Online = boolean(true)
		} else if !unknown {
			out.Online = boolean(false)
		}
	}
	if out.Online == nil {
		out.Error = "Prüfung über WireGuard nicht eindeutig abgeschlossen."
	}
	details := []string{}
	for _, name := range []string{"ping", "web", "tcp"} {
		if r, ok := out.Checks[name]; ok {
			message := r.Detail
			if message == "" {
				message = "Erreichbar"
			}
			details = append(details, name+": "+message)
		}
	}
	out.Detail = strings.Join(details, " · ")
	return out
}

func (t *tunnel) tcp(ctx context.Context, host string, port int, settings checkSettings) result {
	for i := 0; i < settings.Attempts; i++ {
		attempt, cancel := context.WithTimeout(ctx, time.Duration(settings.Timeout)*time.Second)
		start := time.Now()
		socket, err := t.net.DialContext(attempt, "tcp", net.JoinHostPort(host, strconv.Itoa(port)))
		cancel()
		if err == nil {
			socket.Close()
			return reachable(start)
		}
	}
	return result{Online: boolean(false), Detail: "TCP-Port antwortet im WireGuard-Netz nicht."}
}
func (t *tunnel) ping(ctx context.Context, host string, settings checkSettings) result {
	addr, err := netip.ParseAddr(host)
	if err != nil {
		return result{Online: boolean(false), Detail: "Ungültige Ping-Adresse."}
	}
	for sequence := 0; sequence < settings.Attempts; sequence++ {
		if ctx.Err() != nil {
			break
		}
		socket, err := t.net.DialPingAddr(netip.Addr{}, addr)
		if err != nil {
			continue
		}
		deadline := time.Now().Add(time.Duration(settings.Timeout) * time.Second)
		if d, ok := ctx.Deadline(); ok && d.Before(deadline) {
			deadline = d
		}
		socket.SetDeadline(deadline)
		payload := make([]byte, 24)
		rand.Read(payload)
		var kind icmp.Type = ipv4.ICMPTypeEcho
		protocol := 1
		if addr.Is6() {
			kind = ipv6.ICMPTypeEchoRequest
			protocol = 58
		}
		message, _ := (&icmp.Message{Type: kind, Code: 0, Body: &icmp.Echo{Seq: sequence, Data: payload}}).Marshal(nil)
		start := time.Now()
		_, err = socket.Write(message)
		if err == nil {
			buffer := make([]byte, 1500)
			n, readErr := socket.Read(buffer)
			if readErr == nil {
				reply, parseErr := icmp.ParseMessage(protocol, buffer[:n])
				if parseErr == nil {
					echo, ok := reply.Body.(*icmp.Echo)
					if ok && echo.Seq == sequence && bytes.Equal(echo.Data, payload) {
						socket.Close()
						return reachable(start)
					}
				}
			}
		}
		socket.Close()
	}
	return result{Online: boolean(false), Detail: "Keine ICMP-Antwort über WireGuard."}
}
func (t *tunnel) web(ctx context.Context, config target, settings checkSettings) result {
	url := config.Scheme + "://" + net.JoinHostPort(config.Host, strconv.Itoa(config.WebPort)) + config.Path
	transport := &http.Transport{DialContext: t.net.DialContext, TLSClientConfig: &tls.Config{InsecureSkipVerify: !config.VerifyTLS}, DisableKeepAlives: true}
	defer transport.CloseIdleConnections()
	client := http.Client{Transport: transport, Timeout: time.Duration(settings.Timeout) * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	final := result{Online: boolean(false), URL: url, Detail: "Keine HTTP-Antwort über WireGuard. Protokoll, Port, Zertifikat und VPN-Verbindung prüfen."}
	for i := 0; i < settings.Attempts; i++ {
		request, err := http.NewRequestWithContext(ctx, "GET", url, nil)
		if err != nil {
			break
		}
		start := time.Now()
		response, err := client.Do(request)
		if err == nil {
			response.Body.Close()
			r := reachable(start)
			r.HTTPStatus = response.StatusCode
			r.URL = url
			r.Detail = fmt.Sprintf("Webdienst antwortet mit HTTP %d. Inhalt und Weiterleitungsziel werden nicht geprüft.", response.StatusCode)
			return r
		}
	}
	return final
}

func validateCheck(raw json.RawMessage) (target, checkSettings, error) {
	var request struct {
		Target   target        `json:"target"`
		Settings checkSettings `json:"settings"`
	}
	if err := json.Unmarshal(raw, &request); err != nil {
		return target{}, checkSettings{}, errors.New("Ungültige Anfrage.")
	}
	t, s := request.Target, request.Settings
	if len(t.Host) == 0 || len(t.Host) > 253 || strings.ContainsAny(t.Host, "/\\@\r\n \t") || s.Attempts < 1 || s.Attempts > 5 || s.Timeout < 1 || s.Timeout > 10 {
		return t, s, errors.New("Ungültige Adresse oder Prüfgrenzen.")
	}
	if t.Method != "icmp" && t.Method != "tcp" && t.Method != "web" && t.Method != "both" {
		return t, s, errors.New("Ungültige Prüfmethode.")
	}
	if t.Method == "tcp" && (t.Port < 1 || t.Port > 65535) {
		return t, s, errors.New("Ungültiger TCP-Port.")
	}
	if t.Method == "web" || t.Method == "both" {
		if (t.Scheme != "http" && t.Scheme != "https") || t.WebPort < 1 || t.WebPort > 65535 || len(t.Path) > 1024 || !strings.HasPrefix(t.Path, "/") || strings.HasPrefix(t.Path, "//") || strings.ContainsAny(t.Path, "\r\n\\#") {
			return t, s, errors.New("Ungültiges Webziel.")
		}
	}
	return t, s, nil
}
