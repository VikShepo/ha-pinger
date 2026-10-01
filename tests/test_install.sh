#!/bin/sh
# Exercise the actual POSIX installer with a temporary HA config, including spaces.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
TEMP_ROOT=$(CDPATH= cd -- "${TMPDIR:-/tmp}" && pwd -P)
TEST_DIR=$(mktemp -d "$TEMP_ROOT/ha_pinger_test_XXXXXX")
cleanup() {
  case "$TEST_DIR" in "$TEMP_ROOT"/ha_pinger_test_*) rm -rf -- "$TEST_DIR" ;; esac
}
trap cleanup EXIT
CONFIG="$TEST_DIR/HA Config"
mkdir -p "$CONFIG/.storage"
printf 'default_config:\n' > "$CONFIG/configuration.yaml"
printf 'preserved' > "$CONFIG/.storage/ha_pinger"
sh "$ROOT/install.sh" "$CONFIG" > "$TEST_DIR/install.log"
test -f "$CONFIG/custom_components/ha_pinger/frontend/ha-pinger.js"
printf 'previous version' > "$CONFIG/custom_components/ha_pinger/local-note.txt"
sh "$ROOT/install.sh" "$CONFIG" > "$TEST_DIR/update.log"
test ! -f "$CONFIG/custom_components/ha_pinger/local-note.txt"
test -f "$CONFIG"/ha_pinger_backups/*/ha_pinger/local-note.txt
test "$(cat "$CONFIG/.storage/ha_pinger")" = preserved
test "$(cat "$CONFIG/configuration.yaml")" = 'default_config:'
mkdir "$TEST_DIR/invalid"
if sh "$ROOT/install.sh" "$TEST_DIR/invalid" > "$TEST_DIR/invalid.log" 2>&1; then
  printf 'Installer accepted an invalid config directory.\n' >&2
  exit 1
fi
printf 'Shell installer passed: fresh install, update, backup, preserved configuration and invalid path.\n'
PACKAGE="$TEST_DIR/Package"
ADDONS="$TEST_DIR/addons"
mkdir -p "$PACKAGE/addons" "$ADDONS"
cp "$ROOT/install-vpn.sh" "$PACKAGE/install-vpn.sh"
cp -R "$ROOT/addons/ncc_vpn" "$PACKAGE/addons/ncc_vpn"
sh "$PACKAGE/install-vpn.sh" "$ADDONS" > "$TEST_DIR/vpn-install.log"
test -f "$ADDONS/ncc_vpn/config.yaml"
test -f "$ADDONS/ncc_vpn/main.go"
printf 'old app' > "$ADDONS/ncc_vpn/local-note.txt"
sh "$PACKAGE/install-vpn.sh" "$ADDONS" > "$TEST_DIR/vpn-update.log"
test ! -f "$ADDONS/ncc_vpn/local-note.txt"
test -f "$PACKAGE"/ha_pinger_vpn_backups/*/ncc_vpn/local-note.txt
if sh "$PACKAGE/install-vpn.sh" "$TEST_DIR/missing" > "$TEST_DIR/vpn-invalid.log" 2>&1; then
  printf 'VPN installer accepted a missing apps directory.\n' >&2
  exit 1
fi
printf 'VPN installer passed: fresh source install, update, external backup and missing directory.\n'
