"""One Home Assistant service-call path for tests and monitoring alerts."""
import asyncio

from .const import PANEL_PATH


async def send_mobile_push(hass, service, title, message):
    domain, name = service.split(".", 1)
    if not hass.services.has_service(domain, name):
        raise ValueError("Der ausgewählte Handy-Dienst ist nicht verfügbar.")
    async with asyncio.timeout(15):
        await hass.services.async_call(domain, name, {
            "title": title, "message": message,
            "data": {"url": f"/{PANEL_PATH}", "clickAction": f"/{PANEL_PATH}"},
        }, blocking=True)
