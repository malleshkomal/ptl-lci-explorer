import sys
import warnings
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore", module="openpyxl")

from lcitools.circularity import (Params, carbon_loop, eol_coverage,  # noqa: E402
                                  material_inputs, mci, screening_gwp)
from lcitools.model import inventory  # noqa: E402
from lcitools.reader import dataset_paths, read_brightway_csv  # noqa: E402


@pytest.fixture(scope="module")
def totals():
    _, acts, excs = read_brightway_csv(dataset_paths(ROOT / "data/original/power-to-liquid")["csv"])
    return {fu: inventory(acts, excs, {act: 1.0})[0]
            for fu, act in {"ptl": "GTL production", "lh2": "Hydrogen liquefaction"}.items()}


def test_concrete_volume_converts_to_waste_mass(totals):
    # GTL plant: 345,000 m3 concrete and 828,000 t waste reinforced concrete -> 2400 kg/m3
    cov = eol_coverage(totals["ptl"])
    assert cov.loc["concrete", "coverage"] == pytest.approx(1.0, abs=0.01)


def test_liquefaction_plant_has_no_concrete_or_copper_end_of_life(totals):
    cov = eol_coverage(totals["lh2"])
    assert cov.loc["concrete", "coverage"] < 0.02
    assert cov.loc["copper", "route"] == "none modelled"


def test_carbon_loop_closes_within_one_percent(totals):
    assert carbon_loop(totals["ptl"])["closure"] == pytest.approx(1.0, abs=0.01)


def test_mci_is_linear_at_reference_and_rises_with_circularity(totals):
    t = totals["ptl"]
    assert mci(t) == pytest.approx(0.1)
    assert mci(t, Params(recycled_content=1, eol_recycling=1)) > 0.5
    assert mci(t, Params(lifetime=2)) > mci(t)


def test_lifetime_scales_material_burden_inversely(totals):
    t = totals["ptl"]
    one, two = screening_gwp(t), screening_gwp(t, Params(lifetime=2))
    assert two["materials"] == pytest.approx(one["materials"] / 2)
    assert two["electricity"] == one["electricity"]


@pytest.mark.parametrize("fu", ["ptl", "lh2"])
def test_recycling_is_never_credited_twice(totals, fu):
    t = totals[fu]
    cut = Params(rule="cut-off", recycled_content=0.5)
    eol = Params(rule="end-of-life", eol_recycling=0.5)
    # cut-off ignores end-of-life recycling; end-of-life ignores recycled content
    assert screening_gwp(t, replace(cut, eol_recycling=1))["total"] == pytest.approx(screening_gwp(t, cut)["total"])
    assert screening_gwp(t, replace(eol, recycled_content=1))["total"] == pytest.approx(screening_gwp(t, eol)["total"])


def test_materials_are_grams_per_kg(totals):
    assert material_inputs(totals["ptl"]).sum() == pytest.approx(0.0197, rel=0.01)
