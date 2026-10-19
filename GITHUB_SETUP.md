# Publishing this repository on GitHub

## Repository name
`ptl-lci-charts`

## Description (paste into the "Description" field)
Seven charts explaining the life cycle inventory of power-to-liquid jet fuel and liquid hydrogen from wind power and direct air capture (data: Nair et al., DLR).

## Topics (add under the ⚙️ next to "About")
```
life-cycle-assessment  lca  power-to-liquid  sustainable-aviation-fuel  hydrogen
direct-air-capture  data-visualization  charts  infographics  open-data
```

## Upload in the browser
1. On github.com, click **+ → New repository**.
2. Enter the name and description above and choose **Public**. Leave "Add a README",
   ".gitignore" and "license" unticked: this folder already has a README and a LICENSE.
3. Click **Create repository**, then **uploading an existing file**.
4. Open this folder, select **everything inside it** (the `charts`, `chart-data` and
   `docs` folders, README.md, LICENSE), and drag it onto the page.
5. Click **Commit changes**. The README shows all seven charts on the repository page.

## Turn on the interactive page (GitHub Pages)
After uploading:
1. In the repository, open **Settings → Pages**.
2. Set **Source** to *Deploy from a branch*, **Branch** to `main`, **folder** to `/docs`, and click **Save**.
3. After 1–2 minutes the page is live at `https://YOUR-USERNAME.github.io/ptl-lci-charts/`.
4. In `README.md`, replace `YOUR-USERNAME` with your username, and paste the address into the
   repository's **Website** field (⚙️ next to "About").

## Upload from the command line
```bash
cd ptl-lci-charts
git init -b main
git add .
git commit -m "Power-to-liquid LCI charts"
git remote add origin https://github.com/YOUR-USERNAME/ptl-lci-charts.git
git push -u origin main
```

You can delete this file after publishing.
