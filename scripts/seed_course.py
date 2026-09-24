"""Seed course.json with calibration anchors and suggested hazards for every hole.

Run from the golf/ folder after extract_maps.py:  .venv/bin/python scripts/seed_course.py

- Tee and green come from holes/suggested_points.json (auto-detected).
- Guide markers ("220" arcs on the maps) were placed by eye where the arc crosses the middle of
  the fairway. They act as extra calibration anchors, because the maps are drawings, not to scale.
- Water and OB lines are traced from the map colours. Bunkers were placed by eye (the maps draw
  them in the same white as the fairway, so they can't be detected by colour).
Everything seeded here is "suggested" until confirmed in the app.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent

# Pixel position of each guide marker on holes/hole_XX.png, in the order of the markers in course.json.
MARKER_PX = {
    1: [(275, 555)],
    2: [(335, 1218), (514, 468)],
    3: [(400, 512)],
    4: [(305, 718)],
    6: [(390, 668)],
    7: [(640, 1080), (735, 535)],
    9: [(360, 795)],
    10: [(310, 820)],
    12: [(307, 1349), (307, 557)],
    14: [(275, 800)],
    15: [(410, 488)],
    16: [(400, 893)],
    17: [(455, 995), (470, 380)],
    18: [(270, 607)],
}

# Greenside bunkers (x, y, radius px), placed by eye.
BUNKERS = {
    1: [(710, 250, 30), (735, 400, 25)],
    2: [(525, 170, 25), (550, 80, 25), (650, 215, 20)],
    3: [(355, 240, 30), (510, 290, 25), (490, 430, 30), (325, 420, 25), (330, 470, 25)],
    4: [(440, 245, 25), (585, 305, 25), (555, 190, 30)],
    5: [(250, 490, 35), (490, 310, 35)],
    6: [(375, 120, 30), (465, 300, 25)],
    7: [(715, 200, 35), (855, 225, 35)],
    8: [(400, 245, 35), (275, 330, 25)],
    9: [(385, 200, 30), (425, 295, 25), (320, 355, 25)],
    10: [(430, 260, 25)],
    11: [(210, 360, 30), (400, 340, 35)],
    12: [(613, 307, 30), (654, 230, 25)],
    13: [(510, 450, 35)],
    14: [(535, 255, 25), (670, 250, 30)],
    15: [(180, 155, 30), (355, 190, 30)],
    16: [(190, 215, 25), (365, 205, 25), (300, 170, 25)],
    17: [(375, 190, 30), (525, 160, 25), (490, 95, 25)],
    18: [(275, 160, 30)],
}

FLAG_MAX_DIST_PX = 200  # the red shape nearest the green is the flag, if it's this close


def trace_water(rgb):
    """Blue areas -> list of simplified polygons (outline points, clockwise-ish)."""
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mask = (B > 150) & (R < 60) & (G > 80) & (G < 160)
    labels, n = ndimage.label(mask)
    polys = []
    for i in range(1, n + 1):
        blob = labels == i
        if blob.sum() < 3000:
            continue
        ys, xs = np.nonzero(blob)
        cy, cx = ys.mean(), xs.mean()
        # Outline by ray casting from the centroid: fine for these fairly round lakes.
        pts = []
        for a in np.linspace(0, 2 * np.pi, 48, endpoint=False):
            dx, dy = np.cos(a), np.sin(a)
            r, last = 0, None
            while True:
                x, y = int(cx + dx * r), int(cy + dy * r)
                if not (0 <= x < blob.shape[1] and 0 <= y < blob.shape[0]):
                    break
                if blob[y, x]:
                    last = (x, y)
                r += 2
                if r > 2000:
                    break
            if last:
                pts.append([last[0], last[1]])
        polys.append(pts)
    return polys


def trace_ob(rgb, green):
    """Red dashes -> one ordered polyline per OB line."""
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mask = (R > 170) & (R - G > 80) & (R - B > 70)  # hole 7 draws its dashes a lighter red
    labels, n = ndimage.label(mask)
    centers = [(x, y) for y, x in ndimage.center_of_mass(mask, labels, range(1, n + 1))]
    dist = [np.hypot(x - green[0], y - green[1]) for x, y in centers]
    if centers and min(dist) < FLAG_MAX_DIST_PX:
        centers.pop(int(np.argmin(dist)))
    if len(centers) < 4:
        return []
    # Chain dashes by nearest neighbour, starting from the dash furthest from the centroid.
    pts = np.array(centers)
    mid = pts.mean(axis=0)
    order = [int(np.argmax(np.hypot(*(pts - mid).T)))]
    left = set(range(len(pts))) - set(order)
    while left:
        last = pts[order[-1]]
        nxt = min(left, key=lambda i: np.hypot(*(pts[i] - last)))
        if np.hypot(*(pts[nxt] - last)) > 150:  # gap too big: a second OB line starts
            break
        order.append(nxt)
        left.remove(nxt)
    line = [[round(float(pts[i][0])), round(float(pts[i][1]))] for i in order]
    return [line]


def main():
    course = json.loads((ROOT / "course.json").read_text())
    for h in course["holes"]:
        n = h["hole"]
        h.pop("notes_es", None)  # the guide's advice is for low handicaps; strategy.json replaces it
        h["map"] = f"holes/hole_{n:02d}.webp"
        rgb = np.array(Image.open(ROOT / f"holes/hole_{n:02d}.png").convert("RGB")).astype(int)
        green = h["calibration"]["green_px"]
        for marker, px in zip(h["guide_markers"], MARKER_PX.get(n, [])):
            marker["px"] = list(px)
        hazards = []
        for poly in trace_water(rgb):
            hazards.append({"type": "water", "shape": "polygon", "points": poly, "status": "suggested"})
        for line in trace_ob(rgb, green):
            hazards.append({"type": "ob", "shape": "line", "points": line, "status": "suggested"})
        for x, y, r in BUNKERS.get(n, []):
            hazards.append({"type": "bunker", "shape": "circle", "points": [[x, y]], "r": r, "status": "suggested"})
        h["hazards"] = hazards
        # Scorecard confirmed as the source of truth for distances (2026-09-24).
        h["needs_review"] = False
        h["review_notes"] = []
    (ROOT / "course.json").write_text(json.dumps(course, indent=2, ensure_ascii=False))
    for h in course["holes"]:
        kinds = [z["type"] for z in h["hazards"]]
        print(h["hole"], {k: kinds.count(k) for k in set(kinds)})


if __name__ == "__main__":
    main()
