# Publishing this repository on GitHub

## Repository name
`ptl-lci-explorer`

## Description (paste into the "Description" field)
Python tools to read, validate and scale a published LCIS2024 life cycle inventory: power-to-liquid aviation fuel and liquid hydrogen from wind power and direct air capture (Nair et al., DLR).

## Topics (add under the ⚙️ next to "About")
```
life-cycle-assessment  lca  life-cycle-inventory  power-to-liquid  sustainable-aviation-fuel
hydrogen  direct-air-capture  brightway  ecoinvent  python  data-visualization  open-data
```

## Upload in the browser (no tools needed)
1. On github.com, click **+ → New repository**.
2. Enter the name and description above, choose **Public**, and leave
   "Add a README", ".gitignore" and "license" **unticked**.
3. Click **Create repository**, then **uploading an existing file**.
4. Open this folder on your computer, select **everything inside it**, and drag it
   onto the page. The folders `data`, `src`, `tests` and `results` must be included.
5. Click **Commit changes**. The README and charts then appear on the repository page.

Hidden files such as `.gitignore` may not be dragged in. The project works without them.

## Upload from the command line
```bash
cd ptl-lci-explorer
git init -b main
git add .
git commit -m "Power-to-liquid LCI explorer"
git remote add origin https://github.com/YOUR-USERNAME/ptl-lci-explorer.git
git push -u origin main
```

## Turn on the interactive findings page (GitHub Pages)
After uploading:
1. In the repository, open **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to *Deploy from a branch*,
   **Branch** to `main`, and **folder** to `/docs`. Click **Save**.
3. Wait 1–2 minutes and refresh. GitHub shows the address:
   `https://YOUR-USERNAME.github.io/ptl-lci-explorer/`
4. In `README.md`, replace `YOUR-USERNAME` with your GitHub username. You can
   edit it on GitHub with the ✏️ pencil. Also paste the address into the
   repository's **Website** field (⚙️ next to "About").

## Before you publish
- The dataset in `data/original/` belongs to the paper's authors and is licensed
  **CC BY-NC 4.0**. The README credits them; keep that credit, and don't use the
  data commercially.
- The code is MIT-licensed under your GitHub username. Edit `LICENSE` to change that.

You can delete this file after publishing.
