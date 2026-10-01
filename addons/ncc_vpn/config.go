package main

import (
	"bufio"
	"context"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"
	"net"
	"net/netip"
	"strconv"
	"strings"
	"time"
)

type tunnelConfig struct {
	addresses, dns []netip.Addr
	mtu            int
	ipc            string
	refresh        string
}

func parseConfig(raw string) (tunnelConfig, error) {
	result := tunnelConfig{mtu: 1420}
	if len(raw) == 0 || len(raw) > 32768 {
		return result, errors.New("WireGuard-Datei muss 1 bis 32768 Bytes enthalten.")
	}
	sections := []map[string]string{}
	kinds := []string{}
	var current map[string]string
	scanner := bufio.NewScanner(strings.NewReader(strings.TrimPrefix(raw, "\ufeff")))
	for line := 1; scanner.Scan(); line++ {
		value := strings.TrimSpace(strings.SplitN(scanner.Text(), "#", 2)[0])
		if value == "" {
			continue
		}
		if value == "[Interface]" || value == "[Peer]" {
			current = map[string]string{}
			sections = append(sections, current)
			kinds = append(kinds, value)
			continue
		}
		pair := strings.SplitN(value, "=", 2)
		if len(pair) != 2 || current == nil {
			return result, fmt.Errorf("Ungültige Konfiguration in Zeile %d.", line)
		}
		key := strings.TrimSpace(pair[0])
		value = strings.TrimSpace(pair[1])
		if _, exists := current[key]; exists {
			return result, fmt.Errorf("Doppeltes Feld %s in Zeile %d.", key, line)
		}
		allowed := "PrivateKey Address DNS MTU ListenPort"
		if kinds[len(kinds)-1] == "[Peer]" {
			allowed = "PublicKey PresharedKey AllowedIPs Endpoint PersistentKeepalive"
		}
		if !strings.Contains(" "+allowed+" ", " "+key+" ") {
			return result, fmt.Errorf("Feld %s wird nicht unterstützt. Skript-Hooks und Systemrouten sind nicht erlaubt.", key)
		}
		current[key] = value
	}
	if len(sections) < 2 || len(sections) > 9 || kinds[0] != "[Interface]" {
		return result, errors.New("Eine Interface-Sektion und 1 bis 8 Peers erforderlich.")
	}
	iface := sections[0]
	private, err := keyHex(iface["PrivateKey"])
	if err != nil {
		return result, errors.New("PrivateKey ist ungültig.")
	}
	result.ipc = "private_key=" + private + "\n"
	for _, value := range strings.Split(iface["Address"], ",") {
		prefix, err := netip.ParsePrefix(strings.TrimSpace(value))
		if err != nil {
			return result, errors.New("Address muss eine IP mit Netzmaske enthalten.")
		}
		result.addresses = append(result.addresses, prefix.Addr())
	}
	if iface["DNS"] != "" {
		for _, value := range strings.Split(iface["DNS"], ",") {
			addr, err := netip.ParseAddr(strings.TrimSpace(value))
			if err != nil {
				return result, errors.New("DNS muss IP-Adressen enthalten.")
			}
			result.dns = append(result.dns, addr)
		}
	}
	if value := iface["MTU"]; value != "" {
		result.mtu, err = strconv.Atoi(value)
		if err != nil || result.mtu < 1280 || result.mtu > 9000 {
			return result, errors.New("MTU muss zwischen 1280 und 9000 liegen.")
		}
	}
	// ListenPort is deliberately not bound: independent profiles need separate
	// ephemeral UDP sockets. No interface, routes or firewall on the host change.
	for index, peer := range sections[1:] {
		if kinds[index+1] != "[Peer]" {
			return result, errors.New("Nur eine Interface-Sektion erlaubt.")
		}
		public, err := keyHex(peer["PublicKey"])
		if err != nil {
			return result, errors.New("PublicKey ist ungültig.")
		}
		result.ipc += "public_key=" + public + "\n"
		if value := peer["PresharedKey"]; value != "" {
			key, err := keyHex(value)
			if err != nil {
				return result, errors.New("PresharedKey ist ungültig.")
			}
			result.ipc += "preshared_key=" + key + "\n"
		}
		if len(peer["AllowedIPs"]) > 8192 {
			return result, errors.New("Zu viele AllowedIPs.")
		}
		for _, value := range strings.Split(peer["AllowedIPs"], ",") {
			prefix, err := netip.ParsePrefix(strings.TrimSpace(value))
			if err != nil {
				return result, errors.New("AllowedIPs enthält kein gültiges Netz.")
			}
			result.ipc += "allowed_ip=" + prefix.Masked().String() + "\n"
		}
		endpoint, err := resolveEndpoint(peer["Endpoint"])
		if err != nil || endpoint == nil || endpoint.IP == nil || endpoint.Port == 0 {
			return result, errors.New("Peer-Endpoint konnte nicht aufgelöst werden.")
		}
		result.ipc += "endpoint=" + endpoint.String() + "\n"
		result.refresh += "public_key=" + public + "\nendpoint=" + endpoint.String() + "\n"
		keepalive := 25
		if value := peer["PersistentKeepalive"]; value != "" {
			keepalive, err = strconv.Atoi(value)
			if err != nil || keepalive < 0 || keepalive > 65535 {
				return result, errors.New("PersistentKeepalive ist ungültig.")
			}
		}
		result.ipc += "persistent_keepalive_interval=" + strconv.Itoa(keepalive) + "\n"
	}
	return result, nil
}

func resolveEndpoint(value string) (*net.UDPAddr, error) {
	host, portText, err := net.SplitHostPort(value)
	if err != nil {
		return nil, err
	}
	port, err := strconv.Atoi(portText)
	if err != nil || port < 1 || port > 65535 {
		return nil, errors.New("Ungültiger Endpoint-Port")
	}
	if address, err := netip.ParseAddr(host); err == nil {
		return net.UDPAddrFromAddrPort(netip.AddrPortFrom(address, uint16(port))), nil
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	addresses, err := net.DefaultResolver.LookupNetIP(ctx, "ip", host)
	if err != nil || len(addresses) == 0 {
		return nil, errors.New("Endpoint-DNS fehlgeschlagen")
	}
	return net.UDPAddrFromAddrPort(netip.AddrPortFrom(addresses[0], uint16(port))), nil
}

func keyHex(value string) (string, error) {
	raw, err := base64.StdEncoding.DecodeString(value)
	if err != nil || len(raw) != 32 {
		return "", errors.New("Ungültiger Schlüssel")
	}
	return hex.EncodeToString(raw), nil
}
