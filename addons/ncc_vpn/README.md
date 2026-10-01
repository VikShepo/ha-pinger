# Network Control Center WireGuard

Optionale HA-App für gespeicherte WireGuard-Netze im Network Control Center 1.4.1. Sie prüft entfernte Adressen per Ping, HTTP/HTTPS oder TCP. Nur das ausgewählte Netz hat einen aktiven Tunnel. Beim Wechsel ins Heimnetz wird er geschlossen. Der eigene Netzwerkstack innerhalb des Prozesses lässt die HA-Verbindung und die Routen des Raspberry Pi unverändert.

Unterstützt aarch64 und amd64. Kein Host-Netzwerk, kein TUN-Gerät und keine zusätzlichen Netzwerkprivilegien erforderlich. Bedienung über die Integration unter **Netze**. Die App startet ohne Profile.

Siehe [Installation und Bedienung](DOCS.md).
