"""Translate known stored messages without changing device names or addresses."""
import json
from pathlib import Path
import re

_MESSAGES = json.loads((Path(__file__).parent / "frontend/messages.en.json").read_text(encoding="utf-8"))
_PATTERNS = []
for _source, _target in sorted(_MESSAGES.items(), key=lambda item: -len(re.sub(r"\{\w+\}", "", item[0]))):
    if "{" in _source:
        _names = re.findall(r"\{(\w+)\}", _source)
        _pattern = re.compile("^" + "(.*?)".join(re.escape(part) for part in re.split(r"\{\w+\}", _source)) + "$", re.DOTALL)
        _PATTERNS.append((_pattern, _names, _target))


def language(value):
    return "de" if str(value or "en").lower().replace("_", "-").split("-")[0] == "de" else "en"


def translate_message(text, locale, depth=0):
    if not text or language(locale) == "de" or depth > 6:
        return text
    if text in _MESSAGES:
        return _MESSAGES[text]
    if re.match(r"^(Ping|Web|TCP): ", text) and re.search(r" · (Ping|Web|TCP): ", text):
        return " · ".join(translate_message(part, locale, depth+1) for part in re.split(r" · (?=(?:Ping|Web|TCP): )", text))
    for pattern, names, target in _PATTERNS:
        match = pattern.fullmatch(text)
        if match:
            values = {name: translate_message(value, locale, depth+1) if name in ("detail", "error", "title") else value
                      for name, value in zip(names, match.groups())}
            return re.sub(r"\{(\w+)\}", lambda found: values[found[1]], target)
    return text
