"""Trace the terrain out of each guide drawing into vector shapes, for the app's stylised map.

Run from the golf/ folder after extract_maps.py:  .venv/bin/python scripts/trace_terrain.py
Then python3 scripts/build_data.py to bundle terrain.json into data.js.

The guide colours its drawings: white = fairway (bunkers around the green merge into it), teal =
green, blue = water, grey = trees, tee boxes and fescue tufts (plus text and distance arcs, which
are dropped). Shapes keep the drawing's pixel coordinates, so calibration, hazards and routes line
up with them unchanged. Bunkers and OB lines are not traced: the app draws them from the hazards in
course.json, which are the ones the caddie uses.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage.measure import approximate_polygon, find_contours

ROOT = Path(__file__).resolve().parent.parent
MAPS = ROOT / "holes"


def outlines(mask, min_area, tolerance=1.6):
    """Outer outline of every blob bigger than min_area, as [[x, y], ...] polygons."""
    # closing fills text printed over the shape; the 7 px opening drops the thin distance arcs
    mask = ndi.binary_fill_holes(ndi.binary_opening(ndi.binary_closing(mask, structure=np.ones((13, 13))), structure=np.ones((7, 7))))
    lab, n = ndi.label(mask)
    shapes = []
    for i in range(1, n + 1):
        blob = lab == i
        if blob.sum() < min_area:
            continue
        soft = ndi.gaussian_filter(np.pad(blob, 2).astype(float), 2.0)
        contour = max(find_contours(soft, 0.5), key=len)
        poly = approximate_polygon(contour, tolerance)[:-1] - 2  # drop the pad
        shapes.append([[round(float(x), 1), round(float(y), 1)] for y, x in poly])
    return shapes


def grey_blobs(rgb, open_px=0):
    """Trees, tee boxes and fescue tufts are all grey; tell them apart by size, shape and texture.
    open_px > 0 first erases anything thinner than that, like the distance arcs and their labels."""
    mx, mn = rgb.max(-1), rgb.min(-1)
    grey = ndi.binary_closing((mx - mn < 28) & (mn > 95) & (mx < 225), iterations=2)
    if open_px:
        grey = ndi.binary_opening(grey, structure=np.ones((open_px, open_px)))
    lab, _ = ndi.label(grey)
    blobs = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        blob = lab[sl] == i
        area = int(blob.sum())
        if area < 300:
            continue
        h, w = blob.shape
        ys, xs = np.nonzero(blob)
        px = rgb[sl][blob]
        blobs.append(dict(
            area=area, w=w, h=h, aspect=w / h, fill=area / (w * h), texture=float(px[:, 0].std()), value=float(px.mean()),
            cx=float(xs.mean() + sl[1].start), cy=float(ys.mean() + sl[0].start),
            px=np.column_stack([xs + sl[1].start, ys + sl[0].start]), mask=blob, sl=sl,
        ))
    return blobs


def split_trees(blob, tree_area):
    """A blob of k touching trees: split its pixels into k clusters (plain k-means)."""
    k = max(1, round(blob["area"] / tree_area))
    pts = blob["px"].astype(float)
    centers = pts[np.linspace(0, len(pts) - 1, k).astype(int)]
    for _ in range(20):
        nearest = np.argmin(((pts[:, None] - centers[None]) ** 2).sum(-1), axis=1)
        centers = np.array([pts[nearest == j].mean(0) if np.any(nearest == j) else centers[j] for j in range(k)])
    return centers


def trace(n):
    rgb = np.asarray(Image.open(MAPS / f"hole_{n:02d}.png").convert("RGB")).astype(int)
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    white = rgb.min(-1) > 215
    green = (G > 90) & (G - R > 50) & (G - B > 10)
    water = (B > 120) & (B - R > 60) & (B - G > 20)

    # Trees (70-90 px canopies) and tee boxes survive an 11 px opening; arcs, digits and tufts don't.
    blobs = grey_blobs(rgb, open_px=11)
    tee_box = lambda b: b["area"] >= 2500 and (b["texture"] < 17 or (b["fill"] >= 0.6 and not 0.65 <= b["aspect"] <= 1.5 and b["texture"] < 19))
    # Trees: round, textured, lighter than the guide's digits. Their size sets the scale for splitting touching ones.
    tree_like = [b for b in blobs if not tee_box(b) and b["value"] >= 165 and b["fill"] >= 0.6 and 0.7 <= b["aspect"] <= 1.35 and b["area"] >= 2500]
    tree_area = float(np.median([b["area"] for b in tree_like])) if tree_like else 4300.0
    tree_r = round(float(np.sqrt(tree_area / np.pi)) * 1.05, 1)
    trees = []
    for b in blobs:
        merged = not tee_box(b) and b["value"] >= 165 and b["area"] >= 1.6 * tree_area and b["fill"] >= 0.3
        if b in tree_like or merged:
            trees += [[round(float(x), 1), round(float(y), 1)] for x, y in split_trees(b, tree_area)]
    tee_mask = np.zeros(white.shape, bool)
    for b in blobs:
        if tee_box(b):
            tee_mask[b["sl"]] |= b["mask"]
    # Fescue tufts: spiky grey icons about a third the size of a tree (found before the opening erases them).
    tufts = [[round(b["cx"], 1), round(b["cy"], 1)] for b in grey_blobs(rgb)
             if 1000 <= b["area"] <= 1800 and b["texture"] >= 24 and b["value"] >= 160 and 0.4 <= b["fill"] <= 0.56
             and 40 <= b["w"] <= 56 and 50 <= b["h"] <= 62]

    return {
        "fairway": outlines(white, 1500),
        "green": outlines(green, 800),
        "water": outlines(water, 1500, tolerance=2),
        "tees": outlines(tee_mask, 1500),
        "trees": trees,
        "tree_r": tree_r,
        "tufts": tufts,
    }


def main():
    course = json.loads((ROOT / "course.json").read_text())
    out = {}
    for h in course["holes"]:
        t = trace(h["hole"])
        out[str(h["hole"])] = t
        print(f"hole {h['hole']:2d}: fairway {len(t['fairway'])}, green {len(t['green'])}, water {len(t['water'])}, "
              f"tees {len(t['tees'])}, trees {len(t['trees'])}, tufts {len(t['tufts'])}")
    (ROOT / "terrain.json").write_text(json.dumps({"holes": out}, separators=(",", ":")))


if __name__ == "__main__":
    main()
