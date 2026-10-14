"""Retain generated pigment only, preserving the inherited wall's exact pixels."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

BASE = Path('artifacts/line-2/wall.png')
TARGET = Path('artifacts/line-2/wall-v7.png')
ANCESTOR = 'de414a2cbfa1d35cff8fa7cf8bc219dd6f36b63ee4c08713aea05c4b767206e4'


def main():
    original, draft = BASE.read_bytes(), TARGET.read_bytes()
    assert hashlib.sha256(original).hexdigest() == ANCESTOR
    w, h, old = read_png(original)
    gw, gh, generated = read_png(draft)
    assert (w, h) == (gw, gh) == (1254, 1254)
    final = bytearray(old)
    x0, y0, width, height = 924, 544, 126, 140
    red = set()
    for y in range(y0, y0 + height):
        for x in range(x0, x0 + width):
            i = (y*w+x)*3
            r, g, b = generated[i:i+3]
            if y <= 651 and abs(x-932-(y-550)*.85) < 14 and r > 80 and g < .57*r and b < .32*r:
                red.add((x,y))
    colors = {'ochre': (146,58,24), 'charcoal': (43,29,18), 'chalk': (212,190,150)}
    counts = dict.fromkeys(colors, 0)
    for y in range(y0, y0 + height):
        for x in range(x0, x0 + width):
            i = (y*w+x)*3
            r,g,b = generated[i:i+3]
            rock = old[i:i+3]
            # Preserve deep cracks and leave deterministic worn gaps in pigment.
            if max(rock) < 85 or (x*19+y*31) % 13 == 0:
                continue
            kind = None
            if (x,y) in red:
                kind = 'ochre'
            elif max(r,g,b) < 83 and any((x+dx,y+dy) in red
                   for dx in range(-5,6) for dy in range(-5,6)):
                kind = 'charcoal'
            radius = (x-1031)**2+(y-667)**2
            if radius < 16**2:
                if max(r,g,b) < 95:
                    kind = 'charcoal'
                elif radius < 11**2 and r > 140 and g > 105 and b > 70:
                    kind = 'chalk'
            if kind is None:
                continue
            alpha = .68 if kind != 'chalk' else .62
            light = min(1.15, max(.65, sum(rock)/(3*140)))
            for c in range(3):
                final[i+c] = round(rock[c]*(1-alpha) + colors[kind][c]*light*alpha)
            counts[kind] += 1
    changed = 0
    bounds = [w,h,0,0]
    for y in range(h):
        for x in range(w):
            i = (y*w+x)*3
            if final[i:i+3] != old[i:i+3]:
                assert x0 <= x < x0+width and y0 <= y < y0+height
                assert max(old[i:i+3]) >= 85
                changed += 1
                bounds = [min(bounds[0],x),min(bounds[1],y),max(bounds[2],x),max(bounds[3],y)]
    assert changed > 500 and all(counts.values())
    encoded = png(w,h,final)
    BASE.write_bytes(encoded)
    TARGET.write_bytes(encoded)
    preview = jpeg(512,512,resize(w,h,final),52)
    assert len(preview) < 100000
    Path('dist/line-2/27.jpg').write_bytes(preview)
    review = {
        'name': 'The Exact Pebble', 'number': 27,
        'ancestor_sha256': ANCESTOR, 'sha256': hashlib.sha256(encoded).hexdigest(),
        'full_wall': {'format': 'PNG', 'mode': 'RGB', 'width': w, 'height': h},
        'wall_paths': [str(BASE), str(TARGET)],
        'addition_region': {'x': x0, 'y': y0, 'width': width, 'height': height},
        'changed_pixels': changed, 'unchanged_pixels': w*h-changed,
        'changed_bounds_inclusive': bounds, 'pigment_pixels': counts,
        'outside_region_pixel_identical': True, 'deep_cracks_preserved': True,
        'preview': {'path':'dist/line-2/27.jpg','format':'JPEG','width':512,'height':512,'bytes':len(preview)},
        'generation': {'tool':'image_gen.imagegen', 'draft_sha256':hashlib.sha256(draft).hexdigest(),
                       'draft_dimensions':[gw,gh], 'draft_retained_in_workspace':False,
                       'prompt_file':'line-2/WALL-27.md'},
        'method': 'Retained generated ochre/charcoal stick and chalk pebble pigment on bare stone. Original texture remains under pigment. Every pixel outside the bounded addition is original.',
        'visual_review': 'Awaiting final full-wall and JPEG inspection',
        'unmet_visual_requirements': []}
    Path('line-2/wall-review-27.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__ == '__main__':
    main()
