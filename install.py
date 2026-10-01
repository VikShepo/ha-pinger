#!/usr/bin/env python3
"""Install/update the integration in a Home Assistant configuration directory.

Uses only Python's standard library. Existing integration code is backed up;
configuration.yaml and .storage are never rewritten.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile


def install(config, source=None, dry_run=False):
    config = Path(config).expanduser().resolve(strict=True)
    source = (Path(source) if source else Path(__file__).parent / "custom_components" / "ha_pinger").resolve(strict=True)
    if not (config / "configuration.yaml").is_file():
        raise ValueError(f"Kein Home-Assistant-Konfigurationsordner: {config} (configuration.yaml fehlt)")
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("domain") != "ha_pinger":
        raise ValueError("Das Installationspaket ist unvollständig oder ungültig.")
    parent = config / "custom_components"
    target = parent / "ha_pinger"
    if parent.is_symlink() or target.is_symlink():
        raise ValueError("Verlinkte Zielordner werden nicht automatisch überschrieben.")
    if source == target.resolve():
        raise ValueError("Das Paket bitte außerhalb von custom_components/ha_pinger entpacken.")
    if dry_run:
        return target, None
    parent.mkdir(exist_ok=True)
    backup = None
    staging = Path(tempfile.mkdtemp(prefix=".ha_pinger_install_", dir=parent))
    # All replacement paths are fixed descendants of the verified config folder.
    try:
        shutil.copytree(source, staging / "ha_pinger", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if target.exists():
            if not target.is_dir():
                raise ValueError("Das Installationsziel ist kein Ordner.")
            backup_parent = config / "ha_pinger_backups"
            if backup_parent.is_symlink():
                raise ValueError("Der Sicherungsordner darf keine Verknüpfung sein.")
            backup_parent.mkdir(exist_ok=True)
            backup = backup_parent / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            target.rename(backup)
        try:
            (staging / "ha_pinger").rename(target)
        except OSError:
            if backup is not None:
                backup.rename(target)
            raise
    finally:
        # This directory was created above by mkdtemp; no user-controlled deletion.
        if staging.parent.resolve() == parent.resolve() and staging.name.startswith(".ha_pinger_install_"):
            shutil.rmtree(staging)
    return target, backup


def main():
    parser = argparse.ArgumentParser(description="Network Control Center für Home Assistant installieren")
    parser.add_argument("--config", default="/config", help="HA-Konfigurationsordner (Standard: /config)")
    parser.add_argument("--dry-run", action="store_true", help="Ziel prüfen, ohne Dateien zu ändern")
    args = parser.parse_args()
    try:
        target, backup = install(args.config, dry_run=args.dry_run)
    except (OSError, ValueError) as err:
        parser.exit(1, f"Installation fehlgeschlagen: {err}\n")
    print(f"{'Geprüftes Ziel' if args.dry_run else 'Installiert'}: {target}")
    if backup:
        print(f"Sicherung der bisherigen Version: {backup}")
    if not args.dry_run:
        print("\n1. Home Assistant neu starten.")
        print("2. Einstellungen > Geräte & Dienste > Integration hinzufügen:")
        print("   Network Control Center auswählen (nur bei der ersten Installation).")
        print("3. Network Control Center in der Seitenleiste öffnen und eigene Adressen hinzufügen.")
        print("4. Dashboard-Karte hinzufügen: custom:ha-pinger-card")


if __name__ == "__main__":
    main()
