# PRD: Olivar Golf Course Planner

## 1. Summary

A small, single-page web app to plan a round at Olivar (Madrid) the day before playing. It shows every hole as a 2D map taken from the course guide PDF, lets me measure distances interactively, overlays my club distances, and gives a hole-by-hole strategy designed to beat my best score of 98 (default target: 95, adjustable).

This is a learning and fun project. Keep it simple, local, and working by tonight.

## 2. Inputs (provided in the project folder)

- `course_guide.pdf`: hole-by-hole notes and a map of each hole (bunkers, water, trees, green shape).
- `scorecard.pdf` (or image): par, stroke index (handicap) and distance per hole. **I play from the yellow tees. Distances are in meters.**

If any value cannot be read reliably from the PDFs, put it in `course.json` with a `"needs_review": true` flag and show a warning in the UI rather than guessing silently.

## 3. My bag (default values, editable in the app)

Distances are **carry + roll averages in yards**. The course is in **meters**, so the app must convert (1 yd = 0.9144 m) and let me toggle the display unit (meters by default).

| Club | Yards | Meters (approx) | Notes |
|---|---|---|---|
| Driver | 220 | 201 | Main tee club |
| 4 Hybrid | 200 to 210 | 183 to 192 | Low confidence. Avoid unless clearly best option |
| 6 Iron (tee) | 180 | 165 | Off a tee only |
| 6 Iron (fairway) | 170 | 155 | |
| 7 Iron | 160 | 146 | |
| 8 Iron | 150 | 137 | |
| 9 Iron | 140 | 128 | |
| Pitching Wedge | 130 | 119 | |
| Sand Wedge | 100 | 91 | Full swing |

Known gaps the strategy should respect: nothing between PW (130 y) and SW (100 y), and nothing below 100 y except partial wedge shots. Prefer leaving full-swing distances over awkward in-between yardages.

Each club also gets a simple **dispersion** value (left/right spread and distance variance), default: Driver ±25 m wide, irons ±15 m, wedges ±8 m. Editable.

## 4. Core features

### 4.1 Hole viewer
- Hole selector (1 to 18) with previous/next buttons and swipe on mobile.
- Shows the hole map image extracted from the PDF, plus par, stroke index, yellow-tee distance and the PDF notes for that hole.

### 4.2 Map calibration
Map images have no reliable scale, so for each hole:
- I click the tee and the center of the green once.
- The app uses the scorecard distance to compute a meters-per-pixel scale for that hole.
- Calibration is saved (JSON export + browser storage) so I only do it once.
- Optional: Claude Code can pre-fill approximate tee/green pixel positions for me to confirm.

### 4.3 Interactive distance tool
- Tap any point on the map to see: distance from tee, distance remaining to the green center, and front/back of green if marked.
- Plan a route by tapping 2 to 4 points (tee shot, layup, approach). Each segment shows its length and the suggested club for it.
- Draw each planned shot's landing zone as an ellipse using the club's dispersion, so I can see if it reaches a bunker or hazard.
- Distance rings from the tee for each club (toggle on/off).

### 4.4 Hazard annotation (simple)
- Let me tag hazards on the map by tapping: bunker, water, OB, trees. Stored per hole.
- Claude Code should pre-populate hazards it can identify from the PDF map and notes, marked as "suggested" until I confirm.
- No computer vision needed. Manual tagging is fine.

### 4.5 Strategy engine (the "caddie")
For each hole, produce a recommended plan:
- Club off the tee and target line, with the reason (e.g. "7 iron to 146 m keeps the fairway bunker at 180 m out of play").
- Layup club and the yardage it leaves for the approach, preferring a full-swing number.
- Target score for that hole and the "safe miss" side.

Scoring target logic:
- Target total is a slider (default 95, range 85 to 105).
- Strokes above par are allocated using the stroke index: hardest holes get a double-bogey budget, easier holes get bogey or par budget, until the total matches the target.
- Strategy should be conservative: avoid hazards first, distance second. The hybrid is only recommended if no other option works.
- Show a round summary: target per hole, total, and the 3 or 4 holes where I should be most careful.

**How recommendations are generated:** Claude Code writes the initial strategy for all 18 holes into `strategy.json`, using the PDF notes, hazards, and my bag. The app also runs a rule-based recalculation when I edit club distances, target score, or my planned route. (Optional stretch: a "Ask Claude" button calling the Claude API with the hole data for a fresh take.)

### 4.6 Game-day mode
- Mobile-friendly single-column view: hole map, planned shots, target score, 2 or 3 bullet notes.
- Printable one-page summary of all 18 holes (club off tee, target score, key hazard).

## 5. Tech constraints

- One self-contained `index.html` (HTML, CSS, JS inline), no backend, no build step. Libraries from a CDN if needed.
- Map images extracted from the PDF with a small Python script (e.g. PyMuPDF), saved as `holes/hole_01.png` etc., or embedded as base64.
- Data files: `course.json` (par, SI, distances, notes, calibration, hazards), `bag.json`, `strategy.json`.
- Works on a phone browser (I'll use it at the course).

## 6. Out of scope

- GPS or live location tracking.
- Automatic hazard detection from images.
- Live score tracking or handicap calculation (nice to have later).

## 7. Acceptance criteria

1. All 18 holes load with map, par, SI, yellow distance and notes.
2. After calibrating a hole, tapping a point shows distances within about 5 percent of the scorecard.
3. Club rings and dispersion ellipses display in the correct scale and unit.
4. Every hole has a written plan with tee club, target line, layup/approach, target score and reasoning.
5. Changing the target score slider re-allocates per-hole targets and the total matches.
6. Editing a club distance updates recommendations.
7. Game-day view is usable on a phone and the summary prints on one page.

## 8. Suggested build order

1. Extract hole images and scorecard data from the PDFs into `course.json`. Show me anything flagged for review.
2. Hole viewer + calibration.
3. Distance tool + club rings.
4. Strategy generation and target-score allocation.
5. Hazard tagging, game-day view and print summary.
