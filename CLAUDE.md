# golf — Olivar golf planner

A single-page app to plan a round at Golf Olivar de la Hinojosa (Madrid) the day before playing.
The full spec is `PRD_olivar_golf_planner.md`. Repo: `sebagarciar/olivar-golf-planner` (public).

## Layout

- `index.html` — the whole app (HTML, CSS, JS inline). Loads `data.js` and `holes/*.webp`.
- `course.json`, `bag.json`, `strategy.json` — the data. After editing any of them run
  `python3 scripts/build_data.py`, which bundles them into `data.js` (a browser can't read JSON
  from disk when the page is opened by double-click, but it can load a script).
- `scripts/extract_maps.py` — crops the hole maps out of the guide into `holes/` (PNG for
  analysis, WebP for the app) and auto-detects tee and green positions.
- `scripts/seed_course.py` — writes calibration anchors and suggested hazards into `course.json`.
  Guide marker positions and bunkers are hand-placed lists in this script.
- `source/` — the original PDFs, local only (gitignored): `scorecard.pdf` (page 2 is the 18-hole
  card, page 1 is the 9-hole pitch & putt) and `course_guide.pdf` (one page per hole).
- Preview: `golf-planner` in the root `.claude/launch.json` serves this folder on port 8765.

## Facts to respect

- Yellow tees. Course data is in meters because the scorecard is (source of truth, Seba
  confirmed 2026-09-24), but Seba thinks in yards: the app shows yards by default, the bag is in
  yards (distances and spread, `width_yd`/`depth_yd`; the PRD's meter spreads were converted
  2026-09-24), and nothing on screen may hard-code meters (use `fmt()`). Notes in `strategy.json` carry
  no distances for the same reason. The guide's printed distances are older and differ on 11 holes; kept only as
  `guide_distance_m`.
- The maps are drawings, not to scale. Distances are interpolated along the route between
  anchors: tee (0), the guide's distance arcs (e.g. "220" from the tee, "85" to the green) and
  the green (scorecard distance). Tee-to-green along the fairway must equal the card on every hole.
- Holes 9 and 18 share a green.
- The guide's advice is written for good players and Seba doesn't want it: it's not shown in the
  app and isn't stored. Strategy notes in `strategy.json` are for a ~95 player and never name a
  club; the app picks clubs from the bag so the plan stays right when the bag changes.
- The hybrid is a last resort (PRD): the caddie adds a heavy cost to it.
- Local and manual: no backend, no automation, no Claude API button (Seba said no, keep it simple).
