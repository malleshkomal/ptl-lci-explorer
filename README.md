# Power-to-Liquid LCI in Charts

Seven charts that explain what it takes to make **synthetic jet fuel** and **liquid hydrogen** from wind power, water and CO₂ captured from the air.

The charts are drawn from the published life cycle inventory (LCI) of:

> Nair, R. R., Chougule, K. M., Gomez Trillos, J. C., & Brand-Daniels, U.
> **A generalized schema to publish and share life cycle inventories (LCI): Exemplary case of an aviation fuel supply chain.**
> *Journal of Cleaner Production.* [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0959652625014702)

> This is an independent project, not affiliated with the authors or with the German Aerospace Center (DLR). The underlying data is the authors' and is licensed CC BY-NC 4.0.

**[Open the interactive version](https://YOUR-USERNAME.github.io/ptl-lci-charts/)**: the same findings with hover details, a product switch and a searchable data table. It's hosted from [`docs/index.html`](docs/index.html), one file you can also download and open in any browser.

## Key numbers

| Per 1 kg of product | PtL fuel | Liquid hydrogen |
|---|---:|---:|
| Wind electricity | 25.6 kWh | 65.2 kWh |
| of which electrolysis | 95% | 88% |
| Deionised water | 4.75 kg | 11.3 kg |
| CO₂ captured from the air | 3.16 kg | – |
| Energy kept in the product | 47% | 51% |

---

### 1. How 1 kg of fuel is made

3.16 kg of CO₂ and 0.43 kg of hydrogen go in, and 1 kg of fuel comes out. The other 2.59 kg leaves as water, as the chemistry predicts:
CO₂ + H₂ → CO + H₂O, then CO + 2 H₂ → –CH₂– + H₂O.

![How 1 kg of PtL fuel is made](charts/01_mass_flow_sankey.png)

### 2. Electrolysis uses almost all the electricity

Splitting water into hydrogen takes 24.3 of the 25.6 kWh for fuel and 57.6 of the 65.2 kWh for liquid hydrogen. Liquefying hydrogen at −253 °C adds 6.9 kWh.

![Electricity by process step](charts/02_electricity_by_step.png)

### 3. About half of the electricity ends up in the product

The rest is lost as heat along the way. This chart uses standard heating values (hydrogen 120 MJ/kg, kerosene-like fuel 43 MJ/kg), which are not part of the dataset.

![Energy kept in the product](charts/03_energy_kept.png)

### 4. Hydrogen use and the carbon loop

Two thirds of the hydrogen goes straight into syngas. One third is used to strip oxygen from CO₂. The CO₂ captured from the air is within 0.5% of the CO₂ the fuel releases when burned.

![Hydrogen and carbon](charts/04_hydrogen_and_carbon.png)

### 5. Materials are measured in grams

Besides electricity and water, each kg of product needs only grams of other materials. Most of it is steel for plants and equipment.

![Material inputs](charts/05_materials.png)

### 6. Equipment lasts a long time

Each plant is shared by everything it makes over its life. One electrolyser makes about 433 t of hydrogen, and one Fischer-Tropsch plant about 149 million t of fuel.

![Equipment lifetime output](charts/06_equipment_lifetime.png)

### 7. Inside the dataset

There are 14 activities and 80 exchanges. Most of the lines describe how equipment is built. The process steps themselves have only 2–3 lines each.

![Dataset anatomy](charts/07_dataset_anatomy.png)

---

## The numbers behind each chart

Every chart has a matching CSV file in [`chart-data/`](chart-data/), so you can check the values or redraw the chart in Excel or any other tool.

| Chart | Data file |
|---|---|
| 1. Mass flow | `01_mass_flows.csv` |
| 2. Electricity by step | `02_electricity_by_step.csv` |
| 3. Energy kept | `03_energy_kept.csv` |
| 4. Hydrogen and carbon | `04_hydrogen_and_carbon.csv` |
| 5. Materials | `05_materials.csv` |
| 6. Equipment lifetime | `06_equipment_lifetime.csv` |
| 7. Dataset anatomy | `07_dataset_anatomy.csv` |

## How the charts were made

The published inventory was scaled to 1 kg of each product. To do this, the foreground system of 14 activities was solved as a set of linear equations, and every input was added up along the supply chain. The charts were drawn with Python and matplotlib.

All values are **inventory quantities** (kWh, kg, tonnes), **not climate impact scores**. Turning them into kg CO₂-equivalent would need the ecoinvent database, which is licensed separately.

## Licence

The charts and CSV files are derived from the authors' dataset and are shared under the same licence, [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). You may share and adapt them with credit to the original authors, but not for commercial use.
