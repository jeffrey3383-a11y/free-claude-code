#!/usr/bin/env python3
"""Render a schematic track-layout diagram for a Monkey Monorail estate.

Geometry and figures are derived from ``monkey-monorail-bundle.json`` (the product
and sizing source of truth) so the drawing, the numbers in ``layout-routing-plan.md``
and the bundle stay consistent. Pure stdlib; emits an SVG vector file that opens in
any browser.

Usage:
    uv run farm-monorail/generate_layout.py [acres]   # default 5
"""

from __future__ import annotations

import html
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BUNDLE_PATH = Path(__file__).with_name("monkey-monorail-bundle.json")
SVG_PATH = Path(__file__).with_name("estate-layout.svg")
ACRE_M2 = 4046.8564224


def load_bundle(path: Path = BUNDLE_PATH) -> dict[str, Any]:
    """Load the Monkey Monorail product/sizing bundle."""
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class EstateSpec:
    """A sized monorail estate, resolved from the bundle for a given acreage."""

    acres: float
    hectares: float
    shape: str
    short_side_m: float
    long_side_m: float
    lanes: int
    lane_spacing_m: float
    spur_per_lane_m: float
    rail_length_m: float
    locomotives: int
    carts: int
    switches: int
    posts: int
    ffb_t_per_year: float
    turnkey_rm: float | None
    payback_years: float | None


# ---- Sizing (mirrors the bundle's geometric formulas) -------------------------


def plot_dimensions(acres: float, aspect_ratio: float) -> tuple[float, float]:
    """Return (short_side, long_side) in metres for a rectangular strip plot."""
    area = acres * ACRE_M2
    short = math.sqrt(area / aspect_ratio)
    return short, short * aspect_ratio


def lane_count(short_side_m: float, lane_spacing_m: float) -> int:
    """Number of parallel main lanes needed to keep every palm within reach."""
    return max(1, math.ceil(short_side_m / lane_spacing_m))


def compute_rail_length(
    lanes: int, long_side_m: float, spur_per_lane_m: float
) -> float:
    """Geometric rail length: one main per lane along the long side, plus a spur each."""
    return lanes * long_side_m + lanes * spur_per_lane_m


def switch_count(lanes: int) -> int:
    """Y-switches per the bundle rule: MAX(2, lanes - 1)."""
    return max(2, lanes - 1)


def post_count(rail_len_m: float, post_spacing_m: float, lanes: int) -> int:
    """Support posts at the bundle's spacing, plus one terminal post per lane."""
    return math.ceil(rail_len_m / post_spacing_m) + lanes


def _canonical_matrix(bundle: dict[str, Any]) -> dict[int, Any]:
    """Map the bundle's ``sizing_matrix_2026`` rows to {acres: row}."""
    matrix = bundle["sizing_matrix_2026"]
    return {
        int(key.removesuffix("_acres")): row
        for key, row in matrix.items()
        if key.endswith("_acres")
    }


def _interpolate_locomotives(acres: float, matrix: dict[int, Any]) -> int:
    """Linearly interpolate locomotive count between validated canonical sizes."""
    sizes = sorted(matrix)
    locos = [int(matrix[s]["locomotives"]) for s in sizes]
    if acres <= sizes[0]:
        return locos[0]
    if acres >= sizes[-1]:
        return max(1, math.ceil(locos[-1] * acres / sizes[-1]))
    for i in range(1, len(sizes)):
        if acres <= sizes[i]:
            lo, hi = sizes[i - 1], sizes[i]
            frac = (acres - lo) / (hi - lo)
            return max(1, math.ceil(locos[i - 1] + frac * (locos[i] - locos[i - 1])))
    return locos[-1]


def estate_spec(acres: float, bundle: dict[str, Any]) -> EstateSpec:
    """Resolve a full estate spec for ``acres``.

    Canonical sizes (those in ``sizing_matrix_2026``) use the field-validated matrix
    verbatim; other sizes are derived from the bundle's geometric formulas.
    """
    rules = bundle["sizing_rules"]
    lane_spacing = float(rules["lane_spacing_m_optimal"])
    spur = float(rules["spur_per_lane_m"])
    post_spacing = float(rules["post_spacing_m"])
    aspect = float(rules["default_aspect_ratio_sabah"])
    carts_per_loco = int(rules["carts_per_locomotive"])
    ha_per_acre = float(rules["acres_to_hectares"])
    yield_t = float(bundle["sabah_benchmarks_2026"]["ffb_yield_t_per_acre_per_year"])

    matrix = _canonical_matrix(bundle)
    row = matrix.get(int(acres)) if float(acres).is_integer() else None

    if row is not None:
        dims = row["plot_dim_m"]
        short_side, long_side = float(dims[0]), float(dims[1])
        shape = str(row["shape"])
        lanes = int(row["lanes"])
        rail = float(row["rail_length_m"])
        switches = int(row["switches"])
        locomotives = int(row["locomotives"])
        carts = int(row["carts"])
        ffb = float(row["ffb_t_per_year"])
        turnkey: float | None = float(row["turnkey_rm"])
        payback: float | None = float(row["payback_years"])
    else:
        short_side, long_side = plot_dimensions(acres, aspect)
        shape = f"1:{aspect:g} strip"
        lanes = lane_count(short_side, lane_spacing)
        rail = compute_rail_length(lanes, long_side, spur)
        switches = switch_count(lanes)
        locomotives = _interpolate_locomotives(acres, matrix)
        carts = locomotives * carts_per_loco
        ffb = acres * yield_t
        turnkey = None
        payback = None

    return EstateSpec(
        acres=float(acres),
        hectares=acres * ha_per_acre,
        shape=shape,
        short_side_m=short_side,
        long_side_m=long_side,
        lanes=lanes,
        lane_spacing_m=lane_spacing,
        spur_per_lane_m=spur,
        rail_length_m=rail,
        locomotives=locomotives,
        carts=carts,
        switches=switches,
        posts=post_count(rail, post_spacing, lanes),
        ffb_t_per_year=ffb,
        turnkey_rm=turnkey,
        payback_years=payback,
    )


# ---- SVG primitives (all coordinates in px) -----------------------------------


def svg_line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    stroke: str,
    width: float,
    dash: str | None = None,
    cap: str = "round",
) -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{width}" stroke-linecap="{cap}"{d}/>'
    )


def svg_text(
    x: float,
    y: float,
    s: str,
    size: float = 13,
    anchor: str = "start",
    fill: str = "#222",
    weight: str = "normal",
    italic: bool = False,
) -> str:
    st = ' font-style="italic"' if italic else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Helvetica,Arial,sans-serif" '
        f'font-size="{size}" text-anchor="{anchor}" fill="{fill}" '
        f'font-weight="{weight}"{st}>{html.escape(s, quote=False)}</text>'
    )


def svg_circle(
    cx: float,
    cy: float,
    r: float,
    fill: str,
    stroke: str = "#7a3d00",
    width: float = 1.5,
) -> str:
    return (
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{width}"/>'
    )


def svg_rect(
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
    stroke: str = "none",
    width: float = 1.0,
    dash: str | None = None,
    rx: float = 0.0,
) -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{width}" rx="{rx}"{d}/>'
    )


def svg_square(
    cx: float, cy: float, side: float, fill: str, stroke: str = "#000"
) -> str:
    return svg_rect(cx - side / 2, cy - side / 2, side, side, fill, stroke, 1.5)


def svg_star(
    cx: float, cy: float, r: float, fill: str = "#c81e1e", stroke: str = "#7a0000"
) -> str:
    pts = " ".join(
        f"{cx + (r if i % 2 == 0 else r * 0.45) * math.cos(-math.pi / 2 + i * math.pi / 5):.1f},"
        f"{cy + (r if i % 2 == 0 else r * 0.45) * math.sin(-math.pi / 2 + i * math.pi / 5):.1f}"
        for i in range(10)
    )
    return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'


# ---- Diagram ------------------------------------------------------------------

PLOT_PX_H = 540.0
MAIN_RED = "#d11f1f"
SPUR_RED = "#d11f1f"
HEADER_GREEN = "#1f7a3d"
SWITCH_ORANGE = "#ffae42"
REACH_FILL = "#e7f4e1"
PLOT_GREEN = "#9bbf8c"


def _fmt_rm(value: float | None) -> str:
    return f"RM {value:,.0f}" if value is not None else "by quotation"


def build_svg(spec: EstateSpec, bundle: dict[str, Any]) -> str:
    product = bundle["product"]
    engine = product["engine"]
    transport = product["transport"]
    rail = product["rail"]
    warranty = bundle["warranty"]
    worker_reach = float(bundle["sizing_rules"]["worker_carry_m_max"])

    s = PLOT_PX_H / spec.long_side_m
    ml, mt = 70, 96
    plot_w = spec.short_side_m * s
    plot_h = spec.long_side_m * s
    leg_w = 330
    # Floor the width so the title/subtitle/footer fit even for a narrow strip plot.
    width = max(int(ml + plot_w + 70 + leg_w + 30), 740)
    height = int(mt + plot_h + 150)

    def to_px(x: float, y: float) -> tuple[float, float]:
        """Plan metres -> px; north (increasing y) is up, the road sits at y=0."""
        return ml + x * s, mt + (spec.long_side_m - y) * s

    span = (spec.lanes - 1) * spec.lane_spacing_m
    start = (spec.short_side_m - span) / 2
    lane_x = [start + i * spec.lane_spacing_m for i in range(spec.lanes)]

    out: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Helvetica,Arial,sans-serif">',
        svg_rect(0, 0, width, height, "#ffffff"),
        svg_text(ml, 36, "Monkey Monorail — Estate Track Layout", 22, weight="bold"),
        svg_text(
            ml,
            58,
            f"Model {product['model']} · {spec.acres:g} acres ({spec.hectares:.2f} ha) "
            f"· {spec.shape} · road-frontage Sabah smallholding",
            13.5,
            fill="#555",
        ),
        svg_text(
            ml,
            77,
            "Parallel up-field mains (one per lane) into a road-edge header + loading station.",
            12,
            fill="#777",
            italic=True,
        ),
    ]

    # Worker-carry corridors (one band per lane, +/- max manual carry).
    out.extend(
        svg_rect(
            to_px(lx - worker_reach, spec.long_side_m)[0],
            to_px(lx - worker_reach, spec.long_side_m)[1],
            2 * worker_reach * s,
            plot_h,
            REACH_FILL,
        )
        for lx in lane_x
    )

    # Plot outline.
    p_top = to_px(0, spec.long_side_m)
    out.append(
        svg_rect(p_top[0], p_top[1], plot_w, plot_h, "none", PLOT_GREEN, 1, dash="3,3")
    )
    pl = to_px(spec.short_side_m, spec.long_side_m)
    out.append(
        svg_text(
            pl[0] + 8,
            pl[1] + 14,
            f"{spec.short_side_m:.0f} m frontage",
            11,
            fill="#6f8f63",
        )
    )
    pd = to_px(spec.short_side_m, spec.long_side_m / 2)
    out.append(
        svg_text(pd[0] + 8, pd[1], f"{spec.long_side_m:.0f} m deep", 11, fill="#6f8f63")
    )

    # Road band + estate road label (below the plot, y < 0).
    road_h = 22.0
    r0 = to_px(0, 0)
    out.append(svg_rect(r0[0], r0[1], plot_w, road_h, "#d9d2c5"))
    out.append(
        svg_text(
            r0[0] + plot_w / 2,
            r0[1] + 15,
            "ESTATE ROAD  (lorry route to mill)",
            12.5,
            anchor="middle",
            fill="#6b6253",
            weight="bold",
        )
    )

    # Header/trunk rail along the road edge, linking every main.
    h_left = to_px(lane_x[0], 0)
    h_right = to_px(lane_x[-1], 0)
    out.append(svg_line(h_left[0], h_left[1], h_right[0], h_right[1], HEADER_GREEN, 5))

    # Mains (up-field, one per lane) + reach centre-line label.
    for lx in lane_x:
        a = to_px(lx, 0)
        b = to_px(lx, spec.long_side_m)
        out.append(svg_line(a[0], a[1], b[0], b[1], MAIN_RED, 3.4))
    # Y-switch at every main x header junction.
    for lx in lane_x:
        jx, jy = to_px(lx, 0)
        out.append(svg_circle(jx, jy, 5, SWITCH_ORANGE))

    # Loading station (square) + FFB ramp (star) at the centre of the header.
    cx = sum(lane_x) / len(lane_x)
    st = to_px(cx, 0)
    out.append(svg_square(st[0], st[1], 13, "#000"))
    ramp = to_px(cx, 0)
    out.append(svg_star(ramp[0], ramp[1] - road_h / 2, 10))
    out.append(
        svg_text(
            st[0] + 12,
            st[1] + 26,
            "loading station",
            11.5,
            weight="bold",
            fill="#8a0000",
        )
    )

    # Reach callout on the first lane.
    co = to_px(lane_x[0] - worker_reach, spec.long_side_m * 0.6)
    out.append(
        svg_text(
            co[0] - 4,
            co[1],
            f"↔ {worker_reach:.0f} m max carry",
            10.5,
            anchor="start",
            fill="#4a7a3a",
        )
    )

    # North arrow.
    nx, ny = ml + 6, mt + 16
    out.append(
        f'<polygon points="{nx},{ny} {nx - 7},{ny + 18} {nx},{ny + 12} {nx + 7},{ny + 18}" fill="#333"/>'
    )
    out.append(svg_text(nx, ny - 6, "N", 13, anchor="middle", weight="bold"))

    # Scale bar (50 m).
    sb_y = mt + plot_h + 60
    out.append(svg_line(ml, sb_y, ml + 50 * s, sb_y, "#333", 3))
    out.append(svg_line(ml, sb_y - 5, ml, sb_y + 5, "#333", 2))
    out.append(svg_line(ml + 50 * s, sb_y - 5, ml + 50 * s, sb_y + 5, "#333", 2))
    out.append(
        svg_text(ml + 25 * s, sb_y - 8, "50 m", 12, anchor="middle", fill="#333")
    )

    # ---- Legend + key-figures panel -----------------------------------------
    lx0 = ml + plot_w + 70
    out.append(svg_rect(lx0, mt, leg_w, 196, "#fafafa", "#ddd", 1, rx=6))
    out.append(svg_text(lx0 + 14, mt + 24, "LEGEND", 15, weight="bold"))
    legend = [
        (MAIN_RED, 3.4, "Main line (up-field, one per lane)", None),
        (HEADER_GREEN, 5, "Header rail (links mains at the road)", None),
        (SPUR_RED, 2.4, "Spur (5 m, main -> header)", "4,3"),
    ]
    yy = mt + 48
    for color, lw, label, dash in legend:
        out.append(svg_line(lx0 + 16, yy, lx0 + 56, yy, color, lw, dash=dash))
        out.append(svg_text(lx0 + 66, yy + 4, label, 12.5))
        yy += 28
    out.append(svg_square(lx0 + 36, yy, 13, "#000"))
    out.append(svg_text(lx0 + 66, yy + 4, "Loading station (lorry transfer)", 12.5))
    yy += 28
    out.append(svg_circle(lx0 + 36, yy, 6, SWITCH_ORANGE))
    out.append(svg_text(lx0 + 66, yy + 4, "Y-switch (junction)", 12.5))
    yy += 24
    out.append(svg_rect(lx0 + 16, yy - 8, 40, 16, REACH_FILL, "#cfe3c6"))
    out.append(
        svg_text(
            lx0 + 66, yy + 4, f"Harvester carry corridor (≤{worker_reach:.0f} m)", 12.5
        )
    )

    out.append(svg_rect(lx0, mt + 210, leg_w, 380, "#f4f7fb", "#dbe4f0", 1, rx=6))
    out.append(
        svg_text(lx0 + 14, mt + 234, "KEY FIGURES", 14, weight="bold", fill="#234")
    )
    figures = [
        f"Estate: {spec.acres:g} ac ({spec.hectares:.2f} ha) · {spec.shape}",
        f"Plot: {spec.short_side_m:.0f} m x {spec.long_side_m:.0f} m",
        f"Rail total: {spec.rail_length_m:,.0f} m",
        f"Lanes / mains: {spec.lanes}  (spacing {spec.lane_spacing_m:.0f} m)",
        f"Locomotives: {spec.locomotives}  ·  Carts: {spec.carts} (300 kg each)",
        f"Y-switches: {spec.switches}  ·  Posts @{rail['post_spacing_m_max']:g} m: ~{spec.posts:,}",
        f"FFB throughput: {spec.ffb_t_per_year:,.0f} t/year",
        f"Turnkey capex: {_fmt_rm(spec.turnkey_rm)}",
        f"Payback: {spec.payback_years} years"
        if spec.payback_years
        else "Payback: by quotation",
        "",
        f"Engine: {engine['make']} {engine['model']} "
        f"({engine['rated_power_kw']} kW / {engine['rated_power_hp']} HP, {engine['displacement_class_cc']}cc)",
        f"Drive: {transport['drive_system']} · max slope {transport['max_slope_deg']}deg",
        f"Cart: {transport['cargo_capacity_kg_per_cart']} kg "
        f"({transport['cargo_capacity_ffb_bunches_per_cart']} bunches)",
        f"Rail: {rail['material']}",
        f"Warranty: engine {warranty['engine_years']} yr · rail {warranty['railing_years']} yr",
    ]
    ky = mt + 258
    for figure in figures:
        weight = "bold" if figure.startswith(("Rail total", "Turnkey")) else "normal"
        out.append(svg_text(lx0 + 16, ky, figure, 11.6, fill="#234", weight=weight))
        ky += 21

    out.append(
        svg_text(
            ml,
            height - 16,
            f"{bundle['brand']['tagline_en']}  —  {bundle['brand']['by_line']}  ·  "
            "planning-grade schematic.",
            11,
            fill="#888",
            italic=True,
        )
    )
    out.append("</svg>")
    return "\n".join(out)


def main(argv: list[str]) -> None:
    acres = float(argv[1]) if len(argv) > 1 else 5.0
    bundle = load_bundle()
    spec = estate_spec(acres, bundle)
    svg = build_svg(spec, bundle)
    SVG_PATH.write_text(svg, encoding="utf-8")
    print(
        f"wrote {SVG_PATH} for {spec.acres:g} acres "
        f"({spec.lanes} lanes, {spec.rail_length_m:,.0f} m rail, "
        f"{spec.locomotives} loco, {spec.carts} carts)"
    )


if __name__ == "__main__":
    main(sys.argv)
