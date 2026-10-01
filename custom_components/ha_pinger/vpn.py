"""Authenticated bridge to the optional isolated WireGuard probe app."""

from urllib.parse import urlsplit

import aiohttp


def validate_agent_url(value):
    if not isinstance(value, str) or len(value) > 300:
        raise ValueError("Ungültige WireGuard-App-Adresse.")
    try:
        url = urlsplit(value)
        if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError
        if url.port is not None and not 1 <= url.port <= 65535:
            raise ValueError
    except ValueError as err:
        raise ValueError("Bitte die HTTP-/HTTPS-Adresse der WireGuard-App ohne Zugangsdaten eingeben.") from err
    return value.rstrip("/")


class AgentClient:
    def __init__(self, session, secrets):
        self.session, self.secrets = session, secrets

    async def request(self, method, path, data=None):
        if not self.secrets.get("agent_token"):
            raise ValueError("WireGuard-App noch nicht verbunden. Unter Netze die App-Verbindung einrichten.")
        url = validate_agent_url(self.secrets.get("agent_url", ""))
        try:
            async with self.session.request(method, url + path, json=data,
                headers={"Authorization": "Bearer " + self.secrets["agent_token"]},
                timeout=aiohttp.ClientTimeout(total=80), allow_redirects=False) as response:
                if response.status == 401:
                    raise ValueError("WireGuard-App: Zugriffsschlüssel stimmt nicht überein.")
                if response.status == 404 and path == "/active":
                    raise ValueError("Bitte auch die WireGuard-App auf Version 1.4.0 aktualisieren; sie unterstützt den Netzwechsel noch nicht.")
                payload = await response.json()
                if not isinstance(payload, dict):
                    raise ValueError("WireGuard-App hat eine ungültige Antwort gesendet.")
                if not 200 <= response.status < 300:
                    raise ValueError(str(payload.get("error", "WireGuard-App hat die Anfrage abgelehnt.")))
                return payload
        except (aiohttp.ClientError, TimeoutError) as err:
            raise ValueError("WireGuard-App nicht erreichbar. App-Start, Adresse und Zugriffsschlüssel prüfen.") from err

    async def check(self, target, settings):
        try:
            return await self.request("POST", "/check", {"profile_id": target["network_id"],
                "target": {k: target[k] for k in ("host", "method", "port", "web_scheme", "web_port", "web_path", "verify_tls", "availability_mode")},
                "settings": {k: settings[k] for k in ("timeout_seconds", "attempts")}})
        except ValueError as err:
            return {"online": None, "error": str(err), "resolved_ips": [], "checks": {}}

    async def activate(self, network_id):
        reply = await self.request("POST", "/active", {"profile_id": network_id})
        if reply.get("active_profile") != network_id:
            raise ValueError("Die WireGuard-App hat den Netzwechsel nicht bestätigt. App auf Version 1.4.0 aktualisieren.")
