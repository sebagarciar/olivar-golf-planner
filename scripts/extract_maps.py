"""Crop each hole's 2D map out of the course guide PDF and suggest tee/green pixel positions.

Run from the golf/ folder:  .venv/bin/python scripts/extract_maps.py
Writes holes/hole_XX.png (for analysis), holes/hole_XX.webp (for the app) and holes/suggested_points.json.
"""
import json
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "source" / "course_guide.pdf"
OUT = ROOT / "holes"

# Per hole, measured on a 1334x750 view of the page:
#   map = (left, top, right, bottom) of the hole map, including hazards, OB lines and tees
#   photo_right = right edge of the aerial photo (the crop never starts left of it)
#   text = (right, bottom) of the notes paragraph, painted out so stray words don't leak in
#   extra_text = a second, shorter box where one line of the notes runs further right
VIEW_W, VIEW_H, PAD = 1334, 750, 10
HOLES = {
    1: dict(map=(915, 155, 1240, 660), photo_right=820, text=(930, 220)),
    2: dict(map=(955, 85, 1235, 710), photo_right=848, text=(1045, 240)),
    3: dict(map=(965, 115, 1225, 640), photo_right=856, text=(995, 275)),
    4: dict(map=(960, 125, 1260, 705), photo_right=888, text=(995, 300)),
    5: dict(map=(980, 220, 1250, 545), photo_right=910, text=(750, 215)),
    6: dict(map=(930, 105, 1185, 705), photo_right=868, text=(895, 260)),
    7: dict(map=(910, 95, 1255, 700), photo_right=841, text=(1030, 215)),
    8: dict(map=(1005, 205, 1215, 570), photo_right=910, text=(1010, 215)),
    9: dict(map=(1005, 115, 1225, 665), photo_right=921, text=(1000, 285), extra_text=(1020, 200)),
    10: dict(map=(970, 95, 1265, 710), photo_right=930, text=(980, 290)),
    11: dict(map=(905, 135, 1185, 515), photo_right=888, text=(875, 200)),
    12: dict(map=(940, 35, 1270, 725), photo_right=883, text=(885, 245)),
    13: dict(map=(965, 115, 1245, 550), photo_right=900, text=(1020, 205)),
    14: dict(map=(960, 95, 1260, 720), photo_right=901, text=(895, 245)),
    15: dict(map=(975, 200, 1195, 685), photo_right=891, text=(905, 250)),
    16: dict(map=(1015, 130, 1255, 720), photo_right=922, text=(930, 205)),
    17: dict(map=(970, 100, 1250, 715), photo_right=865, text=(970, 250)),
    18: dict(map=(980, 170, 1265, 660), photo_right=930, text=(945, 225)),
}


BACKGROUND = (35 / 255, 31 / 255, 32 / 255)  # the guide's dark page colour


def blob_center(rgb, mask):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return [round(float(xs.mean()), 1), round(float(ys.mean()), 1)]


def main():
    OUT.mkdir(exist_ok=True)
    doc = pymupdf.open(GUIDE)
    points = {}
    for hole, spec in HOLES.items():
        page = doc[hole]  # page 0 is the cover, page N is hole N
        sx, sy = page.rect.width / VIEW_W, page.rect.height / VIEW_H
        left, top, right, bottom = spec["map"]
        x0 = max(left - PAD, spec["photo_right"] + 2)
        clip = pymupdf.Rect(x0 * sx, (top - PAD) * sy, min(right + PAD, VIEW_W) * sx, min(bottom + PAD, VIEW_H) * sy)
        for text_right, text_bottom in [spec["text"], spec.get("extra_text", spec["text"])]:
            page.draw_rect(pymupdf.Rect(0, 0, text_right * sx, text_bottom * sy), color=None, fill=BACKGROUND)
        pix = page.get_pixmap(clip=clip, dpi=144)  # 2x the native 1920x1080 page
        pix.save(OUT / f"hole_{hole:02d}.png")  # full quality, used by seed_course.py
        # What the app loads: about 30 KB instead of 500 KB per hole, same pixel size.
        Image.frombytes("RGB", (pix.w, pix.h), pix.samples).save(OUT / f"hole_{hole:02d}.webp", quality=82, method=6)

        rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)[..., :3].astype(int)
        R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        yellow = (R > 200) & (G > 190) & (B < 90)          # the two yellow tee markers
        green = (G > 90) & (G - R > 50) & (G - B > 10)     # the putting green
        points[hole] = {
            "image_size": [pix.w, pix.h],
            "tee": blob_center(rgb, yellow),
            "green": blob_center(rgb, green),
        }
        print(hole, points[hole])

    (OUT / "suggested_points.json").write_text(json.dumps(points, indent=2))


if __name__ == "__main__":
    main()
