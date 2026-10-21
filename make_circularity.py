"""Link circularity KPIs with a screening carbon footprint for both products.

Writes tables to results/circularity/ and the chart
results/charts/09_circularity_vs_gwp.png.

Usage: python make_circularity.py
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
warnings.filterwarnings("ignore", module="openpyxl")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from lcitools.circularity import (Params, carbon_loop, eol_coverage, levers,  # noqa: E402
                                  material_inputs, mci, scenarios, screening_gwp)
from lcitools.model import inventory  # noqa: E402
from lcitools.reader import dataset_paths, read_brightway_csv  # noqa: E402
from make_charts import (AQUA, BLUE, FU, FU_NAME, GRID, MUTED, ORANGE, TEXT,  # noqa: E402
                         TEXT_2, figure, save, style)

ROOT = Path(__file__).parent
OUT = ROOT / "results" / "circularity"
SCREENING = "Screening GWP uses illustrative emission factors, not ecoinvent 3.9 results."


def kpi_rows(fu, totals):
    g = screening_gwp(totals)
    cov = eol_coverage(totals)
    rows = [
        ("Screening GWP, linear reference", g["total"], "kg CO2e/kg"),
        ("  of which electricity", g["electricity"] / g["total"], "share"),
        ("  of which equipment materials", g["materials"] / g["total"], "share"),
        ("Equipment materials", material_inputs(totals).sum() * 1000, "g/kg"),
        ("Material mass with an end-of-life flow", cov["end-of-life kg"].sum() / cov["input kg"].sum(), "share"),
        ("MCI, linear reference", mci(totals), "0-1"),
        ("MCI, 100% recycled metals and 90% EoL recycling", mci(totals, Params(recycled_content=1, eol_recycling=.9)), "0-1"),
    ]
    if fu == "ptl":
        rows.insert(0, ("Carbon loop closure (CO2 captured / released)", carbon_loop(totals)["closure"], "share"))
    return [{"product": FU_NAME[fu], "kpi": k, "value": v, "unit": u} for k, v, u in rows]


def pareto(df):
    """Scenarios no other scenario beats on both MCI (higher) and GWP (lower)."""
    d = df.sort_values(["MCI", "GWP"], ascending=[False, True])
    best, keep = np.inf, []
    for i, r in d.iterrows():
        if r["GWP"] < best - 1e-12:
            keep.append(i)
            best = r["GWP"]
    return df.loc[keep].sort_values("MCI")


def chart(results):
    fig = figure(13, 9.4, "Circularity and carbon footprint move together, but electricity sets the level",
                 "Each dot is one scenario of metal recycled content, end-of-life recycling and equipment lifetime "
                 "(cut-off rule).\n" + SCREENING)
    colors = {0.5: ORANGE, 1: BLUE, 2: AQUA}
    for i, (fu, (_, sc, lv, base)) in enumerate(results.items()):
        sc = sc[sc["rule"] == "cut-off"]
        ax = fig.add_axes([0.07 + i * 0.49, 0.52, 0.4, 0.3])
        style(ax, "both")
        for life, c in colors.items():
            s = sc[sc["lifetime"] == life]
            ax.scatter(s["MCI"], s["GWP"], s=26, color=c, label=f"lifetime ×{life:g}", zorder=3,
                       edgecolor="white", linewidth=0.6)
        front = pareto(sc)
        note = ("No trade-off: the most circular scenario\nis also the lowest-carbon one" if len(front) == 1
                else f"{len(front)} scenarios on the trade-off front")
        ax.text(0.98, 0.5, note, transform=ax.transAxes, ha="right", fontsize=9, color=TEXT_2)
        ref = sc[(sc["recycled content"] == 0) & (sc["EoL recycling"] == 0) & (sc["lifetime"] == 1)].iloc[0]
        ax.annotate("as published,\nall primary metal", (ref["MCI"], ref["GWP"]), xytext=(18, 14),
                    textcoords="offset points", fontsize=9, color=TEXT_2,
                    arrowprops=dict(arrowstyle="-", color=TEXT_2, linewidth=0.8))
        ax.set_xlim(-0.02, 1)
        ax.set_xlabel("Material Circularity Indicator of the equipment (0 linear, 1 circular)", fontsize=9.5, color=TEXT_2)
        ax.set_ylabel("kg CO₂e per kg", fontsize=9.5, color=TEXT_2)
        ax.set_title(f"{FU_NAME[fu]}", loc="left", fontsize=11.5, color=TEXT, fontweight="bold")
        if i == 0:
            ax.legend(frameon=False, fontsize=9, loc="upper right")

        ax2 = fig.add_axes([0.3 + i * 0.49, 0.1, 0.17, 0.28])
        style(ax2)
        lv = lv.iloc[::-1]
        y = np.arange(len(lv))
        lo, hi = (lv["low"] - base) / base * 100, (lv["high"] - base) / base * 100
        for yi, a, b, name in zip(y, lo, hi, lv["lever"]):
            c = MUTED if "electricity" in name else BLUE
            ax2.barh(yi, b - a, left=a, color=c, height=0.55)
            for v in {round(a), round(b)} - {0}:
                ax2.text(v + (1.5 if v > 0 else -1.5), yi, f"{v:+d}%", ha="left" if v > 0 else "right",
                         va="center", fontsize=9, color=TEXT)
        ax2.axvline(0, color=TEXT, linewidth=0.8)
        ax2.set_xlim(-45, 45)
        ax2.set_yticks(y, lv["lever"], fontsize=9)
        ax2.xaxis.set_major_formatter(lambda v, _: f"{v:+.0f}%")
        ax2.set_title(f"Change in GWP per lever, {FU_NAME[fu] if fu == 'ptl' else FU_NAME[fu].lower()} (base {base:.2f} kg)",
                      loc="left", fontsize=10.5, color=TEXT, fontweight="bold", x=-1.05)
    fig.lines.append(Line2D([0.02, 0.98], [0.45, 0.45], color=GRID, transform=fig.transFigure, linewidth=1))
    save(fig, "09_circularity_vs_gwp.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    _, acts, excs = read_brightway_csv(dataset_paths(ROOT / "data/original/power-to-liquid")["csv"])
    results, kpis, covs, scs, lvs = {}, [], [], [], []
    for fu, activity in FU.items():
        totals, _ = inventory(acts, excs, {activity: 1.0})
        sc = scenarios(totals)
        lv, base = levers(totals)
        results[fu] = (totals, sc, lv, base)
        kpis += kpi_rows(fu, totals)
        covs.append(eol_coverage(totals).reset_index(names="material").assign(product=FU_NAME[fu]))
        scs.append(sc.assign(product=FU_NAME[fu]))
        lvs.append(lv.assign(product=FU_NAME[fu], base=base))

    pd.DataFrame(kpis).to_csv(OUT / "kpis.csv", index=False)
    pd.concat(covs).to_csv(OUT / "eol_coverage.csv", index=False)
    pd.concat(scs).to_csv(OUT / "scenarios.csv", index=False)
    pd.concat(lvs).to_csv(OUT / "levers.csv", index=False)

    for r in kpis:
        v = f"{r['value']:.1%}" if r["unit"] == "share" else f"{r['value']:.3f} {r['unit']}"
        print(f"{r['product']:<16} {r['kpi']:<52} {v}")
    print()
    for c in covs:
        print(c[["product", "material", "input kg", "end-of-life kg", "coverage", "route"]].to_string(index=False), "\n")
    chart(results)
    print(f"Wrote tables to {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
