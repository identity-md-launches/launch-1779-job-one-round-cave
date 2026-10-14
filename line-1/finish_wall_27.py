"""One-time preservation and delivery pass for the installed tool's shell pigment."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

BASE = Path('artifacts/line-1/wall.png')
TARGET = Path('artifacts/line-1/wall-v7.png')
ANCESTOR = '21ef144fa1339bdc2a5de097e4aaae4232ac1bed0eb088cbcb229eb58d73d03b'


def main():
    original = BASE.read_bytes()
    assert hashlib.sha256(original).hexdigest() == ANCESTOR
    w, h, old = read_png(original)
    draft = TARGET.read_bytes()
    gw, gh, generated = read_png(draft)
    assert (w, h) == (1254, 1254) and (gw, gh) == (1024, 1024)
    final = bytearray(old)
    # Only the generated shell pigment, moved into previously bare stone.
    # No generated background, earlier mark, or reinterpreted frog is retained.
    x0, y0, width, height = 710, 248, 85, 92
    sx0, sy0, sw, sh = 667, 275, 101, 111
    for dy in range(height):
        for dx in range(width):
            x, y = x0 + dx, y0 + dy
            i = (y*w+x)*3
            rock = old[i:i+3]
            if max(rock) < 85:
                continue
            gx, gy = sx0+dx*sw//width, sy0+dy*sh//height
            j = (gy*gw+gx)*3
            r, g, b = generated[j:j+3]
            red = r > 105 and g < r*.61 and b < r*.49
            chalk = 699 <= gx <= 729 and 307 <= gy <= 342 and min(r,g,b) > 130 and max(r,g,b)-min(r,g,b) < 60
            if not (red or chalk):
                continue
            pigment = (146, 59, 28) if red else (202, 183, 142)
            # Flatten generated highlights into rubbed earth pigment, retaining rock texture.
            alpha = .56 if red else .61
            light = min(1.15, max(.60, sum(rock)/(3*140)))
            for c in range(3):
                final[i+c] = round(rock[c]*(1-alpha)+pigment[c]*light*alpha)
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
    assert changed > 1000
    encoded = png(w,h,final)
    BASE.write_bytes(encoded)
    TARGET.write_bytes(encoded)
    preview = jpeg(512,512,resize(w,h,final),52)
    assert len(preview) < 100000
    Path('dist/line-1/27.jpg').write_bytes(preview)
    review = {
        'ancestor_sha256': ANCESTOR,
        'wall_sha256': hashlib.sha256(encoded).hexdigest(),
        'format': 'PNG', 'width': w, 'height': h, 'mode': 'RGB',
        'output_paths': [str(BASE),str(TARGET)],
        'changed_pixels': changed, 'unchanged_pixels': w*h-changed,
        'changed_bounds_inclusive': bounds,
        'outside_addition_identical': True, 'deep_cracks_preserved': True,
        'preview': {'path':'dist/line-1/27.jpg','format':'JPEG','width':512,'height':512,'bytes':len(preview)},
        'generation': {'tool':'mcp__image__generate','model':'black-forest-labs/flux-kontext-pro',
                       'draft_sha256':hashlib.sha256(draft).hexdigest(),
                       'draft_dimensions':[gw,gh], 'draft_retained':False,
                       'prompt_file':'line-1/WALL-27.md',
                       'postprocess':'Only generated shell pigment retained on bare stone; highlights flattened to ochre/chalk; original pixels elsewhere restored exactly.'},
        'visual_review': {'status':'awaiting final inspection', 'unmet_visual_requirements':[]}}
    Path('line-1/wall-review-27.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__ == '__main__':
    main()
