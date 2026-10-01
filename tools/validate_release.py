"""Check the exact release package and synchronized version fields."""
import ast
import json
import os
from pathlib import Path
from zipfile import ZipFile

root = Path(__file__).resolve().parents[1]
component = root / "custom_components/ha_pinger"
manifest = json.loads((component / "manifest.json").read_text(encoding="utf-8"))
version = manifest["version"]
tag = os.environ.get("RELEASE_TAG", "")
if tag and tag != f"v{version}":
    raise SystemExit(f"Release tag {tag} differs from manifest version {version}")
assert f'VERSION = "{version}"' in (component / "const.py").read_text(encoding="utf-8")
assert f'?v={version}' in (component / "frontend/ha-pinger.js").read_text(encoding="utf-8")
assert f'version: "{version}"' in (root / "addons/ncc_vpn/config.yaml").read_text(encoding="utf-8")
for field in ("documentation", "issue_tracker", "codeowners"):
    assert manifest[field], f"Missing HACS manifest field: {field}"
assert json.loads((root / "hacs.json").read_text())["name"] == manifest["name"]
archive_path = root / "dist" / f"HA-Pinger-Control-Center-{version}.zip"
with ZipFile(archive_path) as archive:
    assert archive.testzip() is None
    names = archive.namelist()
    assert len(names) == len(set(names))
    for required in ("brand/icon.png", "brand/icon@2x.png", "frontend/ha-pinger.js", "frontend/ha-pinger.css", "frontend/icon-catalog.json", "frontend/i18n.js", "frontend/strings.en.json", "frontend/messages.en.json"):
        assert f"HA-Pinger/custom_components/ha_pinger/{required}" in names
    for required in ("README.en.md", "addons/ncc_vpn/DOCS.en.md", "addons/ncc_vpn/translations/en.yaml", "addons/ncc_vpn/translations/de.yaml"):
        assert f"HA-Pinger/{required}" in names
    for name in names:
        relative = Path(name).relative_to("HA-Pinger")
        assert not any(part in ("..", ".storage", ".test-output", "preview", "__pycache__") for part in relative.parts)
        assert archive.read(name) == (root / relative).read_bytes(), name
        if relative.suffix == ".py":
            ast.parse(archive.read(name), filename=name)
print(f"Validated release {version}: {len(names)} packaged files, including integration and app icons.")
