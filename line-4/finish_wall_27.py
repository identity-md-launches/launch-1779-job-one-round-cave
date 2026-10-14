#!/usr/bin/env python3
"""Retain only the new image-tool pigment, preserving all ancestor marks."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, jpeg, resize

ANCESTOR = '756062212cb1638b80dbe05b5ca9d609e7056e957bf55e4412865fe6390cba13'


def main():
    folder = Path('artifacts/line-4')
    before = (folder / 'wall.png').read_bytes()
    assert hashlib.sha256(before).hexdigest() == ANCESTOR
    draft = (folder / 'wall-v7.png').read_bytes()
    w, h, old = read_png(before)
    gw, gh, generated = read_png(draft)
    assert (w, h) == (gw, gh) == (1254, 1254)
    final = bytearray(old)
    changed = 0
    bounds = [w, h, 0, 0]
    for y in range(410, 622):
        for x in range(74, 178):
            pebble = any((x-104)**2 + (y-cy)**2 < radius**2
                         for cy, radius in ((441, 27), (518, 28), (593, 28)))
            cord = 97 <= x <= 113 and 459 <= y <= 576
            fork = 120 <= x <= 177 and 498 <= y <= 548
            if not (pebble or cord or fork):
                continue
            i = (y*w+x)*3
            r, g, b = generated[i:i+3]
            if sum(old[i:i+3]) < 140:
                continue  # retain deep inherited fissures
            charcoal = r < 95 and g < 78 and b < 59
            red = r > 75 and g < r*.65 and b < g*.8
            yellow = pebble and r > 110 and g > 55 and g < r*.82 and b < g*.75
            if not (charcoal or red or yellow):
                continue
            final[i:i+3] = bytes(round(a*.2+v*.8) for a, v in zip(old[i:i+3], (r, g, b)))
            if final[i:i+3] != old[i:i+3]:
                changed += 1
                bounds = [min(bounds[0], x), min(bounds[1], y), max(bounds[2], x), max(bounds[3], y)]
    assert changed > 1500
    for y in range(h):
        for x in range(w):
            i = (y*w+x)*3
            if final[i:i+3] != old[i:i+3]:
                assert 74 <= x < 178 and 410 <= y < 622
    output = png(w, h, final)
    for name in ('wall.png', 'wall-v7.png'):
        (folder / name).write_bytes(output)
    preview = jpeg(512, 512, resize(w, h, final), 52)
    assert len(preview) < 100000
    Path('dist/line-4/27.jpg').write_bytes(preview)
    sha = hashlib.sha256(output).hexdigest()
    review = {
        'wall': {'paths': ['artifacts/line-4/wall.png', 'artifacts/line-4/wall-v7.png'],
                 'width': w, 'height': h, 'format': 'PNG', 'mode': 'RGB', 'sha256': sha},
        'preview': {'path': 'dist/line-4/27.jpg', 'width': 512, 'height': 512,
                    'format': 'JPEG', 'bytes': len(preview)},
        'ancestorSha256': ANCESTOR,
        'generatedImageSha256': hashlib.sha256(draft).hexdigest(),
        'changedPixels': changed, 'unchangedPixels': w*h-changed,
        'additionBounds': bounds,
        'preservation': 'Only image-tool pigment on vacant far-left stone. Every pixel outside the addition is identical, including all ancestor drawings, Pepe, hands, rock and framing. Deep fissures within the addition are retained.',
        'imageTool': 'built-in image_gen.imagegen; one edit',
        'prompt': 'Preserve the inherited cave wall and all marks. Add a very small worn vertical trail of three uneven red/yellow ochre pebbles linked by thin charcoal cord, with a tiny fork at the middle pebble, on vacant far-left rock. Earth pigments only; no new hands, letters, numbers, captions, logos, signatures, watermarks, border or frame.',
        'visualReview': 'Pending finished PNG and JPEG inspection',
        'unmetVisualRequirements': [],
        'limitations': ['Local checks are not independent visual certification.',
                        'The small worn addition is less distinct in the 512-pixel preview.']}
    Path('line-4/wall-review-27.json').write_text(json.dumps(review, indent=2)+'\n')
    record = {'name': 'The Ordered Trail', 'image': 'https://api.imd.fun/artifacts/'+sha,
              'attributes': [
                  {'trait_type': 'Cave', 'value': 'Water'},
                  {'trait_type': 'Wall', 'value': 'Line 4'},
                  {'trait_type': 'Number', 'value': 27},
                  {'trait_type': 'Left behind', 'value': 'offline ordered EIP-712 request set checker'},
                  {'trait_type': 'Meaning', 'value': 'Pepe checks every pebble and the order of their trail.'},
                  {'trait_type': 'One thing', 'value': 'offline EIP-712 typed-data digest checking'}]}
    Path('dist/line-4/27.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
