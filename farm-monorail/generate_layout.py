#!/usr/bin/env python3
"""Render a schematic track-layout diagram for the example palm-oil estate monorail.

Pure stdlib. Emits an SVG (vector, opens in any browser). Geometry is parametric
so the numbers in layout-routing-plan.md and the drawing stay consistent.
"""

from __future__ import annotations

import math

# ---- Estate / network parameters (plan view, metres) --------------------------
COLS = [175.0, 525.0, 875.0]          # E-W centre of each block column / main line
COL_WIDTH = 350.0
DEPTH = 600.0                          # S->N up-slope extent of planted area
BRANCH_LEVELS = [60, 140, 220, 300, 380, 460, 540]  # up-slope position of each branch
BRANCH_REACH = 150.0                   # each branch extends this far either side of its main
TIER_BREAK = 300.0                     # below = adhesion zone, above = rack-and-pinion
ROAD_Y = -45.0                         # valley road / trunk-to-road band

# ---- Drawing setup ------------------------------------------------------------
S = 0.92                               # px per metre
ML, MT = 95, 120                       # left / top margin (px)
PLAN_W = COLS[-1] + COL_WIDTH / 2      # 1050
LEG_W = 300
W = int(ML + PLAN_W * S + 40 + LEG_W + 30)
H = int(MT + (DEPTH + 80) * S + 150)


def px(x: float, y: float) -> tuple[float, float]:
    """Plan metres -> SVG px (north is up)."""
    return ML + x * S, MT + (DEPTH - y) * S


def line(x1, y1, x2, y2, stroke, w, dash=None, cap="round"):
    a = px(x1, y1)
    b = px(x2, y2)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" '
            f'stroke="{stroke}" stroke-width="{w}" stroke-linecap="{cap}"{d}/>')


def text(x, y, s, size=13, anchor="start", fill="#222", weight="normal", italic=False):
    st = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Helvetica,Arial,sans-serif" '
            f'font-size="{size}" text-anchor="{anchor}" fill="{fill}" '
            f'font-weight="{weight}"{st}>{s}</text>')


def circle(x, y, r, fill, stroke="#7a3d00", w=1.5):
    a = px(x, y)
    return f'<circle cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"/>'


def square(x, y, side, fill, stroke="#000", w=1.5):
    a = px(x, y)
    return (f'<rect x="{a[0]-side/2:.1f}" y="{a[1]-side/2:.1f}" width="{side}" height="{side}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{w}"/>')


def star(x, y, r, fill="#c81e1e"):
    a = px(x, y)
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append(f"{a[0]+rr*math.cos(ang):.1f},{a[1]+rr*math.sin(ang):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="#7a0000" stroke-width="1"/>'


out: list[str] = []
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">')
out.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>')

# Title
out.append(text(ML, 38, "Palm-Oil Estate Field Monorail — Schematic Track Layout", 22, weight="bold"))
out.append(text(ML, 62, "Example hilly cluster · ~63 ha · 6 blocks · valley road on south edge", 14, fill="#555"))
out.append(text(ML, 82, "Comb layout: up-slope mains (carry the grade) + near-level contour branches + bottom trunk linking collection points",
                12.5, fill="#777", italic=True))

# Slope zone bands
tb_top = px(0, DEPTH); tb_mid = px(0, TIER_BREAK); tb_bot = px(0, 0)
adh = px(PLAN_W, 0)
out.append(f'<rect x="{tb_bot[0]:.1f}" y="{tb_mid[1]:.1f}" width="{PLAN_W*S:.1f}" '
           f'height="{(tb_bot[1]-tb_mid[1]):.1f}" fill="#e7f4e1"/>')   # adhesion (lower)
out.append(f'<rect x="{tb_top[0]:.1f}" y="{tb_top[1]:.1f}" width="{PLAN_W*S:.1f}" '
           f'height="{(tb_mid[1]-tb_top[1]):.1f}" fill="#fdeede"/>')    # rack (upper)

# Contour lines + elevation labels (base 40 m at road)
for y, elev in [(0, 40), (150, 72), (300, 104), (450, 165), (600, 225)]:
    out.append(line(0, y, PLAN_W, y, "#bdbdbd", 1, dash="2,5"))
    a = px(PLAN_W, y)
    out.append(text(a[0] + 6, a[1] + 4, f"{elev} m", 11, fill="#999"))

# Tier-break (adhesion / rack transition) line
out.append(line(0, TIER_BREAK, PLAN_W, TIER_BREAK, "#e08a2e", 2, dash="9,5"))
tbl = px(PLAN_W / 2, TIER_BREAK)
out.append(text(tbl[0], tbl[1] - 8, "↑ rack-and-pinion zone (slope ~16–28°)   —   adhesion zone (slope ≤8–14°) ↓",
                12.5, anchor="middle", fill="#b3690f", weight="bold"))

# Block outlines + labels
labels = [["A", "B", "C"], ["D", "E", "F"]]
for ti, (y0, y1) in enumerate([(0, TIER_BREAK), (TIER_BREAK, DEPTH)]):
    for ci, cx in enumerate(COLS):
        x0, x1 = cx - COL_WIDTH / 2, cx + COL_WIDTH / 2
        p0 = px(x0, y1); p1 = px(x1, y0)
        out.append(f'<rect x="{p0[0]:.1f}" y="{p0[1]:.1f}" width="{(x1-x0)*S:.1f}" '
                   f'height="{(y1-y0)*S:.1f}" fill="none" stroke="#9bbf8c" stroke-width="1" stroke-dasharray="3,3"/>')
        lp = px(x0 + 10, y1 - 14)
        out.append(text(lp[0], lp[1], f"Block {labels[ti][ci]}  (~10.5 ha)", 12, fill="#6f8f63", weight="bold"))

# Road band + label
r0 = px(0, ROAD_Y);
out.append(f'<rect x="{r0[0]:.1f}" y="{px(0,0)[1]:.1f}" width="{PLAN_W*S:.1f}" '
           f'height="{abs(ROAD_Y)*S:.1f}" fill="#d9d2c5"/>')
rl = px(PLAN_W / 2, ROAD_Y / 2)
out.append(text(rl[0], rl[1] + 4, "ESTATE ROAD  (lorry route)", 13, anchor="middle", fill="#6b6253", weight="bold"))

# Trunk line (links collection points along the toe of the slope)
out.append(line(COLS[0], 0, COLS[-1], 0, "#1f7a3d", 6))
trl = px(COLS[-1], 0)
out.append(text(trl[0] + 8, trl[1] - 6, "trunk line", 11.5, fill="#1f7a3d", weight="bold"))

# Branches (contour, near-level) + turntable markers at each junction
for cx in COLS:
    for by in BRANCH_LEVELS:
        out.append(line(cx - BRANCH_REACH, by, cx + BRANCH_REACH, by, "#1f5fbf", 2.4))
        out.append(circle(cx, by, 4.5, "#ffae42"))  # switch / turntable at main x branch

# Main lines (up-slope, carry the grade)
for cx in COLS:
    out.append(line(cx, 0, cx, DEPTH, "#d11f1f", 4))

# Collection points (square) + loading ramp (star at centre CP) + holding sidings
for i, cx in enumerate(COLS, start=1):
    # holding siding: short parallel stub just up-slope of CP
    out.append(line(cx + 22, 8, cx + 22, 48, "#d11f1f", 2.4, dash="4,3"))
    out.append(line(cx, 8, cx + 22, 8, "#d11f1f", 2))
    out.append(square(cx, 0, 13, "#000"))
    out.append(circle(cx, 0, 6, "#ffae42"))  # CP turntable on trunk
    cp = px(cx, 0)
    out.append(text(cp[0] - 16, cp[1] + 20, f"CP{i}", 12.5, weight="bold"))

# Central FFB loading ramp at CP2
out.append(star(COLS[1], -18, 11))
lr = px(COLS[1], -18)
out.append(text(lr[0] + 16, lr[1] + 4, "FFB loading ramp", 12, weight="bold", fill="#8a0000"))

# Callout: min curve radius at a branch entry
co = px(COLS[0] - BRANCH_REACH, BRANCH_LEVELS[3])
out.append(f'<circle cx="{co[0]:.1f}" cy="{co[1]:.1f}" r="9" fill="none" stroke="#555" stroke-width="1"/>')
out.append(text(co[0] - 12, co[1] - 14, "min curve R ≈ 3 m", 11, anchor="end", fill="#555"))

# North arrow
nx, ny = ML + 8, MT + 18
out.append(f'<polygon points="{nx},{ny} {nx-7},{ny+18} {nx},{ny+12} {nx+7},{ny+18}" fill="#333"/>')
out.append(text(nx, ny - 6, "N", 13, anchor="middle", weight="bold"))

# Scale bar (100 m)
sb_y = MT + (DEPTH + 78) * S
sb_x = ML
out.append(f'<line x1="{sb_x}" y1="{sb_y}" x2="{sb_x+100*S}" y2="{sb_y}" stroke="#333" stroke-width="3"/>')
out.append(f'<line x1="{sb_x}" y1="{sb_y-5}" x2="{sb_x}" y2="{sb_y+5}" stroke="#333" stroke-width="2"/>')
out.append(f'<line x1="{sb_x+100*S}" y1="{sb_y-5}" x2="{sb_x+100*S}" y2="{sb_y+5}" stroke="#333" stroke-width="2"/>')
out.append(text(sb_x + 100 * S / 2, sb_y - 8, "100 m", 12, anchor="middle", fill="#333"))

# ---- Legend panel -------------------------------------------------------------
lx = ML + PLAN_W * S + 40
ly = MT
out.append(f'<rect x="{lx}" y="{ly}" width="{LEG_W}" height="430" fill="#fafafa" stroke="#ddd" stroke-width="1" rx="6"/>')
out.append(text(lx + 14, ly + 26, "LEGEND", 15, weight="bold"))
yy = ly + 52


def leg_line(color, w, label, dash=None):
    global yy
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(f'<line x1="{lx+16}" y1="{yy}" x2="{lx+56}" y2="{yy}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"{d}/>')
    out.append(text(lx + 66, yy + 4, label, 12.5))
    yy += 30


def leg_mark(svg_mark, label):
    global yy
    out.append(svg_mark)
    out.append(text(lx + 66, yy + 4, label, 12.5))
    yy += 30


leg_line("#d11f1f", 4, "Main line (up-slope, carries grade)")
leg_line("#1f5fbf", 2.4, "Branch (contour, near-level, harvesting)")
leg_line("#1f7a3d", 6, "Trunk line (links collection points)")
leg_line("#d11f1f", 2.4, "Holding siding (full-bin buffer)", dash="4,3")
leg_line("#e08a2e", 2, "Adhesion / rack transition", dash="9,5")
leg_line("#bdbdbd", 1, "Contour (elevation)", dash="2,5")

# marker legend rows (draw markers at fixed legend px)
def lmark_circle(fill, stroke):
    return f'<circle cx="{lx+36}" cy="{yy}" r="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'

leg_mark(f'<rect x="{lx+30}" y="{yy-6}" width="13" height="13" fill="#000"/>', "Collection point (CP) + lorry transfer")
leg_mark(lmark_circle("#ffae42", "#7a3d00"), "Turntable / switch (junction)")
out.append(star(0, 0, 0))  # noop keep import used
star_svg = f'<polygon points="' + " ".join(
    f"{lx+36+ (11 if i%2==0 else 4.95)*math.cos(-math.pi/2+i*math.pi/5):.1f},{yy+(11 if i%2==0 else 4.95)*math.sin(-math.pi/2+i*math.pi/5):.1f}"
    for i in range(10)) + '" fill="#c81e1e" stroke="#7a0000" stroke-width="1"/>'
leg_mark(star_svg, "FFB loading ramp (to lorry)")

# zone swatches
out.append(f'<rect x="{lx+16}" y="{yy-8}" width="40" height="16" fill="#e7f4e1" stroke="#cfe3c6"/>')
out.append(text(lx + 66, yy + 4, "Adhesion zone (≤8–14°)", 12.5)); yy += 26
out.append(f'<rect x="{lx+16}" y="{yy-8}" width="40" height="16" fill="#fdeede" stroke="#f3d7bf"/>')
out.append(text(lx + 66, yy + 4, "Rack-and-pinion zone (16–28°)", 12.5)); yy += 30

# Key figures box
out.append(f'<rect x="{lx}" y="{ly+450}" width="{LEG_W}" height="200" fill="#f4f7fb" stroke="#dbe4f0" stroke-width="1" rx="6"/>')
out.append(text(lx + 14, ly + 476, "KEY FIGURES", 14, weight="bold", fill="#234"))
ky = ly + 500
for s in [
    "Area served: ~63 ha (6 blocks)",
    "Track total: ~9.0 km (~143 m/ha)",
    "  • 3 mains ≈ 1.9 km · 21 branches ≈ 6.3 km",
    "  • trunk ≈ 0.70 km · sidings ≈ 0.12 km",
    "Support posts: ~3,600–4,000 (@~2.5 m)",
    "Turntables/switches: 24",
    "Peak throughput: ~14 t/day → 2 locos",
    "Loco: rack-capable, ~1.0 t payload/trip",
]:
    out.append(text(lx + 16, ky, s, 11.8, fill="#234")); ky += 19

out.append('</svg>')

with open("farm-monorail/estate-layout.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("wrote farm-monorail/estate-layout.svg", f"({W}x{H})")
