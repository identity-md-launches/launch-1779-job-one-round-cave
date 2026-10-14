#!/usr/bin/env python3
"""One-time additive pigment composition of the generated mark on gathering 06."""
import hashlib
import json
from pathlib import Path
import struct
import zlib

from image_bytes import jpeg, png, read_png, resize

ROOT = Path(__file__).resolve().parent.parent
ANCESTOR = '79c12fa2c03d587d5aa0367412946c5662d498e40ef1837973f8c33ee705d9dc'
PROMPT = 'Transparent prehistoric pigment insert: two shallow joined bowls and falling ochre grains, beside a recognizable heavy-lidded wide-mouthed Pepe head; dry broken red/yellow ochre and charcoal strokes; no hands, text, frames, logos or modern rendering. Built-in imagegen. Added only on vacant stone; inherited rock and all previous pigment retained.'


def read_rgba(data):
    """Decode the image tool's noninterlaced 8-bit RGBA draft in memory only."""
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not PNG')
    offset, compressed, header = 8, bytearray(), None
    while offset < len(data):
        size = int.from_bytes(data[offset:offset+4], 'big')
        kind, body = data[offset+4:offset+8], data[offset+8:offset+8+size]
        crc = int.from_bytes(data[offset+8+size:offset+12+size], 'big')
        if len(body) != size or zlib.crc32(kind+body) != crc:
            raise ValueError('draft CRC mismatch')
        if kind == b'IHDR': header = struct.unpack('>IIBBBBB', body)
        if kind == b'IDAT': compressed.extend(body)
        offset += size+12
        if kind == b'IEND': break
    w, h, bits, color, compression, filters, interlace = header
    if (bits, color, compression, filters, interlace) != (8, 6, 0, 0, 0):
        raise ValueError('expected RGBA draft')
    raw = zlib.decompress(compressed)
    stride = w*4
    if len(raw) != (stride+1)*h:
        raise ValueError('draft decoded length mismatch')
    pixels, previous = bytearray(), bytearray(stride)
    for y in range(h):
        f = raw[y*(stride+1)]
        row = bytearray(raw[y*(stride+1)+1:(y+1)*(stride+1)])
        for i in range(stride):
            a, b, c = row[i-4] if i >= 4 else 0, previous[i], previous[i-4] if i >= 4 else 0
            if f == 0: prediction = 0
            elif f == 1: prediction = a
            elif f == 2: prediction = b
            elif f == 3: prediction = (a+b)//2
            elif f == 4:
                p = a+b-c
                distances = [abs(p-a), abs(p-b), abs(p-c)]
                prediction = (a, b, c)[distances.index(min(distances))]
            else: raise ValueError('unsupported draft filter')
            row[i] = (row[i]+prediction)&255
        pixels.extend(row)
        previous = row
    return w, h, pixels


def main():
    ancestor = ROOT / 'artifacts/gathering/wall.png'
    target = ROOT / 'artifacts/gathering/wall-v7.png'
    original = ancestor.read_bytes()
    if hashlib.sha256(original).hexdigest() != ANCESTOR:
        raise ValueError('wall.png must be the verified gathering 06 ancestor')
    w, h, old = read_png(original)
    draft = target.read_bytes()
    gw, gh, generated = read_rgba(draft)
    if (w, h) != (1254, 1254): raise ValueError('unexpected ancestor dimensions')
    # Vacant stone above the woven mark and right of the bowl; no ancestor pigment lies here.
    x0, y0, width, height = 805, 690, 190, 110
    opaque = [(x, y) for y in range(gh) for x in range(gw)
              if generated[(y*gw+x)*4+3] > 128]
    sx0, sy0 = min(x for x, y in opaque), min(y for x, y in opaque)
    sx1, sy1 = max(x for x, y in opaque)+1, max(y for x, y in opaque)+1
    final, bounds, changed = bytearray(old), [w, h, 0, 0], 0
    for dy in range(height):
        for dx in range(width):
            x, y = x0+dx, y0+dy
            i = (y*w+x)*3
            rock = old[i:i+3]
            if max(rock) < 80: continue  # Deep cracks retain every original byte.
            xa, xb = sx0+dx*(sx1-sx0)//width, sx0+(dx+1)*(sx1-sx0)//width
            ya, yb = sy0+dy*(sy1-sy0)//height, sy0+(dy+1)*(sy1-sy0)//height
            pigment, coverage = [0, 0, 0], 0.0
            for gy in range(ya, yb):
                for gx in range(xa, xb):
                    r, g, b, a = generated[(gy*gw+gx)*4:(gy*gw+gx)*4+4]
                    charcoal = max(r, g, b) < 110
                    ochre = r > 85 and g < r*.86 and b < r*.65
                    if not a or not (charcoal or ochre): continue
                    color = (49, 37, 24) if charcoal else (
                        (157, 69, 30) if g < r*.64 else (165, 116, 47))
                    weight = a/255
                    coverage += weight
                    for channel in range(3): pigment[channel] += color[channel]*weight
            if not coverage: continue
            alpha = .82*coverage/((xb-xa)*(yb-ya))
            light = min(1.1, max(.55, sum(rock)/(3*135)))
            for channel in range(3):
                final[i+channel] = round(rock[channel]*(1-alpha)+pigment[channel]/coverage*light*alpha)
            if final[i:i+3] != rock:
                changed += 1
                bounds = [min(bounds[0], x), min(bounds[1], y), max(bounds[2], x), max(bounds[3], y)]
    if changed < 1000: raise ValueError('insufficient new pigment')
    for y in range(h):
        for x in range(w):
            i = (y*w+x)*3
            if not (x0 <= x < x0+width and y0 <= y < y0+height) or max(old[i:i+3]) < 80:
                assert final[i:i+3] == old[i:i+3]
    encoded = png(w, h, final)
    target.write_bytes(encoded)
    ancestor.write_bytes(encoded)
    thumbnail = resize(w, h, final)
    quality = 52
    preview = jpeg(512, 512, thumbnail, quality)
    while len(preview) > 100000 and quality > 10:
        quality -= 5
        preview = jpeg(512, 512, thumbnail, quality)
    if len(preview) > 100000: raise ValueError('preview exceeds byte limit')
    (ROOT / 'dist/gathering/07.jpg').write_bytes(preview)
    review = {
        'ancestorSha256': ANCESTOR, 'ancestorSize': [w, h], 'wallSize': [w, h],
        'wallFormat': 'PNG', 'wallMode': 'RGB', 'wallSha256': hashlib.sha256(encoded).hexdigest(),
        'generatedDraftSha256': hashlib.sha256(draft).hexdigest(), 'generatedDraftSize': [gw, gh],
        'generatedDraftRetained': False, 'changedPixels': changed, 'unchangedPixels': w*h-changed,
        'changedPixelBounds': bounds, 'additionRectangle': [x0, y0, width, height],
        'allPixelsOutsideAdditionUnchanged': True, 'deepCracksProtected': True,
        'previewSize': [512, 512], 'previewFormat': 'JPEG', 'previewBytes': len(preview),
        'previewQuality': quality, 'imageTool': 'image_gen__imagegen', 'prompt': PROMPT,
        'reviewStatus': 'requires final visual inspection', 'unmetVisualRequirements': []}
    (ROOT / 'gathering/wall-review-07.json').write_text(json.dumps(review, indent=2)+'\n')
    print(json.dumps({k: v for k, v in review.items() if k != 'prompt'}, indent=2))


if __name__ == '__main__': main()
