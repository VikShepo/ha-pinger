"""Validation and monitoring engine, independent of Home Assistant.

All mutation happens on one asyncio event loop. The injected checker and notifier
perform I/O; configuration saves are serialized by the Home Assistant adapter.
"""

from __future__ import annotations

import asyncio
from copy import deepcopy
import ipaddress
import logging
import math
import re
import time
from uuid import uuid4

from . import history as timeline_history
from .ranges import describe_range, expand_range
from .icon_names import MDI_ICONS

_LOGGER = logging.getLogger(__name__)
MAX_TARGETS = 256
MAX_GROUPS = 64
GROUP_ICONS = ("network", "home", "router", "office", "server", "globe", "wifi", "storage")
TARGET_ICONS = ("auto", *GROUP_ICONS, "phone", "camera", "printer", "tv", "laptop")
HISTORY_LIMIT = 48
SETTINGS = {
    "interval_minutes": 5,
    "timeout_seconds": 2,
    "attempts": 2,
    "offline_after_seconds": 300,
    "notify_service": "",
    "sort_by": "manual",
    "sort_desc": False,
}
TARGET = {
    "name": "",
    "host": "",
    "kind": "ip",
    "method": "icmp",
    "port": 443,
    "interval_minutes": 0,
    "favorite": False,
    "notify": False,
    "notify_recovery": True,
    "notify_dns": False,
    "enabled": True,
    "group_id": "",
    "web_scheme": "http",
    "web_port": 80,
    "web_path": "/",
    "verify_tls": True,
    "availability_mode": "any",
    "icon": "auto",
    "image_id": "",
    "network_id": "",
}


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name}: ganze Zahl zwischen {low} und {high} erforderlich.")
    return value


def seconds_settings(data):
    data = dict(data)
    if "offline_after_minutes" in data:
        minutes = integer(data.pop("offline_after_minutes"), 0, 1440, "Ausfallverzögerung")
        data.setdefault("offline_after_seconds", minutes * 60)
    return data


def validate_settings(data):
    if not isinstance(data, dict):
        raise ValueError("Ungültige Einstellungen.")
    data = seconds_settings(data)
    if not isinstance(data, dict) or set(data) - SETTINGS.keys():
        raise ValueError("Unbekannte Einstellungen.")
    result = SETTINGS | data
    for key, low, high in (
        ("interval_minutes", 1, 1440), ("timeout_seconds", 1, 10),
        ("attempts", 1, 5), ("offline_after_seconds", 0, 86400),
    ):
        integer(result[key], low, high, key)
    service = result["notify_service"]
    if result["sort_by"] not in ("manual", "name", "address", "status", "last_checked") or type(result["sort_desc"]) is not bool:
        raise ValueError("Ungültige Sortierung.")
    if not isinstance(service, str) or (
        service and not re.fullmatch(r"notify\.mobile_app_[a-z0-9_]+", service)
    ):
        raise ValueError("Bitte einen Handy-Dienst der Home-Assistant-App auswählen.")
    return result


def validate_target(data):
    if not isinstance(data, dict) or set(data) - TARGET.keys():
        raise ValueError("Unbekannte Gerätefelder.")
    result = TARGET | data
    for key in ("name", "host"):
        if not isinstance(result[key], str):
            raise ValueError(f"{key} muss Text sein.")
        result[key] = result[key].strip()
    if not 1 <= len(result["name"]) <= 80:
        raise ValueError("Der Name muss 1 bis 80 Zeichen lang sein.")
    if result["kind"] not in ("ip", "ddns"):
        raise ValueError("Ungültiger Adresstyp.")
    if result["method"] not in ("icmp", "web", "both", "tcp"):
        raise ValueError("Bitte Ping, Web oder beides wählen.")
    if result["web_scheme"] not in ("http", "https"):
        raise ValueError("Bitte HTTP oder HTTPS wählen.")
    integer(result["web_port"], 1, 65535, "Web-Port")
    path = result["web_path"]
    if (not isinstance(path, str) or not path.startswith("/") or path.startswith("//")
            or len(path) > 1024 or any(ord(c) < 32 or ord(c) == 127 for c in path)
            or "#" in path or "\\" in path):
        raise ValueError("Web-Pfad muss mit / beginnen, z. B. / oder /status.")
    if result["availability_mode"] not in ("any", "all"):
        raise ValueError("Ungültige Regel für die Erreichbarkeit.")
    host = result["host"]
    if result["kind"] == "ip":
        try:
            if "%" in host:
                raise ValueError
            result["host"] = str(ipaddress.ip_address(host))
        except ValueError as err:
            raise ValueError("Bitte eine gültige IPv4- oder IPv6-Adresse eingeben.") from err
    else:
        try:
            host = host.rstrip(".").encode("idna").decode("ascii").lower()
        except UnicodeError as err:
            raise ValueError("Ungültiger Domainname.") from err
        labels = host.split(".")
        if len(host) > 253 or len(labels) < 2 or any(
            not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
            for label in labels
        ):
            raise ValueError("Bitte eine Domain ohne https://, Pfad oder Port eingeben.")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ValueError("Im DDNS-Tab bitte einen Domainnamen verwenden.")
        result["host"] = host
    integer(result["port"], 1, 65535, "Port")
    integer(result["interval_minutes"], 0, 1440, "Intervall")
    if not isinstance(result["group_id"], str):
        raise ValueError("Ungültige Gruppe.")
    if not isinstance(result["icon"], str) or (result["icon"] not in TARGET_ICONS and result["icon"] not in MDI_ICONS):
        raise ValueError("Bitte ein verfügbares Symbol auswählen.")
    if not isinstance(result["network_id"], str) or len(result["network_id"]) > 64:
        raise ValueError("Ungültiges Netz.")
    if not isinstance(result["image_id"], str) or (result["image_id"] and not re.fullmatch(r"[0-9a-f]{64}", result["image_id"])):
        raise ValueError("Ungültiges Bild.")
    for key in ("favorite", "notify", "notify_recovery", "notify_dns", "enabled", "verify_tls"):
        if type(result[key]) is not bool:
            raise ValueError(f"{key} muss ein Wahrheitswert sein.")
    return result


def validate_group(data):
    if not isinstance(data, dict) or set(data) - {"name", "icon", "ip_range"}:
        raise ValueError("Unbekannte Gruppenfelder.")
    result = {"name": "", "icon": "network", "ip_range": ""} | data
    if not isinstance(result["name"], str) or not 1 <= len(result["name"].strip()) <= 80:
        raise ValueError("Der Gruppenname muss 1 bis 80 Zeichen lang sein.")
    result["name"] = result["name"].strip()
    if not isinstance(result["icon"], str) or (result["icon"] not in GROUP_ICONS and result["icon"] not in MDI_ICONS):
        raise ValueError("Bitte ein verfügbares Gruppen-Icon auswählen.")
    if not isinstance(result["ip_range"], str):
        raise ValueError("Bitte einen IP-Bereich als Text eingeben.")
    result["ip_range"] = result["ip_range"].strip()
    if result["ip_range"]:
        result["ip_range"] = describe_range(result["ip_range"], MAX_TARGETS)["range"]
    return result


def fresh_state():
    return {
        "online": None, "latency_ms": None, "last_checked": None,
        "last_online": None, "offline_since": None, "outage_notified": False,
        "resolved_ips": [], "dns_baseline": [], "dns_notified_ips": [],
        "notification_error": None, "error": None, "detail": None, "history": [],
        "next_check": 0,
        "checks": {},
        "timeline": {}, "log": [], "last_notification": None,
        "notification_next_attempt": 0,
    }


class Monitor:
    def __init__(self, checker, notifier, changed=lambda: None, clock=time.time, network_switcher=None):
        self.checker = checker
        self.notifier = notifier
        self.changed = changed
        self.clock = clock
        self.settings = dict(SETTINGS)
        self.targets = {}
        self.groups = {}
        self.networks = {}
        self.active_network = ""
        self.switching_network = False
        self.network_switcher = network_switcher
        self.states = {}
        self.events = []
        self.checked = set()
        self.checking = set()
        self._jobs = {}
        self._notification_jobs = {}
        self._semaphore = asyncio.Semaphore(8)

    def load(self, data):
        """New installations start empty; updates keep saved addresses."""
        if data is None:
            return
        self.settings = validate_settings(data["settings"])
        self.networks = deepcopy(data.get("networks", {}))
        active = data.get("active_network", "")
        self.active_network = active if active in self.networks else ""
        for item in data.get("groups", []):
            self.groups[item["id"]] = validate_group({k: v for k, v in item.items() if k != "id"})
        for item in data["targets"]:
            target_id = item["id"]
            self.targets[target_id] = validate_target({k: v for k, v in item.items() if k != "id"})
            if self.targets[target_id]["group_id"] not in self.groups:
                self.targets[target_id]["group_id"] = ""
            saved = deepcopy(data.get("states", {}).get(target_id, {}))
            timeline_history.migrate(saved, self.clock())
            state = fresh_state() | saved
            state["history"] = state["history"][-HISTORY_LIMIT:]
            state["next_check"] = 0
            self.states[target_id] = state
        self.events = data.get("events", [])[-80:]

    def dump(self):
        return deepcopy({
            "settings": self.settings,
            "targets": [dict(target, id=key) for key, target in self.targets.items()],
            "groups": [dict(group, id=key) for key, group in self.groups.items()],
            "networks": self.networks,
            "active_network": self.active_network,
            "states": self.states,
            "events": self.events,
        })

    def snapshot(self):
        rows = []
        for key, target in self.targets.items():
            state = self.states[key]
            status = "unknown"
            if not target["enabled"] or target["network_id"] != self.active_network:
                status = "paused"
            elif key in self.checked:
                status = "error" if state["error"] else (
                    "online" if state["online"] else "offline"
                )
            history = state["history"]
            light_state = {k: v for k, v in state.items() if k not in ("timeline", "log")}
            rows.append(dict(target, id=key, **light_state, status=status,
                             notification_status=self.notification_status(target, state),
                             address_sort_key=(f"{ipaddress.ip_address(target['host']).version}:{int(ipaddress.ip_address(target['host'])):039d}"
                                               if target["kind"] == "ip" else "dns:" + target["host"]),
                             checking=key in self.checking,
                             availability=round(100 * sum(p["online"] for p in history) / len(history), 1)
                             if history else None))
        return deepcopy({"settings": self.settings, "targets": rows, "events": self.events,
                         "active_network": self.active_network, "switching_network": self.switching_network,
                         "networks": [dict(network, id=key) for key, network in self.networks.items()],
                         "groups": [dict(group, id=key) for key, group in self.groups.items()]})

    def event(self, kind, target, message, target_id=None):
        target_id = target_id or next((key for key, row in self.targets.items() if row is target or row == target), None)
        entry = {"time": self.clock(), "kind": kind, "target_id": target_id,
                 "name": target.get("name", "System"), "message": message}
        self.events.append(entry)
        self.events = self.events[-80:]
        if target_id in self.states:
            self.states[target_id]["log"].append(entry)
            timeline_history.prune(self.states[target_id], self.clock())

    def notification_status(self, target, state):
        if not target["notify"]:
            return "Glocke ausgeschaltet"
        if not self.settings["notify_service"]:
            return "Kein Handy ausgewählt"
        if state.get("notification_error"):
            return state["notification_error"]
        if not target["enabled"] or target["network_id"] != self.active_network:
            return "Überwachung pausiert"
        if state["outage_notified"]:
            return "Ausfallmeldung an den Handy-Dienst übergeben"
        if state["online"] is False and state["offline_since"] is not None:
            remaining = max(0, math.ceil(state["offline_since"] + self.settings["offline_after_seconds"] - self.clock()))
            return f"Ausfall-Wartezeit: noch {remaining} Sekunden" if remaining else "Ausfall-Push ist zum Versand vorgemerkt"
        return "Bereit für Ausfallmeldungen" if state["online"] is True else "Warte auf ein gültiges Prüfergebnis"

    def get_history(self, target_id):
        if target_id not in self.states:
            raise ValueError("Adresse nicht gefunden.")
        state = self.states[target_id]
        timeline_history.prune(state, self.clock())
        return deepcopy({"timeline": state["timeline"], "log": state["log"], "now": self.clock()})

    def clear_log(self, target_id):
        if target_id not in self.states:
            raise ValueError("Adresse nicht gefunden.")
        self.states[target_id]["log"] = []
        self.events = [event for event in self.events if event.get("target_id") != target_id]
        self.changed()

    def upsert(self, data, target_id=None):
        if target_id is not None and target_id not in self.targets:
            raise ValueError("Diese Adresse wurde bereits gelöscht.")
        if target_id is None and len(self.targets) >= MAX_TARGETS:
            raise ValueError(f"Maximal {MAX_TARGETS} Adressen möglich.")
        old = self.targets.get(target_id)
        target = validate_target((old or {}) | data)
        if target["group_id"] and target["group_id"] not in self.groups:
            raise ValueError("Diese Gruppe wurde bereits gelöscht.")
        if target["network_id"] and target["network_id"] not in self.networks:
            raise ValueError("Dieses Netz ist nicht eingerichtet.")
        if any(key != target_id and t["host"] == target["host"] and
               t["network_id"] == target["network_id"] and
               t["method"] == target["method"] and
               (t["method"] != "tcp" or t["port"] == target["port"])
               and (t["method"] not in ("web", "both") or all(
                   t[k] == target[k] for k in ("web_scheme", "web_port", "web_path")))
               for key, t in self.targets.items()):
            raise ValueError("Diese Adresse mit dieser Prüfmethode ist bereits vorhanden.")
        target_id = target_id or uuid4().hex
        probe_fields = ("host", "method", "port", "enabled", "web_scheme", "web_port",
                        "web_path", "verify_tls", "availability_mode", "network_id")
        if old is None or any(old[k] != target[k] for k in probe_fields):
            previous_state = self.states.get(target_id, {})
            self.targets[target_id] = target
            self.states[target_id] = fresh_state()
            if old and all(old[k] == target[k] for k in ("host", "network_id")):
                # Pausing or changing the check rule must not erase a device's history.
                for field in ("timeline", "log", "history", "last_online", "last_notification"):
                    self.states[target_id][field] = previous_state[field]
            self.checked.discard(target_id)
        else:
            if old["interval_minutes"] != target["interval_minutes"] or (not old["notify"] and target["notify"]):
                self.states[target_id]["next_check"] = 0
            if not old["notify"] and target["notify"]:
                self.states[target_id]["outage_notified"] = False
                self.states[target_id]["notification_error"] = None
            # Presentation/notification edits do not invalidate an in-flight probe.
            old.update(target)
        self.event("config", target, "Adresse hinzugefügt" if old is None else "Einstellungen geändert")
        self.changed()
        return target_id

    def remove(self, target_id):
        if target_id not in self.targets:
            raise ValueError("Adresse nicht gefunden.")
        target = self.targets.pop(target_id)
        self.states.pop(target_id)
        self.checked.discard(target_id)
        self.event("config", target, "Adresse gelöscht")
        self.changed()

    def configure(self, data):
        old = self.settings
        self.settings = validate_settings(self.settings | seconds_settings(data))
        if any(old[k] != self.settings[k] for k in SETTINGS if k not in ("sort_by", "sort_desc")):
            for state in self.states.values():
                state["next_check"] = 0
                if old["notify_service"] != self.settings["notify_service"]:
                    state["outage_notified"] = False
                    state["notification_error"] = None
                    state["notification_next_attempt"] = 0
        self.changed()

    def add_range(self, data, *, preview=False):
        data = dict(data)
        hosts = expand_range(data.pop("range", ""), MAX_TARGETS)
        prefix = data.pop("name", "")
        if not isinstance(prefix, str):
            raise ValueError("Der Namenszusatz muss Text sein.")
        prefix = prefix.strip()
        data.pop("kind", None)
        candidates, skipped = [], 0
        # Validate the complete batch against a detached configuration first.
        temporary = Monitor(None, None, clock=self.clock)
        temporary.targets = deepcopy(self.targets)
        temporary.groups = self.groups
        temporary.networks = self.networks
        for host in hosts:
            fields = data | {"name": f"{prefix} {host}".strip(), "host": host, "kind": "ip"}
            target = validate_target(fields)
            if any(t["host"] == host and t["network_id"] == target["network_id"] and t["method"] == target["method"]
                   and (t["method"] != "tcp" or t["port"] == target["port"])
                   and (t["method"] not in ("web", "both") or all(t[k] == target[k] for k in ("web_scheme", "web_port", "web_path")))
                   for t in temporary.targets.values()):
                skipped += 1
                continue
            temporary.upsert(target)
            candidates.append(target)
        result = {"count": len(candidates), "skipped": skipped, "first": hosts[0], "last": hosts[-1]}
        if not preview:
            result["ids"] = [self.upsert(target) for target in candidates]
        return result

    def preview_group_range(self, data, group_id=None):
        if not isinstance(data, dict) or set(data) != {"ip_range"}:
            raise ValueError("Bitte einen IP-Bereich angeben.")
        if group_id is not None and group_id not in self.groups:
            raise ValueError("Diese Gruppe wurde bereits gelöscht.")
        result = describe_range(data["ip_range"], MAX_TARGETS)
        addresses = set(expand_range(result["range"], MAX_TARGETS))
        members = [t for t in self.targets.values() if group_id and t["group_id"] == group_id and t["kind"] == "ip"]
        result["outside"] = [{"name": t["name"], "host": t["host"]} for t in members if t["host"] not in addresses]
        result["inside_count"] = len(members) - len(result["outside"])
        return result

    def upsert_group(self, data, group_id=None):
        if group_id is not None and group_id not in self.groups:
            raise ValueError("Diese Gruppe wurde bereits gelöscht.")
        if group_id is None and len(self.groups) >= MAX_GROUPS:
            raise ValueError(f"Maximal {MAX_GROUPS} Gruppen möglich.")
        group = validate_group(self.groups.get(group_id, {}) | data)
        if any(key != group_id and g["name"].casefold() == group["name"].casefold()
               for key, g in self.groups.items()):
            raise ValueError("Eine Gruppe mit diesem Namen ist bereits vorhanden.")
        group_id = group_id or uuid4().hex
        self.groups[group_id] = group
        self.event("config", group, "Gruppe gespeichert")
        self.changed()
        return group_id

    def remove_group(self, group_id):
        if group_id not in self.groups:
            raise ValueError("Gruppe nicht gefunden.")
        group = self.groups.pop(group_id)
        for target in self.targets.values():
            if target["group_id"] == group_id:
                target["group_id"] = ""
        self.event("config", group, "Gruppe gelöscht · Adressen bleiben erhalten")
        self.changed()

    def move(self, data, item_id):
        """Swap neighbours in the latest saved order, including across clients."""
        if set(data) != {"scope", "direction"} or data["scope"] not in ("targets", "groups"):
            raise ValueError("Ungültige Reihenfolge-Anfrage.")
        direction = data["direction"]
        if type(direction) is not int or direction not in (-1, 1):
            raise ValueError("Ungültige Richtung.")
        items = self.targets if data["scope"] == "targets" else self.groups
        if item_id not in items:
            raise ValueError("Eintrag wurde bereits gelöscht.")
        keys = list(items)
        siblings = keys if data["scope"] == "groups" else [
            key for key in keys if items[key]["kind"] == items[item_id]["kind"]
            and items[key]["group_id"] == items[item_id]["group_id"]
            and items[key]["network_id"] == items[item_id]["network_id"]
        ]
        destination = siblings.index(item_id) + direction
        if not 0 <= destination < len(siblings):
            return
        a, b = keys.index(item_id), keys.index(siblings[destination])
        keys[a], keys[b] = keys[b], keys[a]
        reordered = {key: items[key] for key in keys}
        # Keep target objects intact: active checks still refer to these objects.
        items.clear()
        items.update(reordered)
        if data["scope"] == "targets":
            self.settings["sort_by"] = "manual"
        self.changed()

    async def select_network(self, network_id):
        if network_id and network_id not in self.networks:
            raise ValueError("Netz nicht gefunden.")
        self.switching_network = True
        self.changed()
        try:
            await self.stop_checks()
            if self.network_switcher:
                await self.network_switcher(network_id)
            if self.active_network != network_id:
                self.active_network = network_id
                self.checked.clear()
                for state in self.states.values():
                    state.update(online=None, error=None, offline_since=None, outage_notified=False,
                                 notification_error=None, notification_next_attempt=0, next_check=0)
            self.changed()
        finally:
            self.switching_network = False
            self.changed()

    def start_due(self, *, force=False, target_id=None):
        """Reserve only individual targets; other targets remain independently runnable."""
        if target_id is not None and target_id not in self.targets:
            raise ValueError("Adresse nicht gefunden.")
        if target_id is not None and not self.targets[target_id]["enabled"]:
            raise ValueError("Diese Adresse ist pausiert. Bitte zuerst die Überwachung aktivieren.")
        if target_id is not None and self.targets[target_id]["network_id"] != self.active_network:
            raise ValueError("Bitte zuerst zu diesem Netz wechseln.")
        if self.switching_network:
            return []
        now, jobs = self.clock(), []
        for key, target in self.targets.items():
            if key in self._jobs or not target["enabled"] or target["network_id"] != self.active_network or (target_id is not None and target_id != key):
                continue
            if not force and self.states[key]["next_check"] > now:
                continue
            self.checking.add(key)
            job = asyncio.create_task(self._check(key, target))
            self._jobs[key] = job
            job.add_done_callback(lambda done, key=key: self._job_done(key, done))
            jobs.append(job)
        if jobs:
            self.changed()
        return jobs

    def _job_done(self, key, job):
        if self._jobs.get(key) is job:
            self._jobs.pop(key, None)
            self.checking.discard(key)
        if not job.cancelled() and job.exception():
            _LOGGER.error("Check task failed for %s", key, exc_info=job.exception())
        self.changed()

    async def run_due(self, *, force=False, target_id=None):
        jobs = self.start_due(force=force, target_id=target_id)
        if not jobs:
            return False
        results = await asyncio.gather(*(asyncio.shield(job) for job in jobs), return_exceptions=True)
        if any(isinstance(result, asyncio.CancelledError) for result in results):
            raise ValueError("Prüfung durch den Netzwechsel beendet.")
        for result in results:
            if isinstance(result, Exception):
                raise result
        await self.run_notifications_due()
        return True

    async def stop_checks(self):
        jobs = list(self._jobs.values()) + list(self._notification_jobs.values())
        for job in jobs:
            job.cancel()
        await asyncio.gather(*jobs, return_exceptions=True)
        self.checking.clear()

    def start_notifications_due(self):
        """Deliver elapsed outage timers independently of the probe interval."""
        if self.switching_network:
            return []
        now, jobs = self.clock(), []
        for key, target in self.targets.items():
            state = self.states[key]
            if (key in self._notification_jobs or key in self.checking or key not in self.checked
                    or not target["enabled"] or not target["notify"]
                    or target["network_id"] != self.active_network or state["online"] is None
                    or state["notification_next_attempt"] > now):
                continue
            outage = (state["online"] is False and not state["outage_notified"]
                      and state["offline_since"] is not None
                      and now >= state["offline_since"] + self.settings["offline_after_seconds"])
            recovery = state["online"] is True and state["outage_notified"] and target["notify_recovery"]
            if not (outage or recovery):
                continue
            job = asyncio.create_task(self._deliver_status(key, target, state, outage))
            self._notification_jobs[key] = job
            job.add_done_callback(lambda done, key=key: self._notification_done(key, done))
            jobs.append(job)
        return jobs

    def _notification_done(self, key, job):
        if self._notification_jobs.get(key) is job:
            self._notification_jobs.pop(key, None)
        if not job.cancelled() and job.exception():
            _LOGGER.error("Notification task failed for %s", key, exc_info=job.exception())
        self.changed()

    async def run_notifications_due(self):
        jobs = self.start_notifications_due()
        if jobs:
            await asyncio.gather(*(asyncio.shield(job) for job in jobs))

    async def _deliver_status(self, key, target, state, outage):
        if (self.targets.get(key) is not target or self.states.get(key) is not state
                or not target["enabled"] or not target["notify"]
                or target["network_id"] != self.active_network
                or state["online"] is not (False if outage else True)):
            return
        offline_since = state["offline_since"]
        if outage:
            seconds = max(0, int(self.clock() - state["offline_since"]))
            title = f"Nicht erreichbar · {target['name']}"
            message = f"{target['name']} ({target['host']}) ist nicht erreichbar. Seit {seconds} Sekunden keine erfolgreiche Prüfung. {state['detail'] or ''}"
        else:
            title = f"Wieder erreichbar · {target['name']}"
            message = f"{target['name']} ({target['host']}) ist wieder erreichbar."
        sent = await self._send(target, state, title, message)
        # A newer measurement may have arrived while the service call was running.
        if sent:
            if not outage and state["online"] is True:
                state["outage_notified"] = False
            elif outage and (state["online"] is True or state["offline_since"] == offline_since):
                state["outage_notified"] = True
            state["notification_next_attempt"] = 0
        else:
            state["notification_next_attempt"] = self.clock() + 30
        self.changed()

    async def _send(self, target, state, title, message):
        service = self.settings["notify_service"]
        if not service:
            state["notification_error"] = "Kein Handy ausgewählt. In den Einstellungen einen Handy-Dienst speichern."
            return False
        try:
            self.event("push_attempt", target, f"Push-Aufruf an {service}: {title}")
            await self.notifier(service, title, message)
        except Exception as err:  # A push failure must never stop monitoring.
            state["notification_error"] = "Push konnte nicht zugestellt werden. Handy-Dienst prüfen."
            _LOGGER.warning("Notification failed: %s", err)
            self.event("push_error", target, f"{state['notification_error']} Dienst: {service}. {err}")
            return False
        state["notification_error"] = None
        state["last_notification"] = self.clock()
        self.event("push", target, f"{title} · an {service} übergeben")
        return True

    async def _check(self, key, target):
        async with self._semaphore:
            if self.targets.get(key) is not target:
                return
            self.checking.add(key)
            self.changed()
            try:
                try:
                    result = await self.checker(target, dict(self.settings))
                except Exception:
                    _LOGGER.exception("Unexpected check error for %s", target["host"])
                    result = {"online": None, "error": "Prüffehler. Home-Assistant-Protokoll prüfen."}
                # Editing/deleting during I/O must not resurrect an old result.
                if self.targets.get(key) is not target:
                    return
                state = self.states[key]
                now = self.clock()
                interval = target["interval_minutes"] or self.settings["interval_minutes"]
                state["next_check"] = now + interval * 60
                previous = state["online"]
                previous_error = state["error"]
                state.update({"online": result.get("online"), "error": result.get("error"),
                              "detail": result.get("detail"),
                              "checks": result.get("checks", {}),
                              "latency_ms": result.get("latency_ms"), "last_checked": now})
                self.checked.add(key)
                timeline_history.record(state, now, state["online"])
                if state["error"] and state["error"] != previous_error:
                    self.event("error", target, state["error"])
                ips = sorted(set(result.get("resolved_ips", [])))
                state["resolved_ips"] = ips
                if ips:
                    baseline = state["dns_baseline"]
                    if baseline and baseline != ips:
                        self.event("dns", target, "DNS geändert: " + ", ".join(ips))
                    state["dns_baseline"] = ips
                    if not state["dns_notified_ips"] or not (target["notify"] and target["notify_dns"]):
                        state["dns_notified_ips"] = ips
                    elif state["dns_notified_ips"] != ips and await self._send(
                        target, state, f"DNS geändert · {target['name']}",
                        f"{target['host']} zeigt jetzt auf {', '.join(ips)}.",
                    ):
                        state["dns_notified_ips"] = ips
                online = state["online"]
                if online is None:
                    # A broken ping backend is not evidence of an unreachable host.
                    return
                state["history"] = (state["history"] + [{"time": now, "online": online}])[-HISTORY_LIMIT:]
                if online:
                    state["last_online"] = now
                    if not (target["notify"] and target["notify_recovery"]):
                        state["outage_notified"] = False
                    state["offline_since"] = None
                else:
                    # A new outage must be independent of a failed recovery push.
                    if previous is True:
                        state["outage_notified"] = False
                    if state["offline_since"] is None:
                        state["offline_since"] = now
                if previous is not online:
                    state["notification_next_attempt"] = 0
                    self.event("online" if online else "offline", target,
                               "Wieder erreichbar" if online else "Keine Antwort")
            finally:
                self.checking.discard(key)
                self.changed()
