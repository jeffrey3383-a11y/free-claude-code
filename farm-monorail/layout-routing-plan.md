# Palm-Oil Estate Field Monorail — Track Layout & Routing Plan

A worked, first-pass routing plan for a **hilly palm-oil block cluster**. All site
data below is *assumed* (you asked me to create it) and clearly flagged — swap in
your real contours/blocks/yield and the same method and rules apply. The companion
schematic is `estate-layout.svg` (open in any browser); it is generated from
`generate_layout.py` so the drawing and these numbers stay in sync.

---

## 1. Example estate (assumptions)

| Item | Assumed value | Notes |
|---|---|---|
| Area served by monorail | **~63 ha** | The steep/undulating zone where tractors & buffalo are inefficient — monorail's real niche |
| Blocks | **6** (A–F), ~10.5 ha each | 3 columns × 2 up-slope tiers |
| Block footprint | **350 m (E–W) × 300 m (up-slope)** | Cluster ≈ 1050 m × 600 m |
| Terrain | **Hilly**, rising N from a valley road | Lower tier ~8–14°, upper tier ~16–28° |
| Elevation | ~40 m (road) → ~225 m (top) | ~185 m total rise |
| Planting | **9 m triangular**, 136 palms/ha | Inter-row ≈ **7.8 m**; track runs in inter-rows |
| Road | One **estate road along the south (valley) edge** | Lorry route; all FFB leaves here |
| FFB yield | **22 t/ha/yr** (mature) | → 1,386 t/yr over 63 ha |
| Peak crop | **~12% of annual in peak month** | Drives throughput sizing |
| System | **Rack-capable diesel monorail**, ~1.0 t payload/trip | Loco + FFB bins |

---

## 2. Design rules that govern routing

These are the constraints every segment of track is checked against. Final values
must match your chosen supplier's spec — treat these as typical design envelopes.

| Parameter | Design value used | Routing consequence |
|---|---|---|
| Max gradient — **adhesion** (friction) | ≤ **14°** (~25%) | Allowed only in the lower tier |
| Max gradient — **rack-and-pinion** | ≤ **31°** (~60%); monorack units steeper | Lets mains climb the upper tier on the fall line |
| Branch (contour) gradient | ≤ **±3°** (~5%) | Branches follow contours → effectively level, easy traction |
| Min horizontal curve radius | ~**3 m** (light) / larger for bin trains | If a junction turn is tighter than the loco allows → use a **turntable**, not a curve |
| Vertical transition (slope change) | smooth curve, **no kink** | Insert vertical curve at the 12°→22° tier break |
| Support-post spacing | ~**2.5 m** (closer on curves/steep) | Drives post count & cost |
| Rail height above ground | ~0.4–1.0 m | Harvesters load bins; clears undergrowth |
| Max manual carry to a bin | ≤ **~40 m** | Sets line spacing ≤ ~80 m (≈ every 10th inter-row) |

---

## 3. Network architecture — "comb + trunk"

The grade and the harvesting access are deliberately separated onto different members:

- **Mains (red)** run **straight up the fall line** through each column (lower block →
  upper block). They carry essentially all the climb. Lower 300 m sits in the
  **adhesion** zone; upper 300 m sits in the **rack-and-pinion** zone.
- **Branches (blue)** run **across the slope on the contour**, so they are near-level
  regardless of how steep the hill is — good traction, simple, cheap track. Harvesters
  in each ~80 m corridor carry FFB ≤ ~40 m to a bin on the nearest branch.
- **Trunk (green)** runs along the toe of the slope and **links CP1–CP2–CP3**, so a
  single loco can reach any branch and everything is delivered to **one central loading
  ramp** at CP2 (fewer lorry transfer points).
- **Turntables/switches (orange)** sit at every main×branch junction and at each CP, on
  **level benched pads** — you never turn a loaded train on grade.
- **Holding sidings** (dashed red) at each CP buffer full bins while the loco re-enters
  the field.

Why this shape on steep ground: putting the climb on the fall-line main minimises
cross-slope cut/fill, and keeping branches on the contour keeps their gradient trivial.

---

## 4. Routing, segment by segment

Per column (×3 identical columns), measured in **plan** metres and **slope (rail)** metres.

| Segment | Plan length | Slope | Rail length | Drive type |
|---|---|---|---|---|
| Main — lower tier | 300 m | ~12° | **306.7 m** | Adhesion |
| Main — upper tier | 300 m | ~22° | **323.5 m** | Rack-and-pinion |
| **Main subtotal** | 600 m | — | **~630 m** | mixed |
| Branches (7 levels × 300 m) | 2,100 m | ≤3° | **~2,100 m** | Adhesion (level) |
| **Column subtotal** | — | — | **~2,730 m** | |

Branch levels are at up-slope positions **60, 140, 220, 300, 380, 460, 540 m**
(spacing 80 m ⇒ max carry 40 m ✓). Each branch reaches **150 m either side** of its main,
covering the full 350 m block width with margin.

**Network totals**

| Element | Quantity | Length |
|---|---|---|
| Mains | 3 | ~1.89 km |
| Branches | 21 | ~6.30 km |
| Trunk (CP1↔CP3) | 1 | ~0.70 km |
| Holding sidings | 3 | ~0.12 km |
| **Total track** | | **~9.0 km** (~143 m/ha) |
| Support posts @2.5 m (+10% curves/steep) | | **~3,600–4,000** |
| Turntables / switches | 24 | 21 field junctions + 3 CP |

---

## 5. Throughput sizing (sets number of locos)

- Annual FFB = 63 ha × 22 t/ha = **1,386 t/yr**
- Peak month (12%) = **166 t** → over 25 working days = **6.6 t/day** average
- Apply ~2× for uneven harvest rounds / heavy days → **design ~14 t/day**

**Loco cycle (worst-case branch):** ramp → trunk → main → far branch end ≈ 1.05 km one
way; at ~55 m/min plus load/unload/switching ≈ **40–53 min/cycle** → **~11–13 trips/day**
per loco. At ~1.0 t/trip:

| Locos | Capacity/day | Verdict |
|---|---|---|
| 1 | ~11–13 t | Marginal at peak, no redundancy |
| **2** | **~22–26 t** | **Recommended** — covers 14 t/day peak with spare capacity |

Run **2 locos in peak season, 1 in slack**. Bins in circulation ≈ 60–90 (≈2–3 staged per
active branch loading point); a train = 4 × 250 kg or 2 × 500 kg bins.

---

## 6. Routing decision rules & special cases

1. **Gradient check first.** Walk each main segment against the DEM. If any stretch
   exceeds the **rack limit (~31°)**, either (a) re-route the main diagonally across the
   contour to cut effective grade, or (b) bench/terrace that stretch.
2. **Tier break.** At the adhesion→rack change (here ~12°→22°) insert a **smooth vertical
   curve** and start the rack rail a few metres below the break so engagement is on the
   gentler grade.
3. **Junctions = turntables, not tight curves.** Branch entries are ~90°; if the loco's
   min radius (≈3 m for light units, more for bin trains) can't make the turn, the
   junction is a **turntable on a level pad**. That is why turntables, not curves, mark
   every junction on the schematic.
4. **Never turn/park loaded on grade.** All turntables and sidings sit on benched level
   pads.
5. **Drainage / streams.** Cross **perpendicular** on a short reinforced trestle span;
   keep junctions and turntables off the crossing.
6. **Line spacing = harvest reach.** Keep every palm ≤ ~40 m from a branch (⇒ ≤ 80 m
   spacing). Tighten spacing only where yield/terrain justifies the extra track cost.
7. **One exit.** The trunk funnels all three columns to the **central CP2 ramp**, so only
   one lorry-loading operation runs during peak.

---

## 7. Adapting this to your real estate

Replace the Section-1 assumptions with site data and re-run the same steps:

1. Drop your **contour map / DEM / GPS** under the block polygons.
2. Fix **collection points** on the actual road, then lay the **trunk** along the toe.
3. Run **mains up the fall line**; tag each segment adhesion vs. rack from the DEM.
4. Add **contour branches** at ≤80 m spacing across each block width.
5. Place **turntables** at junctions and **sidings** at CPs (level pads).
6. Re-check gradients; re-route/terrace any over-limit stretch.
7. Re-size **locos/bins** from your real yield and peak-crop fraction.

`generate_layout.py` is parametric (column centres, block size, branch levels, reach,
tier break) — edit those constants to redraw the schematic for your numbers.

> Note: lengths, post counts and cycle times are **planning-grade** estimates from the
> assumed geometry, not a construction issue. Confirm gradients on a real DEM and lock
> capacities against your monorail supplier's loco/track datasheet before procurement.
