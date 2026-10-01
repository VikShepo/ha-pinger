"""Local 300 x 300 PNG images, served only over authenticated HA WebSockets."""

import base64
import binascii
import hashlib
from pathlib import Path
import re
import struct
import zlib

MAX_IMAGE_BYTES = 400_000


def validate_image(value):
    if not isinstance(value, str) or not value.startswith("data:image/png;base64,") or len(value) > 540_000:
        raise ValueError("Bitte ein PNG-Bild mit 300 × 300 Pixeln auswählen.")
    try:
        raw = base64.b64decode(value.partition(",")[2], validate=True)
        if len(raw) > MAX_IMAGE_BYTES or raw[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError
        offset, first, ended = 8, True, False
        while offset < len(raw):
            length = struct.unpack_from(">I", raw, offset)[0]
            kind = raw[offset + 4:offset + 8]
            payload = raw[offset + 8:offset + 8 + length]
            crc = struct.unpack_from(">I", raw, offset + 8 + length)[0]
            if zlib.crc32(kind + payload) & 0xffffffff != crc:
                raise ValueError
            if first:
                if kind != b"IHDR" or length != 13 or struct.unpack_from(">II", payload) != (300, 300):
                    raise ValueError
                first = False
            if kind == b"acTL":  # Animated uploads would add distraction and CPU load.
                raise ValueError
            offset += length + 12
            if kind == b"IEND":
                ended = True
                break
        if not ended or offset != len(raw):
            raise ValueError
        return raw
    except (ValueError, struct.error, binascii.Error) as err:
        raise ValueError("Ungültiges Bild. Erwartet wird ein PNG mit 300 × 300 Pixeln (max. 400 KB).") from err


class ImageStore:
    def __init__(self, directory):
        self.directory = Path(directory)

    def path(self, image_id):
        if not isinstance(image_id, str) or not re.fullmatch(r"[0-9a-f]{64}", image_id):
            raise ValueError("Bild nicht gefunden.")
        return self.directory / f"{image_id}.png"

    def put(self, value):
        raw = validate_image(value)
        image_id = hashlib.sha256(raw).hexdigest()
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        path = self.path(image_id)
        if not path.exists():
            path.write_bytes(raw)
        return image_id

    def read(self, image_id):
        try:
            raw = self.path(image_id).read_bytes()
        except FileNotFoundError as err:
            raise ValueError("Bild nicht gefunden. Bitte erneut hochladen.") from err
        return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")

    def remove(self, image_id):
        self.path(image_id).unlink(missing_ok=True)
