# WireGuard-Netze einrichten

**Deutsch** · [English](DOCS.en.md)

## 1. App auf dem Raspberry Pi installieren

### Über GitHub als App-Repository

Unter **Einstellungen → Apps → Store → ⋮ → Repositories** `https://github.com/VikShepo/ha-pinger` hinzufügen. Danach **Network Control Center WireGuard** installieren. Dadurch kann HA spätere App-Versionen aus dem Repository anbieten. Die Option zur automatischen App-Aktualisierung lässt sich auf der App-Seite einschalten.

Bei einer Repository-Installation hat die App einen Hostnamen nach dem Muster `<Repository-Kennung>-ncc-vpn`, statt `local-ncc-vpn`. Im Terminal zeigt `ha addons list` die App-Kennung; `ha addons info <App-Kennung>` zeigt deren Hostnamen. Diesen unter **Netze → App verbinden** als `http://<Hostname>:8099` eintragen. [HA: Interne App-Namen](https://developers.home-assistant.io/docs/apps/communication/).

Eine vorhandene **lokale App** und eine **Repository-App** haben getrennte Datenspeicher. Beim Wechsel die ursprünglichen WireGuard-Dateien und den Zugriffsschlüssel in der neuen App erneut einrichten; gespeicherte Profile werden nicht automatisch übertragen. Die lokale App erst entfernen, wenn der neue Dienst funktioniert.

### Alternativ lokal aus dem ZIP

Diese Schritte gelten für **Home Assistant OS** mit **Einstellungen → Apps** beziehungsweise **Add-ons**. Der Raspberry Pi 5 allein sagt noch nicht, welche HA-Installationsart verwendet wird.

1. Das gesamte Paket nach `/config/HA-Pinger` entpacken. Wenn dein Konfigurationsordner `/homeassistant` heißt, diesen Pfad verwenden.
2. Im Terminal-&-SSH-Add-on mit Zugriff auf `/addons` ausführen:

   ```sh
   sh /config/HA-Pinger/install-vpn.sh /addons
   ```

   Alternativ den Paketordner `addons/ncc_vpn` über Samba in die Freigabe **addons** kopieren, sodass `addons/ncc_vpn/config.yaml` entsteht. Der File Editor für `/homeassistant` zeigt diesen separaten Apps-Ordner normalerweise nicht an. [HA: Lokale Apps installieren](https://developers.home-assistant.io/docs/apps/tutorial/).
3. **Einstellungen → Apps → Store → ⋮ → Nach Updates suchen**. Falls nötig die Seite neu laden.
4. Unter **Lokale Apps** die **Network Control Center WireGuard**-App öffnen und **Installieren** wählen. Der erste Build lädt Go-Abhängigkeiten und kann auf dem Pi mehrere Minuten dauern. Internetzugang ist dafür erforderlich.

Für Deutsch/Englisch auch die Integration `ha_pinger` auf **1.5.0** aktualisieren. Der Netzwechsel erfordert mindestens Version 1.4.0 beider Teile. Diese zusätzliche App wird im **App-Store** installiert; die Integration bleibt unter **Geräte & Dienste**.

## 2. Integration und App verbinden

1. **Network Control Center → Netze → App verbinden** öffnen.
2. **Schlüssel erzeugen → Kopieren**. Die App-Adresse auf `http://local-ncc-vpn:8099` lassen. **Speichern**.
3. In der WireGuard-App unter **Konfiguration** denselben Schlüssel in **api_token** eintragen und speichern.
4. Die App starten und **Beim Booten starten** aktivieren.
5. Im Control Center unter **Netze → Verbindung testen** prüfen.

Der Schlüssel wird zwischen Integration und App verwendet. Die Integration gibt ihn bei späteren Statusabfragen nicht zurück. Der Standardname `local-ncc-vpn` gilt bei Installation als lokale HA-App; Port 8099 muss dafür nicht ins Heimnetz freigegeben werden. [HA: Interne Kommunikation](https://developers.home-assistant.io/docs/apps/communication/).

## 3. WireGuard-Datei hochladen und Netz auswählen

1. Am Router oder VPN-Server eine **eigene WireGuard-Clientkonfiguration** für diese App erzeugen. Ein gleichzeitig auf einem Handy verwendetes Profil kann sich gegenseitig die Verbindung wegnehmen.
2. **Netze → Netz hinzufügen**: Name eingeben, `.conf` auswählen und speichern.
3. Unter **Netze** beim gespeicherten Netz **Aktivieren** drücken. Erst dann öffnet die App den Tunnel. In der Hauptansicht die zu prüfenden Adressen hinzufügen. Bei vorhandenen Einträgen im Bearbeitungsdialog das passende **Netz** wählen.
4. **Jetzt prüfen** testet sofort durch den aktiven Tunnel. Zum Zurückschalten **Netze → Heimnetz → Aktivieren** wählen: Der Tunnel wird geschlossen, und HA prüft wieder die Heimnetz-Adressen.

**Nur das aktive Netz wird überwacht.** Andere Profile bleiben gespeichert, ihre Tunnel sind geschlossen und ihre Prüfungen sowie Ausfallmeldungen pausieren. Verlauf und Protokoll bleiben erhalten. Ein Wechsel bricht laufende Prüfungen ab und startet frische Messungen für das neue Netz. Die Netzauswahl gilt für die ganze Integration und damit für alle verbundenen Browser und Handys. Sie bleibt bei Neustarts erhalten. Beim Update von 1.3.0 startet das Control Center im Heimnetz; gespeicherte Profile lassen sich danach aktivieren.

Gleiche private IP-Adressen in verschiedenen Profilen bleiben getrennt. Bis zu 16 Profile und insgesamt 256 Adressen werden unterstützt. Mit **Netz bearbeiten** eine neue Datei hochladen oder nur den Namen ändern. Vor dem Löschen ins Heimnetz wechseln und die zugeordneten Adressen entfernen oder einem anderen Netz zuordnen.

**Weboberfläche öffnen:** Der Button öffnet die Zieladresse im Browser deines Handys oder PCs. Dieser Browser benötigt selbst Zugang zum Zielnetz. Der Tunnel der App stellt die Hintergrundprüfungen bereit und baut keine VPN-Verbindung auf deinem Handy auf.

## Verbindungen und unterstützte Dateien

Die App nutzt WireGuard mit einem eigenen Netzwerkstack für das aktive Profil. Sie fordert weder `NET_ADMIN` noch `/dev/net/tun` an und läuft mit `host_network: false`. Auch `AllowedIPs = 0.0.0.0/0, ::/0` gilt ausschließlich im jeweiligen Profil. Die Integration schaltet die Netzverbindung des HA-Hosts nicht um. Der Docker-Build und Betrieb auf deinem konkreten Pi müssen vor Ort geprüft werden.

Dateien bis 32 KB: eine `[Interface]`-Sektion mit `PrivateKey`, `Address`, optional `DNS`, `MTU`, `ListenPort`; bis zu acht `[Peer]`-Sektionen mit `PublicKey`, optional `PresharedKey`, `AllowedIPs`, `Endpoint` und optional `PersistentKeepalive`. ListenPort wird durch einen eigenen dynamischen UDP-Port ersetzt. Skript-Hooks, `Table`, `FwMark` und andere Systembefehle werden abgelehnt. Für DDNS-Ziele einen erreichbaren DNS-Server im Profil eintragen und dessen IP in `AllowedIPs` einschließen. DNS-Suchdomänen im `DNS`-Feld werden nicht unterstützt.

Endpoint-Domainnamen werden beim Aktivieren und anschließend etwa alle zwei Minuten neu aufgelöst. Ein beim Start zunächst nicht verfügbares aktives Profil wird automatisch erneut versucht. Inaktive Profile werden dabei nicht geöffnet. Zielprüfungen im aktiven Netz laufen auch bei Ausfall weiter. Wenn die App nicht erreichbar ist, erscheint ein technischer Prüffehler; die Integration prüft dann nicht versehentlich die gleiche IP im Heimnetz.

## Daten, Update und Entfernung

Die App speichert Profile einschließlich privater Schlüssel in `/data/profiles.json` und die aktive Profil-ID in `/data/active-profile.json`, jeweils mit Dateirechten 0600. Über die API werden nur Profilname, ID und Aktivierungsstatus zurückgegeben. Beide Dateien bleiben bei App-Neustarts erhalten. Bei HA-Backups die App einschließen; Backups enthalten dann auch die VPN-Schlüssel. Das persistente `/data` wird durch HA bereitgestellt. [HA: App-Konfiguration](https://developers.home-assistant.io/docs/apps/configuration/).

Zum Update das neue Paket entpacken, `install-vpn.sh` erneut ausführen, den Store aktualisieren und die App auf **1.5.0** aktualisieren und starten. Auch den Integrationsordner `custom_components/ha_pinger` ersetzen und Home Assistant neu starten. Das Skript sichert bisherigen App-Quellcode außerhalb des Apps-Ordners. Bei Änderungen ohne Versionswechsel die lokale App über das App-Menü neu aufbauen.

Zur Entfernung zuerst **Heimnetz aktivieren**, Geräte anderen Netzen zuordnen oder löschen, dann die Profile im Control Center entfernen. Die WireGuard-App stoppen und deinstallieren, deren gespeicherte App-Daten und `/addons/ncc_vpn` bei gewünschter vollständiger Entfernung löschen. Die Integration kann mit Heimnetz-Adressen weiterlaufen. Eine vollständige Deinstallation des Control Centers ist in der Hauptanleitung beschrieben.

## HA Container ohne Apps-Store

Der Dienst lässt sich aus diesem Ordner als separates Docker-Image bauen:

```sh
docker build -t ncc-vpn:1.5.0 .
```

Einen Container mit persistentem Volume für `/data` und der Umgebungsvariable `NCC_TOKEN` (derselbe Zugriffsschlüssel, mindestens 32 Zeichen) starten. HA muss Port 8099 dieses Containers erreichen können. Im Control Center dessen erreichbare interne Adresse eintragen. Kein Host-Netzwerk, kein privilegierter Modus und keine Host-Routen sind erforderlich. Die passende interne Docker-Netzverbindung hängt von der bestehenden HA-Containerinstallation ab.
