"""Tests for the bundle-driven Monkey Monorail layout generator.

``farm-monorail/`` is not an importable package (the directory name contains a
hyphen), so the generator module is loaded by path. The tests assert that the
generator stays consistent with ``monkey-monorail-bundle.json`` — in particular
that it reproduces the field-validated ``sizing_matrix_2026`` exactly.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "farm-monorail" / "generate_layout.py"
MODULE_NAME = "farm_monorail_layout"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec so `@dataclass` under `from __future__ import annotations`
    # can resolve the module via sys.modules during class processing.
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


layout = _load_module()
BUNDLE = layout.load_bundle()
CANONICAL = layout._canonical_matrix(BUNDLE)
CANONICAL_SIZES = sorted(CANONICAL)


def test_canonical_sizes_present() -> None:
    assert CANONICAL_SIZES == [5, 10, 15, 30]


@pytest.mark.parametrize("acres", CANONICAL_SIZES)
def test_canonical_sizes_match_matrix(acres: int) -> None:
    row = CANONICAL[acres]
    spec = layout.estate_spec(acres, BUNDLE)
    assert spec.lanes == row["lanes"]
    assert spec.switches == row["switches"]
    assert spec.locomotives == row["locomotives"]
    assert spec.carts == row["carts"]
    assert spec.rail_length_m == pytest.approx(row["rail_length_m"])
    assert spec.ffb_t_per_year == pytest.approx(row["ffb_t_per_year"])
    assert spec.turnkey_rm == pytest.approx(row["turnkey_rm"])
    assert spec.payback_years == pytest.approx(row["payback_years"])
    assert spec.short_side_m == pytest.approx(row["plot_dim_m"][0])
    assert spec.long_side_m == pytest.approx(row["plot_dim_m"][1])


@pytest.mark.parametrize("acres", CANONICAL_SIZES)
def test_geometric_formulas_reproduce_matrix(acres: int) -> None:
    """Independently derive lanes/rail/switches and confirm they match the matrix."""
    row = CANONICAL[acres]
    short_side, long_side = row["plot_dim_m"]
    rules = BUNDLE["sizing_rules"]
    lanes = layout.lane_count(short_side, rules["lane_spacing_m_optimal"])
    assert lanes == row["lanes"]
    rail = layout.compute_rail_length(lanes, long_side, rules["spur_per_lane_m"])
    assert rail == pytest.approx(row["rail_length_m"], abs=2.0)
    assert layout.switch_count(lanes) == row["switches"]


@pytest.mark.parametrize("acres", CANONICAL_SIZES)
def test_plot_dimensions_within_rounding(acres: int) -> None:
    row = CANONICAL[acres]
    short, long_side = row["plot_dim_m"]
    aspect = long_side / short
    derived_short, derived_long = layout.plot_dimensions(acres, aspect)
    assert derived_short == pytest.approx(short, abs=1.0)
    assert derived_long == pytest.approx(long_side, abs=1.0)


def test_ffb_follows_sabah_yield() -> None:
    yield_t = BUNDLE["sabah_benchmarks_2026"]["ffb_yield_t_per_acre_per_year"]
    spec = layout.estate_spec(5, BUNDLE)
    assert spec.ffb_t_per_year == pytest.approx(5 * yield_t, abs=0.5)


def test_interpolated_size_between_canonical() -> None:
    """A non-canonical size derives from formulas and has no fixed quote."""
    carts_per_loco = BUNDLE["sizing_rules"]["carts_per_locomotive"]
    spec = layout.estate_spec(20, BUNDLE)
    assert spec.turnkey_rm is None
    assert spec.payback_years is None
    assert spec.lanes >= 1
    assert spec.locomotives >= 1
    assert spec.carts == spec.locomotives * carts_per_loco


def test_build_svg_contains_key_facts() -> None:
    spec = layout.estate_spec(5, BUNDLE)
    svg = layout.build_svg(spec, BUNDLE)
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert BUNDLE["product"]["model"] in svg
    assert BUNDLE["product"]["engine"]["make"] in svg
    assert f"{spec.rail_length_m:,.0f} m" in svg


def test_bundle_omits_rent_amount() -> None:
    """The showroom rent must stay out of git per sensitive_data_never_publish."""
    showroom = BUNDLE["company"]["showroom"]
    assert "monthly_rent_rm" not in showroom
    assert "rent amount" in BUNDLE["sensitive_data_never_publish"]["fields"]


def test_locomotive_formula_caveat_documented() -> None:
    """The formula-vs-matrix locomotive discrepancy must stay flagged."""
    rules = BUNDLE["sizing_rules"]
    assert "_locomotives_formula_caveat" in rules
    # The validated matrix specifies 2 locomotives at 30 acres...
    assert CANONICAL[30]["locomotives"] == 2
    # ...while the documented divisor-35 formula would predict only 1.
    hectares = CANONICAL[30]["hectares"]
    assert max(1, -(-hectares // 35)) == 1
