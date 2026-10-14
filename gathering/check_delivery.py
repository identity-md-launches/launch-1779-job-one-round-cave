#!/usr/bin/env python3
"""Offline structural checks for Water's current gathering; no dependencies."""
import hashlib
import json
import struct
import zlib
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BARE = "https://api.imd.fun/artifacts/ce5dbc18003365f5a1bf9014a2a357c2cb5c5dc2335dd0eb9b661ae703d36308"


class Gallery(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.records = []
        self.sections = []
        self.dependencies = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img":
            self.images.append(attrs["src"])
        if tag == "a" and attrs.get("class") == "record":
            self.records.append(attrs["href"])
        if tag == "section":
            self.sections.append(attrs["id"])
        if tag == "script" or (tag == "link" and attrs.get("rel") == "stylesheet"):
            self.dependencies.append(attrs)


def png_info(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    offset = 8
    header = None
    compressed = []
    ended = False
    while offset < len(data):
        size = int.from_bytes(data[offset:offset+4], "big")
        kind = data[offset+4:offset+8]
        body = data[offset+8:offset+8+size]
        crc = int.from_bytes(data[offset+8+size:offset+12+size], "big")
        assert len(body) == size and zlib.crc32(kind + body) == crc
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        if kind == b"IDAT":
            compressed.append(body)
        offset += 12 + size
        if kind == b"IEND":
            ended = True
            break
    assert ended and offset == len(data)
    width, height, bits, color, compression, filter_method, interlace = header
    assert bits == 8 and color == 2 and interlace == 0
    assert compression == filter_method == 0
    decoded = zlib.decompress(b"".join(compressed))
    assert len(decoded) == height * (1 + width * 3)
    assert all(decoded[y * (1 + width * 3)] in range(5) for y in range(height))
    return {"format": "PNG", "width": width, "height": height, "mode": "RGB"}


def jpeg_info(path):
    data = path.read_bytes()
    assert data[:2] == b"\xff\xd8" and data[-2:] == b"\xff\xd9"
    offset = 2
    while offset < len(data):
        assert data[offset] == 255
        while data[offset] == 255:
            offset += 1
        marker = data[offset]
        offset += 1
        size = int.from_bytes(data[offset:offset+2], "big")
        if marker in (0xc0, 0xc1, 0xc2):
            bits, height, width, components = struct.unpack(">BHHB", data[offset+2:offset+8])
            assert bits == 8 and components == 3
            return {"format": "JPEG", "width": width, "height": height}
        offset += size
    raise AssertionError("JPEG has no supported frame")


def main():
    number = 7
    wall = ROOT / "artifacts/gathering/wall-v7.png"
    preview = ROOT / f"dist/gathering/{number:02}.jpg"
    png, jpeg = png_info(wall), jpeg_info(preview)
    assert wall.read_bytes() == (ROOT / 'artifacts/gathering/wall.png').read_bytes()
    assert (png["width"], png["height"]) == (1254, 1254)
    assert (jpeg["width"], jpeg["height"]) == (512, 512)
    r = json.loads((ROOT / f"dist/gathering/{number:02}.json").read_text())
    assert set(r) == {"name", "image", "attributes"}
    assert r["image"] == "https://api.imd.fun/artifacts/" + hashlib.sha256(wall.read_bytes()).hexdigest()
    attrs = r["attributes"]
    assert [a["trait_type"] for a in attrs] == ["Cave", "Wall", "Number", "Left behind", "Meaning", "One thing"]
    assert all(set(a) == {"trait_type", "value"} for a in attrs)
    assert [attrs[i]["value"] for i in (0, 1, 2, 5)] == ["Water", "Gathering", number, "Gathering"]
    assert type(attrs[2]["value"]) is int
    assert all(a["value"] for a in attrs)
    pending = {"name": "Not painted yet", "image": BARE,
               "attributes": [{"trait_type": "Cave", "value": "Water"}]}
    folders = [f"line-{n}" for n in range(1, 5)] + ["gathering"]
    expected, expected_images = [], []
    painted_count = pending_count = 0
    for folder in folders:
        directory = ROOT / "dist" / folder
        records = [(p, json.loads(p.read_text())) for p in directory.glob('[0-9][0-9].json')]
        records.sort(key=lambda item: int(item[0].stem), reverse=True)
        painted = [(p, r) for p, r in records if r['name'] != 'Not painted yet']
        waiting = [(p, r) for p, r in records if r['name'] == 'Not painted yet']
        painted_count += len(painted)
        pending_count += len(waiting)
        assert all((directory / f'{n:02}.json').exists() for n in range(1, 22))
        for path, record in painted + waiting:
            expected.append(path.relative_to(ROOT / 'dist').as_posix())
            assert set(record) == {'name', 'image', 'attributes'}
            if record['name'] == 'Not painted yet':
                assert record == pending and not path.with_suffix('.jpg').exists()
                expected_images.append(record['image'])
            else:
                values = {a['trait_type']: a['value'] for a in record['attributes']}
                assert list(values) == ['Cave', 'Wall', 'Number', 'Left behind', 'Meaning', 'One thing']
                assert values['Cave'] == 'Water'
                assert values['Wall'] == ('Gathering' if folder == 'gathering' else 'Line ' + folder[-1])
                assert type(values['Number']) is int and values['Number'] == int(path.stem)
                info = jpeg_info(path.with_suffix('.jpg'))
                assert (info['width'], info['height']) == (512, 512)
                expected_images.append(path.with_suffix('.jpg').relative_to(ROOT / 'dist').as_posix())
    goals = json.loads((ROOT / "dist/goals.json").read_text())
    assert goals == [{"line": n, "goal": (ROOT / f"line-{n}/GOAL.md").read_text().strip()}
                     for n in range(1, 5)]
    gallery = Gallery()
    gallery.feed((ROOT / "dist/index.html").read_text())
    assert gallery.sections == folders and not gallery.dependencies
    assert gallery.records == expected
    assert gallery.images == expected_images
    for href in gallery.records:
        assert (ROOT / "dist" / href).is_file()
    oversized = [str(p.relative_to(ROOT)) for folder in ("gathering", "shared", "dist")
                 for p in (ROOT / folder).rglob("*") if p.is_file() and p.stat().st_size > 100_000]
    assert not oversized, oversized
    assert not list((ROOT / "dist").rglob("__pycache__"))
    baseline = json.loads((ROOT / 'gathering/line-source-hashes.json').read_text())
    actual = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for n in range(1, 5) for p in (ROOT / f'line-{n}').rglob('*') if p.is_file()}
    assert actual == baseline, 'line folders changed'
    for entry in json.loads((ROOT / 'shared/payment-evidence/provenance.json').read_text()):
        source = ROOT / entry['source']
        copied = ROOT / 'shared/payment-evidence' / entry['copy']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == entry['sha256']
        assert hashlib.sha256(copied.read_bytes()).hexdigest() == entry['copiedSha256']
        if entry['adaptation'] == 'none; byte-for-byte source copy':
            assert source.read_bytes() == copied.read_bytes()
    review = json.loads((ROOT / 'gathering/wall-review-07.json').read_text())
    assert review['wallSha256'] == hashlib.sha256(wall.read_bytes()).hexdigest()
    assert review['changedPixels'] + review['unchangedPixels'] == png['width'] * png['height']
    assert review['unmetVisualRequirements'] == []
    assert review['reviewStatus'] == 'visually inspected full PNG and decoded JPEG'
    print(json.dumps({"valid": True, "wall": png, "preview": jpeg,
                      "paintedRecords": painted_count, "placeholderRecords": pending_count,
                      "galleryRecords": len(gallery.records),
                      "unmetVisualRequirements": [],
                      "lineFoldersUnchanged": True,
                      "vendoredProvenanceVerified": True,
                      "visualReview": "Recorded separately in REPORT.md; this checker validates structure, not appearance."}, indent=2))


if __name__ == "__main__":
    main()
