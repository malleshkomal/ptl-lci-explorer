"""Link circularity KPIs to a screening carbon footprint through shared parameters.

Both sides are computed from the same scaled inventory (``model.inventory``)
and the same scenario ``Params``, so a change in recycled content, end-of-life
recycling or equipment lifetime moves the KPIs and the footprint together:

- Carbon loop: CO2 captured from air vs CO2 released when the fuel burns.
- Material KPIs: equipment material intensity per kg of product, and how much
  of each material has an end-of-life flow in the dataset (EoL coverage).
- Material Circularity Indicator (MCI, Ellen MacArthur Foundation 2019),
  simplified: no recycling-process losses, lifetime as the utility factor.
- Screening GWP per kg of product, with one recycling-credit rule applied at
  a time (cut-off or end-of-life) so recycling is never credited twice.

The GWP factors below are illustrative screening values, not ecoinvent 3.9
results. They are close enough to rank levers; replace them with ecoinvent
cut-off scores before quoting a footprint.
"""

from dataclasses import dataclass, field, replace

import pandas as pd

CONCRETE_DENSITY = 2400  # kg/m3; matches 'waste reinforced concrete' vs concrete volume in the GTL plant
FUEL_CO2_PER_KG = 44 / 14  # burning a -CH2- fuel releases 44/14 kg CO2 per kg
METALS = ("steel", "stainless steel", "aluminium", "copper")

# ecoinvent input -> material class
MATERIALS = {
    "market for reinforcing steel": "steel",
    "market for steel, low-alloyed": "steel",
    "market for steel, chromium steel 18/8": "stainless steel",
    "market for steel, chromium steel 18/8, hot rolled": "stainless steel",
    "market for aluminium, wrought alloy": "aluminium",
    "market for aluminium alloy, AlMg3": "aluminium",
    "market for sheet rolling, copper": "copper",
    "market for concrete, normal strength": "concrete",
    "market group for concrete, normal strength": "concrete",
    "market for corrugated board box": "other",
    "market for nitrogen, liquid": "other",
    "market for potassium hydroxide": "other",
    "market for sodium silicate, spray powder, 80%": "other",
    "market for zeolite, powder": "other",
    "market for lubricating oil": "other",
    "market for aluminium oxide, non-metallurgical": "other",
    "market for copper oxide": "other",
    "market for zinc oxide": "other",
}
# ecoinvent waste flow -> (material group, route as modelled in the dataset)
WASTES = {
    "market for waste bulk iron, excluding reinforcement": ("steel", "scrap market"),
    "market for waste reinforcement steel": ("steel", "scrap market"),
    "market for waste reinforced concrete": ("concrete", "waste market"),
    "market for waste concrete, not reinforced": ("concrete", "waste market"),
    "market for waste fibreboard": ("other", "waste market"),
    "treatment of scrap aluminium, municipal incineration": ("aluminium", "incineration"),
}
GROUP = {"steel": "steel", "stainless steel": "steel", "aluminium": "aluminium",
         "copper": "copper", "concrete": "concrete", "other": "other"}

# Illustrative screening factors, kg CO2e per kg (primary, secondary)
GWP_MATERIAL = {
    "steel": (2.3, 0.6),
    "stainless steel": (4.8, 2.0),
    "aluminium": (9.0, 0.8),
    "copper": (4.0, 1.2),
    "concrete": (0.13, 0.13),
    "other": (1.5, 1.5),
}
GWP_OTHER = {  # per kWh, kg or tkm
    "electricity production, wind, 1-3MW turbine, onshore": 0.012,
    "market for water, deionised": 0.0005,
    "transport, freight, lorry 16-32 metric ton, EURO3": 0.15,
    "market for transport, freight, lorry 16-32 metric ton, EURO6": 0.15,
    "market group for transport, freight train": 0.05,
}
ELECTRICITY = "electricity production, wind, 1-3MW turbine, onshore"


@dataclass(frozen=True)
class Params:
    """Scenario parameters shared by the KPIs and the footprint.

    recycled_content and eol_recycling apply to metals only; concrete and
    other materials stay linear. lifetime is relative to the dataset (1.0 =
    as published), so equipment per kg of product scales with 1 / lifetime.
    """
    recycled_content: float = 0.0
    eol_recycling: float = 0.0
    lifetime: float = 1.0
    rule: str = "cut-off"  # or "end-of-life" (avoided burden, 0:100)
    electricity_gwp: float = GWP_OTHER[ELECTRICITY]
    gwp_material: dict = field(default_factory=lambda: dict(GWP_MATERIAL))


def material_inputs(totals):
    """Equipment materials per functional unit in kg, by material class (as published)."""
    t = totals[(totals["type"] == "technosphere") & totals["name"].isin(MATERIALS)].copy()
    t["kg"] = t["scaled amount"] * t["unit"].map({"kilogram": 1.0, "cubic meter": CONCRETE_DENSITY})
    t["material"] = t["name"].map(MATERIALS)
    return t.groupby("material")["kg"].sum()


def eol_coverage(totals):
    """Material input vs end-of-life flow per material group, per functional unit.

    Coverage below 100% means some of the material has no end-of-life
    treatment in the dataset; the route column says where the rest goes.
    """
    inputs = material_inputs(totals).groupby(GROUP).sum()
    w = totals[totals["name"].isin(WASTES)].copy()
    w["group"] = w["name"].map(lambda n: WASTES[n][0])
    w["route"] = w["name"].map(lambda n: WASTES[n][1])
    waste = w.groupby("group")["scaled amount"].sum()
    routes = w.groupby("group")["route"].agg(lambda r: ", ".join(sorted(set(r))))
    out = pd.DataFrame({"input kg": inputs, "end-of-life kg": waste}).fillna(0.0)
    out["coverage"] = out["end-of-life kg"] / out["input kg"]
    out["route"] = routes.reindex(out.index).fillna("none modelled")
    return out.sort_values("input kg", ascending=False)


def carbon_loop(totals):
    """CO2 captured from air per kg, as a share of the CO2 the fuel releases when burned."""
    captured = totals.loc[totals["name"] == "Carbon dioxide, in air", "scaled amount"].sum()
    return {"captured kg": captured, "released kg": FUEL_CO2_PER_KG,
            "closure": captured / FUEL_CO2_PER_KG}


def _shares(material, p):
    metal = material in METALS
    return (p.recycled_content if metal else 0.0), (p.eol_recycling if metal else 0.0)


def mci(totals, p=Params()):
    """Simplified Material Circularity Indicator of the equipment (0 linear .. 1 circular)."""
    mass = material_inputs(totals) / p.lifetime
    virgin = waste = 0.0
    for material, m in mass.items():
        fr, cr = _shares(material, p)
        virgin += m * (1 - fr)
        waste += m * (1 - cr)
    lfi = (virgin + waste) / (2 * mass.sum())
    return max(0.0, 1 - lfi * 0.9 / p.lifetime)


def screening_gwp(totals, p=Params()):
    """Screening GWP per functional unit (kg CO2e), split by source.

    Cut-off: recycled content lowers the material burden; no end-of-life credit.
    End-of-life: materials are charged as primary; recycling earns a credit.
    """
    if p.rule not in ("cut-off", "end-of-life"):
        raise ValueError(f"unknown rule {p.rule!r}")
    amounts = totals.groupby("name")["scaled amount"].sum()
    out = {"electricity": amounts.get(ELECTRICITY, 0.0) * p.electricity_gwp,
           "water": amounts.get("market for water, deionised", 0.0) * GWP_OTHER["market for water, deionised"],
           "transport": sum(amounts.get(n, 0.0) * f for n, f in GWP_OTHER.items()
                            if "transport" in n) / p.lifetime,
           "materials": 0.0, "recycling credit": 0.0}
    for material, m in (material_inputs(totals) / p.lifetime).items():
        primary, secondary = p.gwp_material[material]
        fr, cr = _shares(material, p)
        if p.rule == "cut-off":
            out["materials"] += m * (fr * secondary + (1 - fr) * primary)
        else:
            out["materials"] += m * primary
            out["recycling credit"] -= m * cr * (primary - secondary)
    out["total"] = sum(out.values())
    return out


def scenarios(totals, recycled=(0, .25, .5, .75, 1), recycling=(0, .5, .9),
              lifetimes=(.5, 1, 2), rules=("cut-off", "end-of-life"), base=Params()):
    """MCI and screening GWP for every combination of the shared parameters."""
    rows = []
    for rule in rules:
        for fr in recycled:
            for cr in recycling:
                for life in lifetimes:
                    p = replace(base, recycled_content=fr, eol_recycling=cr, lifetime=life, rule=rule)
                    g = screening_gwp(totals, p)
                    rows.append({"rule": rule, "recycled content": fr, "EoL recycling": cr,
                                 "lifetime": life, "MCI": mci(totals, p),
                                 "GWP": g["total"], "GWP materials": g["materials"] + g["recycling credit"]})
    return pd.DataFrame(rows)


def levers(totals, base=Params()):
    """Screening GWP at the low and high end of each lever, other parameters at base."""
    cases = {
        "Equipment lifetime ×0.5 / ×2": (replace(base, lifetime=.5), replace(base, lifetime=2)),
        "Metal recycled content 0 / 100% (cut-off)": (replace(base, recycled_content=0),
                                                      replace(base, recycled_content=1)),
        "Metal EoL recycling 0 / 90% (end-of-life rule)": (replace(base, rule="end-of-life", eol_recycling=0),
                                                           replace(base, rule="end-of-life", eol_recycling=.9)),
        "Wind electricity GWP −25% / +25%": (replace(base, electricity_gwp=base.electricity_gwp * .75),
                                             replace(base, electricity_gwp=base.electricity_gwp * 1.25)),
    }
    rows = [{"lever": k, "low": screening_gwp(totals, a)["total"], "high": screening_gwp(totals, b)["total"]}
            for k, (a, b) in cases.items()]
    return pd.DataFrame(rows), screening_gwp(totals, base)["total"]
