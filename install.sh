#!/bin/sh
# HA Terminal add-ons may not include Python. This installer needs only POSIX tools.
set -eu

SOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
CONFIG_INPUT=${1:-/config}
if [ ! -f "$CONFIG_INPUT/configuration.yaml" ]; then
  printf 'Fehler: configuration.yaml fehlt in %s\n' "$CONFIG_INPUT" >&2
  exit 1
fi
CONFIG_DIR=$(CDPATH= cd -- "$CONFIG_INPUT" && pwd -P)
PARENT="$CONFIG_DIR/custom_components"
TARGET="$PARENT/ha_pinger"
if [ -L "$PARENT" ] || [ -L "$TARGET" ] || [ -L "$CONFIG_DIR/ha_pinger_backups" ]; then
  printf 'Fehler: Verlinkte Zielordner werden nicht überschrieben.\n' >&2
  exit 1
fi
if [ ! -f "$SOURCE_DIR/custom_components/ha_pinger/manifest.json" ]; then
  printf 'Fehler: Bitte das komplette Installationspaket entpacken.\n' >&2
  exit 1
fi
mkdir -p "$PARENT"
STAGING=$(mktemp -d "$PARENT/.ha_pinger_install_XXXXXX")
BACKUP=''
# Trap removes only our newly-created temporary directory, after path validation.
cleanup() {
  case "$STAGING" in "$PARENT"/.ha_pinger_install_*) rm -rf -- "$STAGING" ;; esac
}
trap cleanup EXIT
cp -R "$SOURCE_DIR/custom_components/ha_pinger" "$STAGING/ha_pinger"
if [ -e "$TARGET" ]; then
  [ -d "$TARGET" ] || { printf 'Fehler: Ziel ist kein Ordner.\n' >&2; exit 1; }
  mkdir -p "$CONFIG_DIR/ha_pinger_backups"
  BACKUP=$(mktemp -d "$CONFIG_DIR/ha_pinger_backups/$(date -u +%Y%m%d_%H%M%S)_XXXXXX")
  mv "$TARGET" "$BACKUP/ha_pinger"
fi
if ! mv "$STAGING/ha_pinger" "$TARGET"; then
  if [ -n "$BACKUP" ]; then mv "$BACKUP/ha_pinger" "$TARGET"; fi
  exit 1
fi
printf '\nInstalliert: %s\n' "$TARGET"
if [ -n "$BACKUP" ]; then printf 'Bisherige Version gesichert: %s\n' "$BACKUP"; fi
printf '\n1. Home Assistant neu starten.\n2. Einstellungen > Geräte & Dienste > Integration hinzufügen > Network Control Center.\n3. Network Control Center in der Seitenleiste öffnen und eigene Adressen hinzufügen.\n4. Dashboard-Karte hinzufügen: custom:ha-pinger-card\n'
