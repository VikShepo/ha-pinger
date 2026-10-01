# Network Control Center WireGuard

[Deutsch](DOCS.md) · [English](DOCS.en.md)

**English:** Optional Home Assistant app for saved WireGuard networks. Checks remote addresses with ping, HTTP/HTTPS or TCP. Only the selected network has an active tunnel; switching to the home network closes it. An isolated network stack preserves HA's host routes. Supports aarch64 and amd64. Manage networks from the Network Control Center integration. Fresh installations have no profiles.

**Deutsch:**

Optionale HA-App für gespeicherte WireGuard-Netze im Network Control Center 1.5.0. Sie prüft entfernte Adressen per Ping, HTTP/HTTPS oder TCP. Nur das ausgewählte Netz hat einen aktiven Tunnel. Beim Wechsel ins Heimnetz wird er geschlossen. Der eigene Netzwerkstack innerhalb des Prozesses lässt die HA-Verbindung und die Routen des Raspberry Pi unverändert.

Unterstützt aarch64 und amd64. Kein Host-Netzwerk, kein TUN-Gerät und keine zusätzlichen Netzwerkprivilegien erforderlich. Bedienung über die Integration unter **Netze**. Die App startet ohne Profile.

Siehe [Installation und Bedienung](DOCS.md).
