"""Bundle the official @mdi/svg package as a local, searchable path catalog.

Usage: python tools/import_icons.py path/to/extracted/package
The package is only needed by maintainers; HA needs no extra dependency.
"""
import json
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

source = Path(sys.argv[1])
root = Path(__file__).resolve().parents[1]
frontend = root / "custom_components/ha_pinger/frontend"
translations = {
    "network": "netzwerk netz switch", "lan": "netzwerk kabel switch",
    "router": "router gateway", "wifi": "wlan drahtlos", "access-point": "wlan repeater",
    "server": "server rechner", "nas": "netzwerkspeicher", "database": "datenbank speicher",
    "home": "haus zuhause heim", "office": "büro buero gebäude gebaeude",
    "warehouse": "lager halle", "factory": "fabrik werkstatt", "garage": "garage",
    "cellphone": "handy telefon smartphone", "phone": "telefon handy",
    "desktop": "computer rechner pc", "laptop": "notebook rechner", "monitor": "bildschirm computer",
    "printer": "drucker", "camera": "kamera überwachung ueberwachung", "cctv": "kamera überwachung ueberwachung",
    "television": "fernseher tv", "speaker": "lautsprecher", "headphone": "kopfhörer kopfhoerer",
    "lightbulb": "lampe licht", "led": "licht lampe", "power": "strom steckdose",
    "plug": "stecker steckdose strom", "battery": "batterie akku", "solar": "solar sonne strom",
    "water": "wasser", "thermometer": "temperatur heizung", "radiator": "heizung",
    "thermostat": "heizung temperatur", "air": "luft klima", "fan": "lüfter luefter ventilator",
    "shield": "sicherheit schutz", "lock": "schloss sperre", "key": "schlüssel schluessel",
    "door": "tür tuer eingang", "window": "fenster", "gate": "tor", "alarm": "alarm wecker",
    "motion": "bewegung sensor", "smoke": "rauch melder", "fire": "feuer brand",
    "earth": "welt internet", "web": "internet browser", "cloud": "wolke internet",
    "vpn": "wireguard tunnel", "ip": "adresse netzwerk", "ethernet": "netzwerkkabel lan",
    "bed": "bett schlafzimmer", "sofa": "wohnzimmer couch", "fridge": "kühlschrank kuehlschrank küche kueche",
    "stove": "herd küche kueche", "washing": "waschmaschine waschen", "dishwasher": "spülmaschine spuelmaschine",
    "car": "auto fahrzeug", "bike": "fahrrad", "garden": "garten", "flower": "blume garten",
    "tree": "baum garten", "account": "benutzer person", "map": "karte standort",
    "folder": "ordner gruppe", "floor": "etage stockwerk", "stairs": "treppe",
    "check": "erfolgreich erreichbar", "alert": "warnung fehler", "clock": "uhr zeit",
}
catalog = []
authors = []
for item in json.loads((source / "meta.json").read_text(encoding="utf-8")):
    name = item["name"]
    if not re.fullmatch(r"[a-z0-9-]+", name):
        raise ValueError("Invalid icon name")
    svg = ET.parse(source / "svg" / (name + ".svg")).getroot()
    paths = [p.attrib["d"] for p in svg if p.tag.endswith("path")]
    if not paths or any(not re.fullmatch(r"[0-9a-zA-Z., +\-]+", p) for p in paths):
        raise ValueError("Unsupported SVG path")
    search = " ".join([name, *item.get("aliases", []), *item.get("tags", [])]).lower()
    german = " ".join(value for key, value in translations.items() if key in name)
    catalog.append([name, " ".join(paths), search + " " + german])
    authors.append(name + " — " + item.get("author", "Pictogrammers"))
catalog.sort()
(frontend / "icon-catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
names = "\n".join("mdi:" + row[0] for row in catalog)
(root / "custom_components/ha_pinger/icon_names.py").write_text(
    '# Generated from @mdi/svg; see frontend/ICON-LICENSE.txt.\nMDI_ICONS = frozenset("""\n' + names + '\n""".split())\n', encoding="utf-8")
shutil.copyfile(source / "LICENSE", frontend / "ICON-LICENSE.txt")
(frontend / "ICON-AUTHORS.txt").write_text("Material Design Icons 7.4.47 / Pictogrammers\n" + "\n".join(authors) + "\n", encoding="utf-8")
print(f"Bundled {len(catalog)} icons")
