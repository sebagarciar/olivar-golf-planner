# Olivar Golf Planner

A one-page app I open the night before a round at Golf Olivar de la Hinojosa (Madrid) to plan
every hole from the yellow tees, with my own clubs, aiming to beat my best score of 98.

The course guide gives me a drawing of each hole and advice written for players far better than
me. This puts my bag on those drawings instead: tap anywhere for distances, see how far each club
goes, see where a shot can end up, and get a plan per hole that fits the score I'm going for.

## What it does

- **Hole maps** from the club's course guide, with par, stroke index and yellow distance from the
  scorecard.
- **Distances that respect the drawing.** The maps aren't to scale, so distances come from the
  scorecard plus the distance arcs printed on each map. Tap a point: distance from the tee and to
  the green, straight line and along the fairway, plus front and back of the green.
- **A caddie per hole.** It picks the clubs by trying every sequence in my bag and keeping the
  one that's cheapest in strokes, counting water, OB and bunkers inside each shot's landing zone.
  It explains each choice ("Driver would bring the water into play", "leaves 119 m, a full
  pitching wedge"). The hybrid only comes out when nothing else works.
- **Target score.** A slider from 85 to 105 spreads the extra strokes over the hardest holes first,
  and each hole's plan is judged against its own target.
- **My route.** Tap up to four landing spots and the app suggests a club per shot and shows the
  landing zones.
- **Hazards.** Water and OB lines traced from the maps, greenside bunkers placed by hand, all
  "suggested" until I confirm them. I can tag more.
- **Game day** view for the phone, and a one-page printable summary of all 18 holes.

## Using it

Live at https://sebagarciar.github.io/olivar-golf-planner/ (on the phone, add it to the home
screen). Or open `index.html` in a browser. Everything I change (calibration, hazards, routes, bag) is saved
in that browser, and can be exported to JSON from the Bag tab.

The data lives in three files: `course.json` (holes, calibration, hazards), `bag.json` (my
clubs) and `strategy.json` (where to aim, safe miss and notes per hole). After editing any of
them:

```bash
python3 scripts/build_data.py
```

Rebuilding the maps from the course guide PDF needs the original PDFs in `source/` (not in the
repo) and a few Python packages:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/extract_maps.py
.venv/bin/python scripts/seed_course.py
```

Full spec in [`PRD_olivar_golf_planner.md`](PRD_olivar_golf_planner.md).

## Status

Built on 2026-09-24, not yet tested on the course. Tee and green positions were detected
automatically and still need confirming hole by hole; hazards are all still "suggested". Club
distances are my averages, not measured.
