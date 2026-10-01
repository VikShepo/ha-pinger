# Network Control Center für Home Assistant

Ein lokales Control Center mit den Tabs **IP-Adressen** und **DDNS**, einer eigenen Seite **Network Control Center** in der Home-Assistant-Seitenleiste und einer kompakten Dashboard-Kachel. Die Oberfläche ist auf Deutsch und für Desktop und Handy ausgelegt.

**Version 1.4.1: Neue Installationen starten leer.** Ausfallmeldungen verwenden denselben Handy-Dienst wie der Testknopf, mit einer Wartezeit in Sekunden und unabhängigen Wiederholungen bei gemeldeten Versandfehlern. Verlaufsbalken sind auch mobil sichtbar. Unter **Netze** aktivierst du ein gespeichertes WireGuard-Netz; der Wechsel ins Heimnetz schließt den Tunnel. Der Sonne-/Mond-Knopf schaltet das Control Center zwischen hell und dunkel um. Gerätebilder, 7.447 durchsuchbare Symbole, Gruppen, IP-Bereiche und der 30-Tage-Verlauf bleiben enthalten.

## Vorhandene Installation aktualisieren

### Mit HACS installieren und aktualisieren

1. In **HACS → ⋮ → Benutzerdefinierte Repositories** `https://github.com/VikShepo/ha-pinger` als Typ **Integration** hinzufügen.
2. **Network Control Center** suchen und herunterladen. Eine schon manuell eingerichtete Integration bleibt dabei bestehen.
3. Home Assistant neu starten und Browser/Companion-App neu laden.

Neue veröffentlichte GitHub-Releases werden von HACS erkannt und über eine eigene `update`-Entität angeboten. Die Erkennung erfolgt bei der nächsten HACS-Aktualisierung. [HACS: Releases](https://www.hacs.xyz/docs/publish/start/), [HACS: Update-Entitäten](https://www.hacs.xyz/docs/use/entities/update/).

**Optional automatisch installieren:** Die [Auto-Update-Blueprint](https://github.com/VikShepo/ha-pinger/blob/master/blueprints/automation/ha_pinger/release_update.yaml) unter **Einstellungen → Automatisierungen & Szenen → Blaupausen → Blaupause importieren** importieren. Daraus eine Automatisierung erstellen und die HACS-Update-Entität von Network Control Center auswählen. Die Blueprint ruft bei einem verfügbaren Update `update.install` auf. Der optionale automatische HA-Neustart ist standardmäßig ausgeschaltet. Ohne Neustart sind die neuen Dateien installiert und werden beim nächsten HA-Neustart geladen. Die Blueprint wird beim Installieren der Integration nicht automatisch aktiviert.

Die WireGuard-App wird separat über den HA-App-Store aktualisiert, siehe [WireGuard-Anleitung](addons/ncc_vpn/DOCS.md).

### Manuell über ZIP

1. Das neue ZIP entpacken. Den enthaltenen Ordner `HA-Pinger/custom_components/ha_pinger` vollständig über deinen bisherigen Ordner **`/homeassistant/custom_components/ha_pinger`** kopieren und vorhandene Dateien ersetzen. Je nach Installation heißt der Konfigurationsordner `/config` statt `/homeassistant`. `manifest.json` muss direkt in `custom_components/ha_pinger` liegen.
2. **Home Assistant vollständig neu starten.**
3. Den Browser mit **Strg + F5** neu laden bzw. die Companion-App vollständig neu laden.
4. **Network Control Center → Adresse bearbeiten → Prüfmethode**: Ping, Web oder beides auswählen. Für Web das Protokoll und den Port der Geräte-Weboberfläche eintragen.

Die Integration bleibt eingerichtet. Bereits gespeicherte Adressen, Gruppen, Favoriten, Push-Einstellungen und vorhandene Messungen bleiben erhalten. Die längere Historie wächst ab den tatsächlichen Prüfungen; fehlende frühere Daten bleiben grau. Eine neue Installation ohne gespeicherte Daten startet leer. Schon gespeicherte Einträge werden beim Update nicht automatisch gelöscht. Alternativ das Installationsskript wie unten erneut ausführen; dabei wird zusätzlich der bisherige Code gesichert.

**Bei WireGuard auch die mitgelieferte App auf 1.4.1 aktualisieren.** Integration und App benötigen beide dieses Update für das Aktivieren und Deaktivieren der Tunnel. Beim ersten Update von 1.3.0 ist das Heimnetz ausgewählt; gespeicherte Profile bleiben erhalten und können unter **Netze** aktiviert werden. Für HA OS auf deinem Raspberry Pi 5: [WireGuard installieren und aktualisieren](addons/ncc_vpn/DOCS.md). Die übrigen Funktionen benötigen nur die Integration.

Bestehende Push-Wartezeiten werden umgerechnet: **5 Minuten werden zu 300 Sekunden**. Für eine Meldung unmittelbar nach der ersten erfolglosen Prüfung in den Einstellungen **Ausfallmeldung nach · Sekunden = 0** setzen. Das Prüfintervall bleibt eine separate Einstellung.

## Schnell installieren

### Panel lädt nicht oder Integrations-Icon fehlt

Bei **„Unable to load custom panel …“** zuerst die angezeigte Versionsnummer prüfen. Das Paket 1.4.1 registriert `ha-pinger.js?v=1.4.1`. Wenn noch 1.3.0 angezeigt wird, den gesamten Ordner `custom_components/ha_pinger` aus **`HA-Pinger-Control-Center-1.4.1.zip`** ersetzen, Home Assistant vollständig neu starten und anschließend Browser bzw. Companion-App vollständig neu laden. Nur die Versionsnummer im Link zu ändern ersetzt keine Dateien.

Im File Editor müssen danach diese Dateien im tatsächlichen HA-Konfigurationsordner liegen:

```text
custom_components/ha_pinger/manifest.json         (version: 1.4.1)
custom_components/ha_pinger/const.py              (VERSION = "1.4.1")
custom_components/ha_pinger/frontend/ha-pinger.js
custom_components/ha_pinger/frontend/ha-pinger.css
custom_components/ha_pinger/brand/icon.png
custom_components/ha_pinger/brand/icon@2x.png
```

Der Ordner `brand` gehört direkt neben `frontend`. Die Integration und ihre `.storage`-Dateien müssen dafür nicht gelöscht werden. Lokale Integrations-Icons werden ab HA 2026.3 unterstützt. Falls das Panel mit aktuellem Code weiterhin nicht lädt, den vollständigen Browser-Konsolenfehler und etwaige fehlgeschlagene Dateiabrufe prüfen; die allgemeine Panel-Meldung allein nennt die Ursache nicht.

### Neue Installation

1. `dist/HA-Pinger-Control-Center.zip` auf dein Home-Assistant-System kopieren und entpacken, beispielsweise nach `/config/HA-Pinger`.
2. Im **Terminal-&-SSH-Add-on** ausführen:

   ```sh
   sh /config/HA-Pinger/install.sh /config
   ```

   Alternativ mit Python 3, auch unter Windows bei Zugriff auf den HA-Konfigurationsordner:

   ```sh
   python3 /config/HA-Pinger/install.py --config /config
   ```

3. **Home Assistant vollständig neu starten.** Das Neuladen der YAML-Konfiguration reicht nicht.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Network Control Center** auswählen und bestätigen.
5. **Network Control Center** in der Seitenleiste öffnen. Beide Tabs sind zunächst leer. Über **Hinzufügen** deine eigenen IP-Adressen oder Domains eintragen; danach beginnt die automatische Prüfung.

Der Installationsordner muss der echte Home-Assistant-Konfigurationsordner mit `configuration.yaml` sein. In manchen Terminal-Add-ons liegt er unter `/homeassistant`; dann diesen Pfad verwenden. Bei HA Container ist es der eingebundene Konfigurationsordner auf dem Host. Das Installationsskript greift nicht auf deine laufende HA-Instanz zu und startet sie nicht automatisch neu.

**Ohne Terminal:** Den Ordner `custom_components/ha_pinger` aus dem Paket nach `/config/custom_components/ha_pinger` kopieren; danach ab Schritt 3 fortfahren.

### Extrakachel im Dashboard

**Dashboard bearbeiten → Karte hinzufügen → Manuell**:

```yaml
type: custom:ha-pinger-card
title: Network Control Center
compact: true
```

Die Kachel zeigt Statuszahlen und bis zu fünf Favoriten. **Control Center öffnen** führt zur vollständigen Ansicht. Mit `compact: false` lässt sich die vollständige Oberfläche direkt als große Dashboard-Karte einbetten. Die Integration registriert das JavaScript automatisch; zusätzliche Karten aus HACS sind nicht erforderlich. Nach der ersten Einrichtung den Browser oder die Companion-App neu laden. Die Karte erscheint auch in der Auswahl als „Network Control Center“.

Falls „Custom element doesn't exist“ bestehen bleibt, unter **Einstellungen → Dashboards → Ressourcen** einmalig `/ha_pinger_static/ha-pinger.js?v=1.4.1` als **JavaScript-Modul** hinzufügen. Den erweiterten Modus im Benutzerprofil bei Bedarf einschalten.

## Funktionen

| Funktion | Bedienung |
| --- | --- |
| Standardintervall | Alle **5 Minuten**, in den Einstellungen von 1–1440 Minuten änderbar |
| Individuelles Intervall | Adresse bearbeiten; **0** übernimmt das Standardintervall |
| Status | Grün: erreichbar; Rot: keine Antwort; Gelb: Prüffehler; Grau: ungeprüft oder pausiert |
| Sofort prüfen | Pfeilkreis je Adresse; andere Einträge bleiben unabhängig prüfbar; alle aktiven Adressen oben |
| Adressen verwalten | Hinzufügen, Bearbeiten, Pausieren und Löschen mit Bestätigung |
| Favoriten | Stern je Adresse; optional ausschließlich anzeigen; eigene Reihenfolge bleibt erhalten |
| Gruppen | **Gruppe → Gruppe hinzufügen**; Name, durchsuchbare Icons und optionaler IP-Bereich |
| Reihenfolge | **Gruppe**: Gruppen und Adressen mit Pfeilen verschieben; sofort gespeichert |
| Sortieren | Manuell, Name, Adresse, Status oder letzte Prüfung; auf- oder absteigend |
| Bilder und Symbole | **Adresse bearbeiten**: Bild hochladen, ersetzen oder entfernen; voreingestelltes Symbol wählen |
| IP-Bereich | Beim Hinzufügen optional Start–Ende oder CIDR eingeben und Vorschau prüfen |
| Suche und Filter | Name, Adresse, Status |
| Push | Glocke je Adresse; ein auswählbares Handy für das Control Center |
| Ausfallverzögerung | 0–86.400 Sekunden ab erster fehlgeschlagener Prüfung; 0 = sofort |
| Entwarnung | Pro Adresse einschaltbar, nach zuvor gesendeter Ausfallmeldung |
| DDNS | Domain hinzufügen; DNS-Adressen, Verbindungsstatus und optionale Meldung bei DNS-Änderungen |
| Ping, Web oder beides | Beim Hinzufügen und Bearbeiten wählbar; getrennte Ergebnisse für Ping und Web |
| Webprüfung | HTTP/HTTPS, eigener Port und Pfad, wählbare HTTPS-Zertifikatsprüfung, HTTP-Status in den Details |
| Kombinierte Prüfregel | Bei „beides“: Mindestens eine oder beide Prüfungen müssen erfolgreich sein |
| Verlauf | Heartbeat-Button: 30 Tage als Tageszeilen; ein Strich entspricht 30 Minuten |
| Protokoll | Statuswechsel, Fehler und Push-Aufrufe; je Gerät leerbar, bis 30 Tage / 2.000 Einträge |
| Web öffnen | Bei Web/Beides öffnet der zusätzliche Button neben der Glocke die konfigurierte Adresse |
| WireGuard | Unter **Netze** Profile speichern und aktivieren; nur das aktive Netz wird geprüft; Heimnetz schließt den Tunnel |
| Hell/Dunkel | Sonne-/Mond-Knopf neben Einstellungen; Auswahl wird in diesem Browser gespeichert |
| HA-Entitäten | Eine native `binary_sensor`-Entität pro Adresse für eigene Automationen |
| Rechte | Angemeldete Benutzer sehen Status; Änderungen und manuelle Prüfungen erfordern ein Administratorkonto |

### Eigene Adressen hinzufügen

Bei einer neuen Installation sind Adressen, Gruppen und Verlauf leer. Über **Hinzufügen** trägst du deine eigenen Geräte ein. Push ist bei neuen Adressen zunächst ausgeschaltet. Maximal 256 konfigurierte Adressen werden unterstützt; es gibt keinen automatischen Subnetzscan.

### Bilder, Symbole und IP-Bereiche

Im Bearbeitungsdialog ein **Symbol** auswählen oder ein Bild als PNG, JPEG oder WebP bis 10 MB hochladen. Das Bild wird mittig auf **300 × 300 Pixel** zugeschnitten und als PNG gespeichert. Ein neues Bild ersetzt das alte. **Bild entfernen** zeigt wieder das ausgewählte Symbol; „Automatisch“ setzt die Symbolwahl zurück. Bilder werden nur angemeldeten HA-Benutzern bereitgestellt.

**Alle Symbole durchsuchen** öffnet für Geräte und Gruppen einen lokalen Katalog mit **7.447 Material Design Icons**. Suche nach Icon-Namen oder deutschen Begriffen wie „Kamera“, „Lager“, „WLAN“, „Heizung“ oder „Küche“. Ergebnisse werden seitenweise dargestellt. Die bisherigen Schnellauswahlen bleiben verfügbar. Quelle: [Pictogrammers / Material Design Icons](https://github.com/Templarian/MaterialDesign-SVG), Version 7.4.47; Lizenztexte liegen im Frontend-Ordner. Es werden zur Laufzeit keine Icons von externen Servern geladen.

Ein eigenes blaues Netzwerk-Icon ist für die Integration, die zusätzliche WireGuard-App und die Dashboard-Kachel enthalten. HA unterstützt lokal mitgelieferte Integrations-Icons ab Version 2026.3. [HA: Brand Images](https://developers.home-assistant.io/docs/core/integration/brand_images/).

Für mehrere IPs beim Hinzufügen **IP-Bereich** aktivieren. Beispiele: `192.168.1.20-192.168.1.30` oder `192.168.1.0/28`. IPv6 wird ebenfalls unterstützt. **Vorschau** zeigt die Anzahl. Gleiche Einträge mit gleicher Prüfmethode im gleichen Netz werden übersprungen. Gruppe, Netz und Prüfeinstellungen gelten für alle neuen Einträge. Der komplette Bereich wird vor dem Speichern geprüft; maximal 256 Adressen insgesamt. Dies legt die Adressen an, auch wenn sie gerade nicht antworten.

## Gruppen und Reihenfolge

Unter **Gruppe** lassen sich bis zu 64 Gruppen anlegen, umbenennen, mit einem Icon versehen und verschieben. Die Gruppen gelten für beide Tabs. Ordne eine Adresse beim Hinzufügen oder Bearbeiten einer Gruppe zu. Gruppen ohne passende Adressen werden in der normalen Ansicht ausgeblendet.

Beim Anlegen oder Bearbeiten einer Gruppe kannst du einen **IP-Bereich** speichern, zum Beispiel `192.168.1.10-192.168.1.30` oder `192.168.1.0/24`. Das Feld ist optional und lässt sich wieder leeren. Unter **Gruppe → Adressen aus Bereich hinzufügen** sind Bereich, Gruppenname und Gruppenzuordnung bereits vorausgefüllt. Wähle Prüfmethode und Netz, prüfe die Vorschau und speichere die Einträge. Der Bereich umfasst höchstens 256 Adressen. Das Speichern oder Ändern eines Gruppenbereichs allein fügt keine Geräte hinzu und entfernt keine vorhandenen Geräte.

Der Bereich wird schon beim Eingeben und erneut vor dem Speichern geprüft: gültige IPv4-/IPv6-Adressen, passende IP-Versionen, aufsteigende Grenzen, gültiges CIDR-Präfix und höchstens 256 nutzbare Adressen. Die Rückmeldung zeigt Anzahl sowie erste und letzte Adresse. CIDR-Eingaben werden auf die Netzadresse vereinheitlicht. Zugeordnete IPs außerhalb des Bereichs erscheinen als Hinweis; bestehende Einträge bleiben erhalten. DDNS-Namen werden dabei nicht auf einen IP-Bereich eingeschränkt. Diese Eingabeprüfung führt keine Ping- oder Webanfragen aus.

Im Dashboard steht die gespeicherte Range direkt bei der **Gruppenüberschrift**. Auf schmalen Bildschirmen bricht sie unter den Gruppennamen um.

Die Pfeile bei den Adressen ändern die Reihenfolge innerhalb ihrer Gruppe, ihres Tabs und Netzes und aktivieren die manuelle Sortierung. Über **Sortieren** lassen sich alternativ Name, Adresse, Status oder letzte Prüfung wählen. IPv4- und IPv6-Adressen werden numerisch sortiert. Änderungen werden in HA gespeichert. „Ohne Gruppe“ steht hinter den benannten Gruppen. Beim Löschen einer Gruppe bleiben die Adressen samt Verlauf erhalten. Favorisieren ändert die Reihenfolge nicht.

## Ping, Web oder beides

Die Prüfungen des **aktiven Netzes** laufen im Hintergrund, auch wenn das Dashboard geschlossen ist. Heimnetz-Adressen prüft der **Home-Assistant-Rechner**, zugeordnete WireGuard-Adressen die separate App. Standardmäßig wird alle fünf Minuten geprüft; das globale oder gerätespezifische Intervall gilt für beide Prüfungen. Bei „beides“ laufen Ping und Web parallel nach der DNS-Auflösung. Auch ausgefallene Geräte werden weiter geprüft. Eine manuelle Prüfung sperrt nur denselben Eintrag; insgesamt sind bis zu acht Geräteprüfungen gleichzeitig aktiv.

| Auswahl | Was wird geprüft? |
| --- | --- |
| Ping | Antwort auf ICMP-Ping |
| Web | Antwort eines HTTP- oder HTTPS-Webservers |
| Beides | Ping und Web; beide Ergebnisse erscheinen getrennt unter der Adresse |

**Ein Gerät kann im Browser erreichbar sein und dennoch nicht auf Ping antworten.** Manche Geräte oder Firewalls blockieren ICMP. Zudem kann der Netzwerkweg von deinem PC anders sein als der von Home Assistant. Die getrennten Ergebnisse zeigen beispielsweise „Ping rot, Web grün“.

Für `http://192.168.1.1/` wählst du **HTTP, Port 80, Pfad /**. Für `https://192.168.1.1:8443/status` wählst du **HTTPS, Port 8443, Pfad /status**. Die IP selbst kommt weiterhin ins Feld „IP-Adresse“. Beim Wechsel zwischen HTTP und HTTPS wird ein Standardport von 80 bzw. 443 angepasst; eigene Ports bleiben erhalten.

Bei **beides** gilt standardmäßig **mindestens eine Prüfung erfolgreich**: Web grün reicht dann für einen grünen Gesamtstatus. Optional kannst du **beide Prüfungen erfolgreich** wählen. Der Gesamtstatus, der Verlauf, die HA-Entität und Ausfallmeldungen folgen dieser Regel. Technische Prüffehler werden separat angezeigt; wenn deswegen kein eindeutiges Gesamtergebnis möglich ist, lautet der Gesamtstatus „Prüffehler“.

Die Webprüfung sendet einen GET-Aufruf und wertet die HTTP-Antwort aus. Auch eine Anmeldeseite (401/403), Weiterleitung (3xx) oder Fehlerseite (4xx/5xx) bestätigt, dass der Webserver antwortet. Der HTTP-Status bleibt sichtbar. Seiteninhalt und Weiterleitungsziel werden nicht geprüft. Es werden keine Zugangsdaten benötigt. HTTPS-Zertifikate werden standardmäßig geprüft; für Geräte mit eigenem Zertifikat lässt sich diese Prüfung je Adresse ausschalten. Bei einem falschen Protokoll, Port oder Zertifikatsproblem zeigen die Details den Hinweis.

Vorhandene **TCP-Einträge** bleiben kompatibel und bearbeitbar. TCP bestätigt nur einen offenen Port; die neue Webprüfung erwartet eine tatsächliche HTTP-Antwort.

## Push auf dein Handy

1. Die **Home Assistant Companion App** auf deinem Handy einrichten und Benachrichtigungen erlauben.
2. Im Control Center **Einstellungen** öffnen und bei **Push an dieses Handy** deinen `notify.mobile_app_…`-Dienst auswählen.
3. **Speichern**, Einstellungen erneut öffnen und **Gespeichertes Handy testen** drücken.
4. Die **Glocke** bei den gewünschten Adressen aktivieren.
5. Über **Bearbeiten** bei Bedarf Entwarnungen oder bei DDNS Meldungen zu DNS-Änderungen wählen.

Beispiel: Die erste erfolglose Prüfung endet um 12:00:00. Bei einer Wartezeit von **10 Sekunden** ist die Meldung ab 12:00:10 fällig, sofern das letzte Prüfergebnis weiterhin einen Ausfall zeigt. Dafür muss nicht die nächste reguläre Prüfung nach fünf Minuten abgewartet werden. **0 Sekunden** sendet unmittelbar nach der ersten erfolglosen Prüfung. Der Scheduler prüft jede Sekunde auf fällige Arbeit; laufende Geräteprüfungen und der Handy-Dienst können den Versand verzögern. Pro erkanntem Ausfall wird nach einem erfolgreichen Dienstaufruf nur einmal gemeldet.

Ein Ausfall zwischen zwei Prüfungen wird erst bei der nächsten Prüfung erkannt. Ein Timer misst die Zeit seit dem ersten beobachteten Ausfall; er kann keine durchgängige Unerreichbarkeit zwischen den Messungen bestätigen. Gibt der Handy-Dienst einen Fehler zurück, wird der Versand nach **30 Sekunden** erneut versucht, solange der Ausfall weiter besteht. Diese Wiederholungen laufen unabhängig vom Prüfintervall. Test und Ausfallmeldung verwenden denselben gespeicherten `notify.mobile_app_…`-Dienst. Ein erfolgreicher Dienstaufruf bestätigt die Übergabe an Home Assistant, aber keine tatsächliche Zustellung auf dem Handy. Nach einem Neustart bleiben gemeldete Ausfälle gespeichert, damit nicht bei jedem Neustart erneut alarmiert wird.

**Test kommt an, Ausfallmeldung fehlt:** Bei ausgefallenen Geräten steht der Push-Status direkt im Eintrag. Der Heartbeat-Button zeigt zusätzlich Restwartezeit, letzten Push-Aufruf und **Protokoll** mit dem genauen Handy-Dienst sowie zurückgegebenen Fehlern. Vorher gespeicherte 5 Minuten entsprechen weiterhin 300 Sekunden. Bei „Beides / mindestens eine Prüfung“ wird erst gemeldet, wenn Ping **und** Web ausfallen. Ein gelber technischer Prüffehler ist kein bestätigter Geräteausfall. Für einen kontrollierten Test die Ausfallverzögerung vorübergehend auf **0 Sekunden** setzen, die Glocke aktivieren, das gewünschte Gerät abschalten und **Jetzt prüfen** wählen. Danach die gewünschte Verzögerung wiederherstellen. Wenn „an den Handy-Dienst übergeben“ erscheint und das Handy trotzdem nichts zeigt, auch die Home-Assistant-Systemprotokolle für `mobile_app` und die Benachrichtigungseinstellungen des Handys prüfen.

## 30-Tage-Verlauf und Protokoll

Die kurzen Verlaufsbalken sind sowohl am PC als auch auf dem Handy in jedem Geräteeintrag sichtbar. Der Heartbeat-Button öffnet die Details mit **30 Tageszeilen**. Jeder Strich fasst 30 Minuten zusammen: Rot bedeutet mindestens eine beobachtete erfolglose Prüfung, Gelb einen technischen Fehler, Grün eine erfolgreiche Prüfung und Grau keine Messung. Antippen zeigt den Zeitraum. Die Uhrzeit richtet sich nach deinem Browser. Ein späterer erfolgreicher Test übermalt einen früheren beobachteten Ausfall im gleichen Zeitraum nicht.

**Protokoll** zeigt Statuswechsel, Konfigurationsänderungen, Prüffehler und Push-Aufrufe mit Zeitstempel. **Protokoll leeren** löscht diese Meldungen für das Gerät, der Tagesverlauf bleibt erhalten. Beides wird bis zu 30 Tage gespeichert; das Protokoll ist zusätzlich auf 2.000 Meldungen begrenzt. Pausieren und Änderungen der Prüfmethode behalten den Verlauf. Beim Wechsel der Zieladresse oder des Netzes beginnt ein neuer Verlauf. Ausfälle zwischen zwei Messungen lassen sich nicht nachträglich feststellen.

## DDNS und Netzwerkbedingungen

- Im DDNS-Tab einen **Domainnamen ohne `https://`, Pfad oder Port** eintragen, beispielsweise `zuhause.example.org`.
- Die DNS-Auflösung wird bei jeder Prüfung erneut angefragt. Caches des Systems oder DNS-Servers können Änderungen bis zum Ablauf ihrer TTL verzögern.
- Ping bzw. bestehende TCP-Einträge prüfen bis zu acht aufgelöste Adressen parallel. Eine antwortende Adresse genügt für dieses Prüfergebnis. Web verwendet den Domainnamen einschließlich HTTPS-Zertifikatsprüfung; der HTTP-Client wählt die Verbindung aus den DNS-Adressen. Alle aufgelösten IPs werden angezeigt. Einzelne fehlerhafte A/AAAA-Adressen benötigen bei Bedarf eigene Einträge im IP-Tab.
- Eine DNS-Auflösung allein führt nicht zu Grün. Die ausgewählte Prüfregel muss erfüllt sein.
- **DDNS-Adressen werden überwacht, nicht beim DDNS-Anbieter aktualisiert.** Zugangsdaten eines DDNS-Anbieters werden nicht benötigt.
- Für Heimnetz-Prüfungen braucht Home Assistant eine Route zur Zieladresse. Unter **Netze → Aktivieren** wird das gewählte WireGuard-Profil geöffnet und das bisherige geschlossen. **Heimnetz → Aktivieren** schließt den Tunnel. Nur Adressen des aktiven Netzes werden geprüft; Prüfungen und Ausfall-Timer anderer Netze pausieren. Verlauf und Protokoll bleiben erhalten. Beim Wechsel beginnt eine frische Prüfung. Die Netzauswahl gilt gemeinsam für alle Benutzer und Browser. [Einrichtung und Grenzen](addons/ncc_vpn/DOCS.md).
- Manche Router blockieren ICMP oder NAT-Loopback. Bei DDNS kann eine interne Prüfung daher anders ausfallen als eine Prüfung aus dem Internet.
- Wenn ICMP-Berechtigungen fehlen, erscheint ein Prüffehler für Ping. Bei Container-Installationen die Netzwerkkonfiguration bzw. ICMP-Berechtigungen prüfen oder Web verwenden.
- Der Prozentwert ist der Anteil erfolgreicher Prüfungen im gespeicherten Verlauf, keine zeitgewichtete Verfügbarkeit. Während HA ausgeschaltet ist, finden keine Prüfungen statt. Nach einem Neustart wird zunächst „Ungeprüft“ gezeigt, bis frische Ergebnisse vorliegen.

## Updates, Daten und Deinstallation

Das Installationsskript erneut ausführen und HA neu starten. Vorhandener Integrationscode wird unter `ha_pinger_backups` gesichert. `configuration.yaml` und andere Integrationen werden nicht verändert.

Beim Update auf **1.4.1** anschließend auch den Browser bzw. die Companion-App vollständig neu laden. Falls eine JavaScript-Ressource manuell angelegt wurde, deren Versionsangabe auf `?v=1.4.1` ändern. Den gesamten Integrationsordner einschließlich `frontend/ha-pinger.css` aktualisieren. Bei Nutzung von WireGuard auch die separate App auf 1.4.1 aktualisieren.

Adressen, Gruppen, Reihenfolge, Favoriten, Prüfregeln, aktives Netz, Einstellungen, Meldestatus und Verlauf liegen in **`/config/.storage/ha_pinger`**. Der App-Zugriffsschlüssel liegt separat in **`.storage/ha_pinger_secrets`**, die Bilder im Ordner **`.storage/ha_pinger_images`**. Diese Daten bleiben bei Updates und beim Entfernen/erneuten Hinzufügen der Integration erhalten. Sie gehören in dein HA-Backup. Nicht bei laufender Integration bearbeiten. Beim Löschen aller Adressen bleibt die Liste auch nach einem Neustart leer. WireGuard-Dateien einschließlich privater Schlüssel liegen im eigenen persistenten Datenspeicher der optionalen App; diese App bei HA-Backups mit auswählen. Die Hell-/Dunkel-Auswahl liegt nur im jeweiligen Browser; ohne eigene Auswahl folgt das Control Center dem HA-Theme.

### Vollständig deinstallieren

1. Die Integration unter **Geräte & Dienste** entfernen und Dashboard-Karten sowie eine eventuell manuell angelegte JavaScript-Ressource löschen.
2. Falls eingerichtet, die separate **Network Control Center WireGuard**-App stoppen und deinstallieren; deren gespeicherte App-Daten ebenfalls entfernen.
3. Home Assistant stoppen. Den Codeordner `custom_components/ha_pinger` und gezielt `.storage/ha_pinger`, `.storage/ha_pinger_secrets` sowie `.storage/ha_pinger_images` löschen. Andere `.storage`-Dateien unverändert lassen.
4. Falls vorhanden, `/addons/ncc_vpn`, die entpackte Paketquelle, `ha_pinger_backups` und `ha_pinger_vpn_backups` entfernen. HA wieder starten.

Alte HA-Backups können weiterhin gespeicherte Profile enthalten. Die Integration ändert keine Routerkonfiguration und installiert keine Routen auf dem HA-Host.

## Entwicklung und Prüfung

Zielplattform: Home Assistant **2026.9**, optionale App für **aarch64** (Raspberry Pi 5 mit 64-Bit-HA-OS) und amd64. Verwendete HA-Schnittstellen wurden mit dem Quellcode von **2026.9.3** abgeglichen. Eine echte HA-Installation, der Docker-Build auf dem Pi und reale Handy-Zustellung sind hier nicht geprüft.

```sh
python -m pip install aiohttp icmplib==3.0.4
python -m unittest discover -s tests -v
node --check custom_components/ha_pinger/frontend/ha-pinger.js
python tools/build.py
```

`aiohttp` ist in HA bereits enthalten; `icmplib` wird über das Integrationsmanifest eingebunden. Die Python-Tests prüfen unter anderem einen echten lokalen Web-Ausfall bis zum gemeinsamen HA-Dienstaufruf für Test und Alarm, Sekunden-Timer, Wiederholungen, Netzwechsel, parallele Einzelprüfungen, Historie, Bilder, IP-Bereiche, Gruppen und Installation. Die HA-Dienstgrenze wird im Test simuliert; es wird kein echtes Handy angeschrieben. `node tools/ui_smoke.mjs` prüft mit Playwright und lokalem Chrome die Oberfläche von 360 bis 1480 Pixeln, einschließlich mobiler Balken, Filterzeile, Netzdialog und Hell-/Dunkel-Schalter. `go test ./...` im App-Ordner testet Ping und HTTP durch zwei echte lokale WireGuard-Gegenstellen, API-Anmeldung, gespeicherte Profile und das Aktivieren, Wechseln und Schließen des Tunnels. Der Dienst wurde für Linux/arm64 kompiliert. Der lokale UI-Demomodus unter `preview/` gehört nicht zum Installationspaket; Beispieldaten erscheinen dort nur mit `?fixtures`.

### Neue Version veröffentlichen

Versionen in `manifest.json`, `const.py`, den Frontend-Asset-URLs und den App-Versionsfeldern gemeinsam erhöhen. `CHANGELOG.md` und `RELEASE_NOTES.md` aktualisieren, Änderungen committen und pushen. Danach einen passenden Tag anlegen und pushen, beispielsweise `v1.4.1`. Der Workflow **Test and release** prüft Python, Oberfläche, Installationsskripte und WireGuard, baut den Container und veröffentlicht bei Erfolg den GitHub-Release samt ZIP. Ein Tag ohne erfolgreichen Release wird von HACS nicht als neue Release-Version angeboten. Der Workflow hat Schreibrechte nur im Veröffentlichungsjob.

Für die optionale WireGuard-App liest der HA-App-Store die Version aus `addons/ncc_vpn/config.yaml` im Standardbranch. App-Änderungen deshalb zusammen mit der getesteten Release-Version veröffentlichen. Bei einem einmaligen Update über den Store kann dort die automatische Aktualisierung für die App eingeschaltet werden.

### Technische Referenzen

- [Home Assistant: Ping (ICMP)](https://www.home-assistant.io/integrations/ping/)
- [aiohttp: HTTP-Client, Antwortstatus und TLS](https://docs.aiohttp.org/en/stable/client_reference.html)
- [Custom Panels](https://developers.home-assistant.io/docs/frontend/custom-ui/creating-custom-panels/)
- [WebSocket-Erweiterungen](https://developers.home-assistant.io/docs/frontend/extending/websocket-api/)
- [Asynchrone statische Dateien](https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/)
- [Companion-App: Benachrichtigungen](https://companion.home-assistant.io/docs/notifications/notifications-basic/)
