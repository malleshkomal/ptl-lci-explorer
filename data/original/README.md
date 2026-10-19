# Original dataset (unmodified)

These files are the supplementary data of:

> Nair, R. R., Chougule, K. M., Gomez Trillos, J. C., & Brand-Daniels, U.
> *A generalized schema to publish and share life cycle inventories (LCI):
> Exemplary case of an aviation fuel supply chain.* Journal of Cleaner Production.
> https://www.sciencedirect.com/science/article/pii/S0959652625014702
> (supplementary file `mmc1`, archive `supplementary_data_20250102.7z`)

Authors' affiliation: German Aerospace Center (DLR), Oldenburg.
Funding: ALICIA Project, German Aerospace Center.

## Licence

The authors released the dataset under **Creative Commons Attribution-NonCommercial
4.0 International (CC BY-NC 4.0)**, as declared in `power-to-liquid/metadata/metadata.xlsx`.
Full terms: https://creativecommons.org/licenses/by-nc/4.0/

- You may share and adapt it, with attribution to the authors above.
- You may **not** use it for commercial purposes.

The files were extracted from the 7z archive and are otherwise unchanged.

## Contents

| File | What it is |
|---|---|
| `metadata_template.xlsx` | Blank LCIS2024 metadata template proposed in the paper |
| `power-to-liquid/dataset/power-to-liquid.csv` / `.xlsx` | Foreground inventory (Brightway 2.4.3 export, 14 activities, 80 exchanges) |
| `power-to-liquid/dataset/power-to-liquid_properties.csv` | Dataset properties: schema version, counts, dependencies |
| `power-to-liquid/metadata/metadata.xlsx` | Filled-in metadata (scope, assumptions, authors, background database, licence) |
| `power-to-liquid/network/power-to-liquid.graphml` | Supply-chain network as a graph |
| `power-to-liquid/environment.yml` | The authors' conda environment (Windows) |

The archive also contains an empty `power-to-liquid/dependencies/` folder. Git does not store empty folders, so it is not in this repository.
