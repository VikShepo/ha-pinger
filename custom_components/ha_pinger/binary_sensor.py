"""Native connectivity entities for dashboards, history and automations."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    hub = entry.runtime_data
    known = {}

    @callback
    def synchronize():
        for target_id in list(known):
            if target_id not in hub.targets:
                entity = known.pop(target_id)
                registry = er.async_get(hass)
                registry_id = registry.async_get_entity_id(
                    "binary_sensor", DOMAIN, f"{DOMAIN}_{target_id}",
                )
                if registry_id:
                    registry.async_remove(registry_id)
                elif entity.hass is not None and entity.entity_id:
                    hass.async_create_task(entity.async_remove())
        added = []
        for target_id in hub.targets:
            if target_id not in known:
                known[target_id] = entity = PingSensor(hub, target_id)
                added.append(entity)
        if added:
            async_add_entities(added)

    # Remove registry leftovers if a previous shutdown interrupted a deletion.
    registry = er.async_get(hass)
    valid_ids = {f"{DOMAIN}_{target_id}" for target_id in hub.targets}
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.unique_id not in valid_ids:
            registry.async_remove(entity.entity_id)
    entry.async_on_unload(hub.listen(synchronize))
    synchronize()


class PingSensor(BinarySensorEntity):
    _attr_should_poll = False
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, hub, target_id):
        self.hub = hub
        self.target_id = target_id
        self._attr_unique_id = f"{DOMAIN}_{target_id}"

    @property
    def name(self):
        prefix = "Netzwerk" if self.hub.language == "de" else "Network"
        return f"{prefix} {self.hub.targets.get(self.target_id, {}).get('name', '')}".strip()

    @property
    def available(self):
        target = self.hub.targets.get(self.target_id)
        state = self.hub.states.get(self.target_id)
        return bool(target and target["enabled"] and state and not state["error"]
                    and self.target_id in self.hub.checked)

    @property
    def is_on(self):
        return self.hub.states.get(self.target_id, {}).get("online")

    @property
    def extra_state_attributes(self):
        target = self.hub.targets.get(self.target_id, {})
        state = self.hub.states.get(self.target_id, {})
        return {"host": target.get("host"), "method": target.get("method"),
                "latency_ms": state.get("latency_ms"), "resolved_ips": state.get("resolved_ips"),
                "last_checked": state.get("last_checked"), "error": state.get("error"),
                "checks": state.get("checks", {}), "detail": state.get("detail"),
                "availability_mode": target.get("availability_mode", "any")}

    async def async_added_to_hass(self):
        self.async_on_remove(self.hub.listen(self._changed))

    @callback
    def _changed(self):
        if self.target_id in self.hub.targets:
            self.async_write_ha_state()
