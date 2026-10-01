# Network Control Center 1.5.0

## Deutsch

- Oberfläche, Dialoge, Statusmeldungen und Push-Nachrichten auf Deutsch und Englisch.
- **Einstellungen → Sprache:** HA-Sprache automatisch übernehmen oder Deutsch/English speichern. Namen eigener Geräte und Gruppen bleiben unverändert.
- Angenehmer Dunkelmodus: Schwarzgrau (`#282828`), hellere Karten (`#333333`) und besser lesbare Statusfarben.
- Beschreibung und Anleitung in beiden Sprachen, einschließlich WireGuard-Einrichtung.

**Aktualisieren:** In HACS Version 1.5.0 herunterladen, Home Assistant neu starten und Browser/Companion-App neu laden. Alternativ den vollständigen Ordner `custom_components/ha_pinger` aus dem ZIP ersetzen, einschließlich der neuen Übersetzungsdateien. Gespeicherte Geräte, Einstellungen und Verläufe bleiben erhalten. Die optionale WireGuard-App erhält ebenfalls übersetzte Konfigurationsfelder.

**Icon in HACS:** Die Icon-Dateien sind enthalten. „Icon not available“ in HACS 2.0.5 bleibt ein [offenes HACS-Problem](https://github.com/hacs/integration/issues/5223). Dieses Release behebt den HACS-Fehler nicht. HA 2026.3+ unterstützt die mitgelieferten Icons unter Geräte & Dienste.

## English

- Interface, dialogs, status messages and push notifications in German and English.
- **Settings → Language:** follow the HA language or save Deutsch/English. User-defined names remain unchanged.
- Softer dark theme: charcoal background (`#282828`), lighter cards (`#333333`) and clearer status colors.
- Bilingual descriptions and documentation, including WireGuard setup.

**Update:** Download version 1.5.0 in HACS, restart Home Assistant and reload your browser/Companion app. For manual updates, replace the complete `custom_components/ha_pinger` folder, including the new translation files. Existing devices, settings and history are preserved. The optional WireGuard app also gains translated configuration labels.

**HACS icon:** Icon assets are included. HACS 2.0.5 still has an [open issue](https://github.com/hacs/integration/issues/5223) displaying bundled integration icons. This release does not fix that HACS issue. HA 2026.3+ supports the bundled icons in Devices & services.

Tests cover both languages, desktop/mobile layouts and localized notification payloads at the simulated HA service boundary. Real phone delivery and operation on the user's Pi are not confirmed by these tests.
