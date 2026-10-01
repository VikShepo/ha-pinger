"""Bounded DNS, ICMP, HTTP(S) and legacy TCP checks; no shell execution."""

import asyncio
import ipaddress
import socket
import time

import aiohttp
from icmplib import ICMPLibError, SocketPermissionError, async_ping


async def resolve_addresses(host, timeout):
    try:
        ipaddress.ip_address(host)
        addresses = [host]
    except ValueError:
        try:
            async with asyncio.timeout(timeout):
                records = await asyncio.get_running_loop().getaddrinfo(
                    host, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM,
                )
            addresses = sorted({record[4][0] for record in records},
                               key=lambda value: (":" in value, value))
        except (OSError, TimeoutError):
            return []
    return addresses


async def network_check(target, settings, addresses):
    timeout = settings["timeout_seconds"]
    attempts = settings["attempts"]
    if not addresses:
        return {"online": False, "detail": "DNS-Auflösung fehlgeschlagen."}

    async def probe(address):
        if target["method"] == "tcp":
            detail = f"TCP-Port {target['port']} antwortet nicht."
            for _ in range(attempts):
                start = time.monotonic()
                writer = None
                try:
                    async with asyncio.timeout(timeout):
                        _, writer = await asyncio.open_connection(address, target["port"])
                    return {"online": True, "latency_ms": round((time.monotonic() - start) * 1000, 2)}
                except ConnectionRefusedError:
                    detail = (f"TCP-Port {target['port']}: Verbindung abgelehnt. "
                              "Das Gerät oder eine Firewall antwortet, aber der Port ist geschlossen oder blockiert.")
                except TimeoutError:
                    detail = (f"TCP-Port {target['port']}: Zeitüberschreitung. "
                              "Port, Firewall und Netzwerkweg von Home Assistant prüfen.")
                except OSError:
                    detail = (f"TCP-Port {target['port']}: Netzwerkverbindung fehlgeschlagen. "
                              "Adresse und Netzwerkweg von Home Assistant prüfen.")
                finally:
                    if writer:
                        writer.close()
            return {"online": False, "detail": detail}
        # Unprivileged sockets work on HA OS; raw sockets cover other setups.
        for privileged in (False, True):
            try:
                answer = await async_ping(address, count=attempts, interval=0.2,
                                          timeout=timeout, privileged=privileged)
                return {"online": answer.is_alive,
                        "latency_ms": round(answer.avg_rtt, 2) if answer.is_alive else None,
                        "detail": None if answer.is_alive else (
                            "Keine ICMP-Antwort bei Home Assistant. Das Gerät kann trotzdem im Browser "
                            "erreichbar sein, wenn Ping blockiert wird. Wähle Web oder beides, "
                            "um den Webdienst ebenfalls zu prüfen.")}
            except SocketPermissionError:
                continue
            except ICMPLibError as err:
                return {"online": None, "error": f"ICMP-Prüffehler: {err}"}
        return {"online": None,
                "error": "ICMP-Berechtigung fehlt. Container-Netzwerk prüfen oder Web wählen."}

    # Cap DNS fan-out, but report all resolved addresses. Any responding address
    # means reachable; DNS alone never counts as a successful connectivity check.
    try:
        async with asyncio.timeout(attempts * (timeout + 0.2) + 3):
            results = await asyncio.gather(*(probe(address) for address in addresses[:8]))
    except TimeoutError:
        return {"online": None, "error": "Die Netzwerkprüfung hat ihr Zeitlimit überschritten."}
    result = next((r for r in results if r["online"] is True), None)
    if result is None:
        result = next((r for r in results if r["online"] is False), results[0])
    return result


def web_url(target):
    host = target["host"]
    if ":" in host:
        host = f"[{host}]"
    scheme = target.get("web_scheme", "http")
    port = target.get("web_port", 80)
    suffix = "" if port == (443 if scheme == "https" else 80) else f":{port}"
    return f"{scheme}://{host}{suffix}{target.get('web_path', '/')}"


async def web_check(target, settings, session):
    url = web_url(target)
    detail = "Webdienst antwortet nicht."
    for _ in range(settings["attempts"]):
        start = time.monotonic()
        try:
            # A redirect/login/error response also proves that the Web server
            # responds. Do not follow it to an unrelated server or read the body.
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=settings["timeout_seconds"]),
                allow_redirects=False, ssl=target.get("verify_tls", True),
                raise_for_status=False,
            ) as response:
                status = response.status
                detail = f"Webdienst antwortet mit HTTP {status}."
                if status in (401, 403):
                    detail += " Anmeldung oder Freigabe erforderlich; der Webdienst ist erreichbar."
                elif status >= 400:
                    detail += " Die Fehlerseite bestätigt die Erreichbarkeit; der Inhalt wurde nicht geprüft."
                elif 300 <= status < 400:
                    detail += " Weiterleitung empfangen; das Weiterleitungsziel wird nicht geprüft."
                response.close()
                return {"online": True, "latency_ms": round((time.monotonic() - start) * 1000, 2),
                        "http_status": status, "url": url, "detail": detail}
        except (aiohttp.ClientConnectorCertificateError, aiohttp.ClientSSLError):
            detail = ("HTTPS-Zertifikat oder TLS-Verbindung konnte nicht geprüft werden. "
                      "Bei einem eigenen Zertifikat die Zertifikatsprüfung in den Geräte-Einstellungen anpassen.")
        except TimeoutError:
            detail = "Webprüfung: Zeitüberschreitung. Protokoll, Port und Netzwerkweg von Home Assistant prüfen."
        except aiohttp.ClientConnectorError:
            detail = "Webverbindung fehlgeschlagen. Protokoll, Port, DNS und Firewall prüfen."
        except (aiohttp.ClientError, OSError):
            detail = "Keine gültige HTTP-Antwort. Protokoll und Web-Port prüfen."
    return {"online": False, "url": url, "detail": detail}


async def check_target(target, settings, *, session=None):
    addresses = await resolve_addresses(target["host"], settings["timeout_seconds"])
    method = target["method"]
    checks = {}
    names, jobs = [], []
    if method in ("icmp", "both", "tcp"):
        names.append("tcp" if method == "tcp" else "ping")
        jobs.append(network_check(target, settings, addresses))
    if method in ("web", "both"):
        names.append("web")
        jobs.append(web_check_with_session(target, settings, session))
    results = await asyncio.gather(*jobs)
    checks.update(zip(names, results))
    # Preserve unknown when a technical failure prevents a conclusive result.
    values = [result["online"] for result in results]
    if method == "both" and target.get("availability_mode", "any") == "all":
        online = False if False in values else None if None in values else True
    else:
        online = True if True in values else None if None in values else False
    errors = [result["error"] for result in results if result.get("error")]
    detail = " · ".join(f"{name.upper() if name == 'tcp' else name.title()}: "
                        f"{result.get('error') or result.get('detail') or ('Erreichbar' if result['online'] else 'Keine Antwort')}"
                        for name, result in checks.items())
    latencies = [result["latency_ms"] for result in results if result.get("latency_ms") is not None]
    return {"online": online, "error": "; ".join(errors) if online is None else None,
            "detail": detail, "latency_ms": min(latencies) if online and latencies else None,
            "resolved_ips": addresses, "checks": checks}


async def web_check_with_session(target, settings, session):
    if session is not None:
        return await web_check(target, settings, session)
    # Standalone tests use their own session; HA supplies its managed session.
    async with aiohttp.ClientSession(cookie_jar=aiohttp.DummyCookieJar()) as client:
        return await web_check(target, settings, client)
