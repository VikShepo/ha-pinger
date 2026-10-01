#!/bin/sh
# Install source for the optional local HA app. Does not start a VPN or change routes.
set -eu
SOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
ADDONS_INPUT=${1:-/addons}
if [ ! -d "$ADDONS_INPUT" ]; then
  printf 'Fehler: %s fehlt. Ein Terminal mit Zugriff auf den lokalen Apps-Ordner /addons verwenden.\n' "$ADDONS_INPUT" >&2
  exit 1
fi
ADDONS_DIR=$(CDPATH= cd -- "$ADDONS_INPUT" && pwd -P)
[ "$ADDONS_DIR" != / ] || { printf 'Fehler: / ist kein zulässiger Apps-Ordner.\n' >&2; exit 1; }
TARGET="$ADDONS_DIR/ncc_vpn"
BACKUPS="$SOURCE_DIR/ha_pinger_vpn_backups"
if [ -L "$TARGET" ] || [ -L "$BACKUPS" ]; then
  printf 'Fehler: Verlinkte Zielordner werden nicht überschrieben.\n' >&2
  exit 1
fi
case "$SOURCE_DIR/" in "$TARGET/"*) printf 'Fehler: Quelle liegt im Zielordner.\n' >&2; exit 1 ;; esac
case "$BACKUPS/" in "$ADDONS_DIR/"*) printf 'Fehler: Paket bitte außerhalb des Apps-Ordners entpacken.\n' >&2; exit 1 ;; esac
if [ ! -f "$SOURCE_DIR/addons/ncc_vpn/config.yaml" ]; then
  printf 'Fehler: Bitte das komplette Installationspaket entpacken.\n' >&2
  exit 1
fi
STAGING=$(mktemp -d "$ADDONS_DIR/.ncc_vpn_install_XXXXXX")
BACKUP=''
cleanup() {
  case "$STAGING" in "$ADDONS_DIR"/.ncc_vpn_install_*) rm -rf -- "$STAGING" ;; esac
}
trap cleanup EXIT
cp -R "$SOURCE_DIR/addons/ncc_vpn" "$STAGING/ncc_vpn"
if [ -e "$TARGET" ]; then
  [ -d "$TARGET" ] || { printf 'Fehler: Ziel ist kein Ordner.\n' >&2; exit 1; }
  mkdir -p "$BACKUPS"
  BACKUP=$(mktemp -d "$BACKUPS/$(date -u +%Y%m%d_%H%M%S)_XXXXXX")
  mv "$TARGET" "$BACKUP/ncc_vpn"
fi
if ! mv "$STAGING/ncc_vpn" "$TARGET"; then
  if [ -n "$BACKUP" ]; then mv "$BACKUP/ncc_vpn" "$TARGET"; fi
  exit 1
fi
printf '\nWireGuard-App-Quelle installiert: %s\n' "$TARGET"
if [ -n "$BACKUP" ]; then printf 'Bisheriger Code gesichert: %s\n' "$BACKUP"; fi
printf '\n1. Einstellungen > Apps (Add-ons) > Store > Menü > Nach Updates suchen.\n2. Unter Lokale Apps: Network Control Center WireGuard installieren.\n3. Zugriffsschlüssel gemäß addons/ncc_vpn/DOCS.md setzen, dann App starten.\n'
