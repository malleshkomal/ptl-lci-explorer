# Methods: circularity KPIs and the screening carbon footprint

This file explains how `make_circularity.py` and `src/lcitools/circularity.py` calculate each number in the README's circularity section. The worked numbers are for **1 kg of PtL fuel**. Liquid hydrogen follows the same steps; its results are in `results/circularity/kpis.csv`.

## 1. Scale the inventory

`run.py` solves the foreground system for 1 kg of product (**A · s = f**, see `model.py`). The scaling vector **s** says how much of each activity is needed, including each piece of equipment. For example, 1 kg of fuel needs 9.9 × 10⁻⁷ electrolysers, or one electrolyser per 1.01 million kg of fuel.

Each equipment material is multiplied by that share. The electrolyser contains 8,000 kg of stainless steel, so 8,000 × 9.9 × 10⁻⁷ = 7.9 g of stainless steel per kg of fuel. Over all equipment:

| Material class | g per kg fuel |
|---|---:|
| Stainless steel | 8.0 |
| Concrete | 6.0 |
| Steel (reinforcing, low-alloyed) | 5.2 |
| Other (catalyst oxides, KOH, zeolite, board, nitrogen, oil) | 0.5 |
| Aluminium | 0.007 |
| **Total** | **19.7** |

Concrete is given in m³. It is converted at **2,400 kg/m³**, a value taken from the dataset itself: the Fischer-Tropsch plant's 828,000 t of concrete waste divided by its 345,000 m³ of concrete.

## 2. Circularity KPIs

### Carbon loop

```
closure = CO₂ captured from air / CO₂ released when the fuel burns
        = 3.160 kg / (44/14) kg = 3.160 / 3.143 = 100.5%
```

Burning assumes a –CH₂– fuel (44/14 kg of CO₂ per kg), as in chart 4.

### End-of-life coverage

```
coverage = mass of end-of-life (waste) flows in the dataset / mass of material going in
```

It is calculated per material group (steel grades together, because the bulk iron waste covers both). For PtL fuel, 97.5% of the material mass has an end-of-life flow. For liquid hydrogen it is 22.4%: the liquefaction plant has no end-of-life flows, so 99% of its concrete and all of its copper have no end-of-life treatment.

### Material Circularity Indicator (MCI)

A simplified version of the Ellen MacArthur Foundation (2019) indicator:

```
M   = equipment material mass per kg of product
V   = virgin input       = M × (1 − recycled content)
W   = unrecovered waste  = M × (1 − end-of-life recycling)
LFI = (V + W) / (2M)                  linear flow index, 0 to 1
MCI = max(0, 1 − LFI × 0.9 / X)       X = lifetime relative to the dataset
```

Only metals (steel, stainless steel, aluminium, copper) can have recycled content or be recycled. Concrete and other materials always count as linear. Recycling-process losses are ignored.

- **As published** (no recycled content, no recycling, X = 1): V = W = M, LFI = 1, MCI = 1 − 0.9 = **0.10**.
- **Circular case** (100% recycled metals, 90% end-of-life recycling). Metals are 13.2 g and non-metals 6.5 g:
  - V = 6.5 g
  - W = 6.5 + 13.2 × 0.1 = 7.8 g
  - LFI = (6.5 + 7.8) / (2 × 19.7) = 0.36
  - MCI = 1 − 0.36 × 0.9 = **0.67**

## 3. Screening carbon footprint (GWP)

Each flow is multiplied by an emission factor. **These factors are illustrative screening values, not ecoinvent 3.9 results.** They are good enough to rank levers, but replace them with ecoinvent cut-off scores before quoting a footprint.

| Flow | Factor (kg CO₂e) |
|---|---|
| Wind electricity | 0.012 per kWh |
| Steel, primary / secondary | 2.3 / 0.6 per kg |
| Stainless steel, primary / secondary | 4.8 / 2.0 per kg |
| Aluminium, primary / secondary | 9.0 / 0.8 per kg |
| Copper, primary / secondary | 4.0 / 1.2 per kg |
| Concrete | 0.13 per kg |
| Other materials | 1.5 per kg |
| Deionised water | 0.0005 per kg |
| Transport by lorry / train | 0.15 / 0.05 per tkm |

Worked example, as published:

| Source | Calculation | kg CO₂e |
|---|---|---:|
| Electricity | 25.55 kWh × 0.012 | 0.307 |
| Stainless steel | 0.0080 kg × 4.8 | 0.038 |
| Steel | 0.0052 kg × 2.3 | 0.012 |
| Water, concrete, other, transport | | 0.004 |
| **Total** | | **0.361** |

Electricity is 85% of the total and equipment materials 14%. Hydrogen leakage and land occupation are not included.

## 4. Shared scenario parameters

The KPIs and the footprint use the same three parameters, so one change moves both:

| Parameter | Effect on the footprint | Effect on the MCI |
|---|---|---|
| Metal recycled content | Metals charged at the secondary factor (cut-off rule) | Lowers V |
| Metal end-of-life recycling | Credit of mass × rate × (primary − secondary) (end-of-life rule) | Lowers W |
| Equipment lifetime X | Equipment materials and transport per kg divided by X | 0.9 / X |

Worked lever results for PtL fuel:
- **Recycled content 0 → 100%:** steel 2.3 → 0.6 and stainless 4.8 → 2.0 saves 0.031 kg, **−9%**.
- **Lifetime × 2:** materials and transport fall from 0.052 to 0.026 kg, **−7%**. Lifetime × 0.5 doubles them, **+14%**.
- **End-of-life recycling 0 → 90%:** **−8%**.
- **Wind electricity factor ±25%:** 0.307 × 0.25 = 0.077 kg, **±21%**.

## 5. One recycling-credit rule at a time

Crediting recycled content at the input and recycling at end of life for the same material counts the same benefit twice. The model applies one rule per scenario:

- **Cut-off (100:0)**, matching ecoinvent cut-off: recycled content lowers the input burden; no end-of-life credit.
- **End-of-life (0:100)**, avoided burden: all metal is charged as primary; recycling earns a credit.

`tests/test_circularity.py` checks that end-of-life recycling has no effect under cut-off, and recycled content has no effect under the end-of-life rule.

## 6. Scenario grid

Every combination is run for each product: 5 recycled-content levels (0, 25, 50, 75, 100%) × 3 recycling rates (0, 50, 90%) × 3 lifetimes (× 0.5, 1, 2) × 2 rules = **90 scenarios**. The chart plots the 45 cut-off scenarios per product. All are in `results/circularity/scenarios.csv`.

Two results come from the grid:
- The most circular scenario is also the lowest-carbon one for both products, so there is no trade-off at the best end.
- In 7% of scenario pairs, the more circular scenario has the higher footprint. The MCI counts kilograms, not carbon: a kilogram of concrete counts as much as a kilogram of stainless steel.

## Output files

| File | Contents |
|---|---|
| `results/circularity/kpis.csv` | The KPI table in the README |
| `results/circularity/eol_coverage.csv` | Material in vs end-of-life flows, per material group |
| `results/circularity/scenarios.csv` | MCI and GWP for every scenario |
| `results/circularity/levers.csv` | GWP at the low and high end of each lever |
| `results/charts/09_circularity_vs_gwp.png` | The chart |
