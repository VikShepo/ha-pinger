"""Build the distributable ZIP without caches, demo data or test dependencies."""

from pathlib import Path
import json
from shutil import copyfile
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
version = json.loads((root / "custom_components/ha_pinger/manifest.json").read_text(encoding="utf-8"))["version"]
output = root / "dist" / f"HA-Pinger-Control-Center-{version}.zip"
output.parent.mkdir(exist_ok=True)
files = [root / name for name in ("install.py", "install.sh", "install-vpn.sh", "README.md", "README.en.md", "CHANGELOG.md", "hacs.json", "repository.yaml")]
files.extend((root / "examples").rglob("*.yaml"))
files.extend((root / "blueprints").rglob("*.yaml"))
files.extend(p for p in (root / "custom_components").rglob("*")
             if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
files.extend(p for p in (root / "addons" / "ncc_vpn").iterdir()
             if p.is_file() and (p.name == "Dockerfile" or p.suffix in (".go", ".mod", ".sum", ".yaml", ".md", ".png"))
             and not p.name.endswith("_test.go"))
files.extend((root / "addons/ncc_vpn/translations").glob("*.yaml"))
with ZipFile(output, "w", ZIP_DEFLATED) as archive:
    for path in sorted(files):
        archive.write(path, str(Path("HA-Pinger") / path.relative_to(root)))
copyfile(output, root / "dist" / "HA-Pinger-Control-Center.zip")
print(output)
