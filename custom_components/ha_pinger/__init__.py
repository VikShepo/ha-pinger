"""Home Assistant adapter for the Network Control Center."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from pathlib import Path

import voluptuous as vol

from homeassistant.components import frontend, panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store

from .const import ASSET_PATH, DOMAIN, MODULE_URL, PANEL_PATH
from .model import Monitor
from .probe import check_target
from .media import ImageStore
from .vpn import AgentClient, validate_agent_url
from .notifications import send_mobile_push
from .i18n import language

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS = [Platform.BINARY_SENSOR]


class Hub(Monitor):
    def __init__(self, hass):
        self.hass = hass
        self.store = Store(hass, 1, DOMAIN, atomic_writes=True)
        self.secret_store = Store(hass, 1, DOMAIN + "_secrets", atomic_writes=True)
        self.secrets = {}
        self.images = ImageStore(hass.config.path(".storage", DOMAIN + "_images"))
        self.listeners = set()
        self.task = None
        self.ready = False
        self.publish_handle = None
        self.write_lock = asyncio.Lock()
        self.network_task = None
        self.next_network_sync = 0
        self.network_error = None
        self.network_ready = False
        async def checker(target, settings):
            if target["network_id"]:
                if not self.network_ready:
                    return {"online": None, "error": self.network_error or "WireGuard-Verbindung wird hergestellt."}
                return await self.agent().check(target, settings)
            return await check_target(target, settings, session=async_get_clientsession(hass))

        super().__init__(checker, self.notify, self.on_change, network_switcher=self.switch_tunnel)

    def agent(self):
        return AgentClient(async_get_clientsession(self.hass), self.secrets)

    @property
    def language(self):
        locale = self.settings.get("language", "auto")
        if locale == "auto":
            locale = self.hass.config.language
        return language(locale)

    async def notify(self, service, title, message):
        await send_mobile_push(self.hass, service, title, message, locale=self.language)

    async def switch_tunnel(self, network_id):
        if network_id or self.secrets.get("agent_token"):
            await self.agent().activate(network_id)
        self.network_ready = True
        self.network_error = None

    async def sync_network(self):
        async with self.write_lock:
            try:
                was_ready = self.network_ready
                await self.switch_tunnel(self.active_network)
                if not was_ready:
                    for state in self.states.values():
                        state["next_check"] = 0
            except ValueError as err:
                self.network_ready = False
                self.network_error = str(err)
            self.on_change()

    @callback
    def on_change(self):
        if not self.ready:
            return
        self.store.async_delay_save(self.dump, 5)
        if self.publish_handle is None:
            self.publish_handle = self.hass.loop.call_later(0.15, self.publish)

    @callback
    def publish(self):
        self.publish_handle = None
        for listener in tuple(self.listeners):
            listener()
        publish(self.hass)

    @callback
    def listen(self, listener):
        self.listeners.add(listener)
        return lambda: self.listeners.discard(listener)

    async def loop(self):
        while True:
            if self.clock() >= self.next_network_sync and (self.network_task is None or self.network_task.done()):
                self.next_network_sync = self.clock() + 30
                self.network_task = self.hass.async_create_background_task(self.sync_network(), "ha_pinger network sync")
            self.start_due()
            self.start_notifications_due()
            await asyncio.sleep(1)

    async def stop(self, _event=None):
        self.ready = False
        if self.network_task:
            self.network_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.network_task
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
            self.task = None
        await self.stop_checks()
        if self.publish_handle:
            self.publish_handle.cancel()
            self.publish_handle = None
        await self.store.async_save(self.dump())


def snapshot(hass):
    hub = hass.data[DOMAIN].get("hub")
    if hub is None:
        return {"available": False}
    data = hub.snapshot()
    data["available"] = True
    data["vpn"] = {"agent_url": hub.secrets.get("agent_url", "http://local-ncc-vpn:8099"),
                   "token_set": bool(hub.secrets.get("agent_token")), "error": hub.network_error}
    data["notify_services"] = sorted(
        f"notify.{name}" for name in hass.services.async_services().get("notify", {})
        if name.startswith("mobile_app_")
    )
    return data


@callback
def publish(hass):
    listeners = hass.data[DOMAIN]["listeners"]
    if listeners:
        data = snapshot(hass)
        for listener in tuple(listeners):
            listener(data)


async def async_setup(hass, config):
    hass.data.setdefault(DOMAIN, {"hub": None, "listeners": set(), "static": False})
    for command in (ws_subscribe, ws_get, ws_command, ws_history, ws_image):
        websocket_api.async_register_command(hass, command)
    return True


async def async_setup_entry(hass, entry):
    data = hass.data[DOMAIN]
    hub = Hub(hass)
    hub.secrets = await hub.secret_store.async_load() or {}
    hub.load(await hub.store.async_load())
    # Persist initial empty configuration and previously saved data.
    await hub.store.async_save(hub.dump())
    if not data["static"]:
        await hass.http.async_register_static_paths([
            StaticPathConfig(ASSET_PATH, str(Path(__file__).parent / "frontend"), False)
        ])
        data["static"] = True
    await panel_custom.async_register_panel(
        hass, frontend_url_path=PANEL_PATH, webcomponent_name="ha-pinger-panel",
        sidebar_title="Network Control Center", sidebar_icon="mdi:lan",
        module_url=MODULE_URL, require_admin=False,
    )
    frontend.add_extra_js_url(hass, MODULE_URL)
    data["hub"] = hub
    entry.runtime_data = hub
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        data["hub"] = None
        frontend.async_remove_panel(hass, PANEL_PATH)
        frontend.remove_extra_js_url(hass, MODULE_URL)
        raise
    hub.ready = True
    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, hub.stop))
    hub.task = hass.async_create_background_task(hub.loop(), "ha_pinger monitor")
    hub.publish()
    return True


async def async_unload_entry(hass, entry):
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.stop()
    hass.data[DOMAIN]["hub"] = None
    frontend.async_remove_panel(hass, PANEL_PATH)
    frontend.remove_extra_js_url(hass, MODULE_URL)
    publish(hass)
    return True


@websocket_api.websocket_command({"type": "ha_pinger/get"})
@callback
def ws_get(hass, connection, msg):
    connection.send_result(msg["id"], snapshot(hass))


@websocket_api.websocket_command({"type": "ha_pinger/subscribe"})
@callback
def ws_subscribe(hass, connection, msg):
    @callback
    def send(data):
        connection.send_event(msg["id"], data)

    listeners = hass.data[DOMAIN]["listeners"]
    listeners.add(send)
    connection.subscriptions[msg["id"]] = lambda: listeners.discard(send)
    connection.send_result(msg["id"])
    send(snapshot(hass))


@websocket_api.websocket_command({
    "type": "ha_pinger/command",
    vol.Required("action"): vol.In(["save", "delete", "settings", "check", "test_notify",
                                    "save_group", "delete_group", "move", "clear_log", "add_range", "preview_range", "preview_group_range",
                                    "agent_settings", "save_network", "delete_network", "test_agent", "select_network"]),
    vol.Optional("target_id"): str,
    vol.Optional("data", default={}): dict,
})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_command(hass, connection, msg):
    hub = hass.data[DOMAIN].get("hub")
    if hub is None:
        connection.send_error(msg["id"], "not_loaded", "Integration ist nicht geladen.")
        return
    action = msg["action"]
    target_id = msg.get("target_id")
    try:
        if action == "check":
            ran = await hub.run_due(force=True, target_id=target_id)
            if not ran:
                connection.send_error(msg["id"], "busy", "Diese Adresse wird bereits geprüft oder es gibt keine aktiven Adressen.")
                return
        elif action == "preview_range":
            connection.send_result(msg["id"], hub.add_range(msg["data"], preview=True))
            return
        elif action == "preview_group_range":
            connection.send_result(msg["id"], hub.preview_group_range(msg["data"], target_id))
            return
        elif action == "test_agent":
            await hub.agent().request("GET", "/health")
        elif action == "test_notify":
            if not hub.settings["notify_service"]:
                raise ValueError("Bitte zuerst ein Handy auswählen und speichern.")
            await hub.notify(hub.settings["notify_service"], "Network Control Center",
                             "Test erfolgreich. Hier erhältst du deine Netzwerk-Meldungen.")
        else:
            async with hub.write_lock:
                if action == "save":
                    fields = dict(msg["data"])
                    image_data = fields.pop("image_data", None)
                    previous = hub.targets.get(target_id, {}).get("image_id")
                    new_image = None
                    try:
                        if image_data:
                            new_image = await hass.async_add_executor_job(hub.images.put, image_data)
                            fields["image_id"] = new_image
                        hub.upsert(fields, target_id)
                    finally:
                        if new_image and not any(t["image_id"] == new_image for t in hub.targets.values()):
                            await hass.async_add_executor_job(hub.images.remove, new_image)
                elif action == "delete":
                    previous = hub.targets.get(target_id, {}).get("image_id")
                    hub.remove(target_id)
                elif action == "add_range":
                    hub.add_range(msg["data"])
                elif action == "clear_log":
                    hub.clear_log(target_id)
                elif action == "select_network":
                    await hub.select_network(target_id or "")
                elif action == "agent_settings":
                    fields = msg["data"]
                    agent_url = validate_agent_url(fields.get("agent_url", ""))
                    token = fields.get("agent_token") or hub.secrets.get("agent_token", "")
                    if not isinstance(token, str) or not 32 <= len(token) <= 256 or any(ord(c) <= 32 for c in token):
                        raise ValueError("Der Zugriffsschlüssel muss 32 bis 256 Zeichen ohne Leerzeichen enthalten.")
                    hub.secrets = {"agent_url": agent_url, "agent_token": token}
                    await hub.secret_store.async_save(hub.secrets)
                    hub.next_network_sync = 0
                elif action == "save_network":
                    fields = msg["data"]
                    name = fields.get("name", "")
                    if not isinstance(name, str):
                        raise ValueError("Der Netzname muss Text sein.")
                    name = name.strip()
                    config = fields.get("config", "")
                    if not 1 <= len(name) <= 80 or not isinstance(config, str) or len(config) > 32768:
                        raise ValueError("Netzname oder Konfigurationsdatei ungültig (max. 32 KB).")
                    profile = await hub.agent().request("POST", "/profiles", {"id": target_id or "", "name": name, "config": config})
                    hub.networks[profile["id"]] = {"name": profile["name"]}
                    hub.changed()
                elif action == "delete_network":
                    if target_id == hub.active_network:
                        raise ValueError("Bitte zuerst ins Heimnetz wechseln.")
                    if target_id not in hub.networks:
                        raise ValueError("Netz nicht gefunden.")
                    if any(t["network_id"] == target_id for t in hub.targets.values()):
                        raise ValueError("Dieses Netz enthält noch Adressen. Bitte zuerst verschieben oder löschen.")
                    await hub.agent().request("DELETE", "/profiles/" + target_id)
                    hub.networks.pop(target_id)
                    hub.changed()
                elif action == "settings":
                    hub.configure(msg["data"])
                elif action == "save_group":
                    hub.upsert_group(msg["data"], target_id)
                elif action == "delete_group":
                    hub.remove_group(target_id)
                elif action == "move":
                    hub.move(msg["data"], target_id)
                await hub.store.async_save(hub.dump())
                if action in ("save", "delete") and previous and not any(t["image_id"] == previous for t in hub.targets.values()):
                    await hass.async_add_executor_job(hub.images.remove, previous)
        hub.publish()
        connection.send_result(msg["id"], snapshot(hass))
    except (ValueError, TimeoutError) as err:
        connection.send_error(msg["id"], "invalid_request", str(err) or "Zeitüberschreitung beim Senden.")


@websocket_api.websocket_command({"type": "ha_pinger/history", vol.Required("target_id"): str})
@callback
def ws_history(hass, connection, msg):
    hub = hass.data[DOMAIN].get("hub")
    try:
        if hub is None:
            raise ValueError("Integration ist nicht geladen.")
        connection.send_result(msg["id"], hub.get_history(msg["target_id"]))
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_request", str(err))


@websocket_api.websocket_command({"type": "ha_pinger/image", vol.Required("image_id"): str})
@websocket_api.async_response
async def ws_image(hass, connection, msg):
    hub = hass.data[DOMAIN].get("hub")
    try:
        if hub is None or not any(t["image_id"] == msg["image_id"] for t in hub.targets.values()):
            raise ValueError("Bild nicht gefunden.")
        connection.send_result(msg["id"], await hass.async_add_executor_job(hub.images.read, msg["image_id"]))
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_request", str(err))
