## Network Control Center 1.4.1

- Gruppenbereiche werden beim Eingeben und vor dem Speichern geprüft. Anzahl, erste und letzte nutzbare Adresse werden angezeigt.
- Bereits zugeordnete IPs außerhalb des Bereichs werden kenntlich gemacht; bestehende Geräte bleiben erhalten.
- Die Range steht bei der Gruppenüberschrift im Dashboard, auch auf dem Handy.
- HACS-Unterstützung, ein HA-App-Repository und eine optionale Auto-Update-Blueprint sind enthalten.

Auch enthalten: Push-Wartezeit in Sekunden, einheitliche mobile Verlaufsbalken, Hell-/Dunkel-Schalter und WireGuard nur für das aktive Netz.

### Update

In HACS dieses Repository als benutzerdefinierte **Integration** hinzufügen und herunterladen. Alternativ den vollständigen Ordner `custom_components/ha_pinger` aus dem ZIP ersetzen. Danach Home Assistant neu starten und Browser/Companion-App neu laden. Geräte und gespeicherte Daten bleiben erhalten.

Für WireGuard die separate App ebenfalls aktualisieren. Die optionale Auto-Update-Blueprint installiert erkannte HACS-Updates; ein automatischer HA-Neustart ist standardmäßig ausgeschaltet.

Die Tests prüfen die Software mit lokalen Gegenstellen und simuliertem HA-Dienstaufruf. Die Zustellung an ein echtes Handy und der Betrieb auf einem konkreten Raspberry Pi sind dadurch nicht bestätigt.
