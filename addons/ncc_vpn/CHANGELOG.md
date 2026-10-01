# 1.5.0

- Deutsch/English für die Konfigurationsfelder und Installationsanleitung.
- German/English configuration labels and installation documentation.
- Die Integration übersetzt WireGuard-Status und Fehler passend zur gewählten Sprache.
- The integration translates WireGuard status and errors into the selected language.

# 1.4.1

- Veröffentlichung im GitHub-Repository mit Installationsquelle für den HA-App-Store.
- WireGuard-Verhalten aus 1.4.0 bleibt erhalten.

# 1.4.0

- Gespeicherte Profile werden erst beim Aktivieren geöffnet.
- Beim Netzwechsel wird das bisherige Profil geschlossen; Heimnetz schließt alle Tunnel.
- Die aktive Auswahl bleibt bei Neustarts erhalten. Alte Installationen ohne gespeicherte Auswahl starten im Heimnetz.
- Endpoint-Aktualisierungen und Wiederherstellung gelten nur für das aktive Profil.
- Benötigt die Integration 1.4.0; andere Netze pausieren dort bis zum Aktivieren.
- Aktivieren, Wechseln, Schließen und Wiederherstellen mit lokalen WireGuard-Gegenstellen getestet.

# 1.3.0

- Gespeicherte WireGuard-Profile mit getrennten Netzwerkstacks.
- Ping, Web und TCP durch das zugeordnete Profil, parallele Prüfungen.
- Authentifizierte API; private Schlüssel bleiben im persistenten App-Speicher.
- Automatische erneute Endpoint-Auflösung und Wiederholungen nach Startfehlern.
- Lokaler Test mit zwei WireGuard-Gegenstellen und erfolgreicher Linux/arm64-Kompilierung.
