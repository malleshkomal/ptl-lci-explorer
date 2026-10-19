"""Build docs/index.html: the interactive findings page as one self-contained file.

The page body is the same as the online dashboard. Here a small `dash` shim
serves the tables in results/dashboard_data/ (embedded in the file) instead of
the dashboard runtime, so the page works on GitHub Pages or opened locally.

Usage: python build_site.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent
PAGE = ROOT / "site" / "page.html"
DATA = ROOT / "results" / "dashboard_data"
OUT = ROOT / "docs" / "index.html"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Power-to-Liquid LCI Findings</title>
<meta name="description" content="Interactive findings from the published life cycle inventory of power-to-liquid jet fuel and liquid hydrogen (Nair et al., DLR).">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<style>
:root {
  color-scheme: light;
  --font-anthropic-sans: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-anthropic-serif: "Source Serif 4", Georgia, "Times New Roman", serif;
  --color-bg: #f7f7f5; --color-panel: #ffffff; --color-fg: #16181d; --color-fg-muted: #5b5e66;
  --color-border-line: #e3e3df; --color-ok: #1b7f4b; --color-warn: #a35f00; --color-bad: #c8322f;
  --cds-chart-muted: #b4b3ac; --cds-chart-grid: #e8e7e3; --cds-chart-axis: #c9c8c2; --cds-chart-reference: #8b8a84;
  --cds-surface-popover: #ffffff; --cds-border: #dcdcd7; --cds-shadow-popover: 0 6px 20px rgba(20, 22, 28, .12);
  --cds-text-secondary: #5b5e66;
  --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a; --s4: #eda100; --s5: #e87ba4; --s6: #008300; --s7: #6250d6; --s8: #e34948;
  --cds-radius: 10px; --cds-pad-xs: 6px; --cds-pad-sm: 10px; --cds-pad-md: 14px; --cds-pad-lg: 20px; --cds-pad-xl: 28px;
  --cds-gap-xs: 6px; --cds-gap-sm: 10px; --cds-gap-md: 16px; --cds-gap-lg: 24px; --cds-gap-xl: 40px;
  --cds-font-size-caption: 13px; --cds-font-size-body: 15px; --cds-font-size-heading: 17px; --cds-font-size-title: 24px;
  --cds-font-weight-medium: 600; --cds-dur-slow: 600ms; --cds-ease-out: cubic-bezier(.2, .7, .2, 1);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --color-bg: #141518; --color-panel: #1d1f23; --color-fg: #eeeeec; --color-fg-muted: #a6a8ae;
    --color-border-line: #2f3237; --color-ok: #4cc38a; --color-warn: #e6a23c; --color-bad: #f0706b;
    --cds-chart-muted: #5d6067; --cds-chart-grid: #2a2d32; --cds-chart-axis: #3a3d43; --cds-chart-reference: #8d9097;
    --cds-surface-popover: #24272c; --cds-border: #3a3d43; --cds-shadow-popover: 0 6px 20px rgba(0, 0, 0, .45);
    --cds-text-secondary: #a6a8ae;
    --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500; --s5: #d55181; --s6: #008300; --s7: #9085e9; --s8: #e66767;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --color-bg: #141518; --color-panel: #1d1f23; --color-fg: #eeeeec; --color-fg-muted: #a6a8ae;
  --color-border-line: #2f3237; --color-ok: #4cc38a; --color-warn: #e6a23c; --color-bad: #f0706b;
  --cds-chart-muted: #5d6067; --cds-chart-grid: #2a2d32; --cds-chart-axis: #3a3d43; --cds-chart-reference: #8d9097;
  --cds-surface-popover: #24272c; --cds-border: #3a3d43; --cds-shadow-popover: 0 6px 20px rgba(0, 0, 0, .45);
  --cds-text-secondary: #a6a8ae;
  --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500; --s5: #d55181; --s6: #008300; --s7: #9085e9; --s8: #e66767;
}
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--color-bg); color: var(--color-fg); font-family: var(--font-anthropic-sans); font-size: var(--cds-font-size-body); }
#dash-root { padding-block: 40px 56px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
@media (min-width: 900px) { #dash-root { padding-left: max(40px, env(safe-area-inset-left, 0px)); padding-right: max(40px, env(safe-area-inset-right, 0px)); } }
.dash-skeleton { color: transparent !important; background: var(--color-border-line); border-radius: 6px; min-width: 2.5em; display: inline-block; }
.pl-chart.dash-skeleton { display: block; }
.site-foot { max-width: 72rem; margin: 48px auto 0; font-size: var(--cds-font-size-caption); color: var(--color-fg-muted); line-height: 1.55; }
.site-foot a { color: inherit; }
</style>
</head>
<body>
<main id="dash-root">
"""

SHIM = """<script>
// Stand-in for the dashboard runtime: serves the embedded tables and the page's calculations.
window.dash = (() => {
  const raw = __DATA__;
  const calcs = {};
  const cache = {};
  const listeners = [];
  let started = false;
  const data = (id) => {
    if (id in raw) return { status: 'ok', data: raw[id], refreshing: false, meta: [] };
    if (id in calcs) {
      if (!(id in cache)) {
        const c = calcs[id];
        cache[id] = c.fn(...c.inputs.map((i) => data(i).data));
      }
      return { status: 'ok', data: cache[id], refreshing: false, meta: [] };
    }
    return { status: 'missing', data: [], refreshing: false, meta: [] };
  };
  const run = () => listeners.forEach((fn) => { try { fn(); } catch (e) { console.error(e); } });
  document.addEventListener('DOMContentLoaded', () => { started = true; run(); });
  let t;
  window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(run, 150); });
  return {
    data,
    calc: (id, opts) => { calcs[id] = opts; },
    loader: () => {},
    onData: (fn) => { listeners.push(fn); if (started) fn(); },
    colors: ['var(--s1)', 'var(--s2)', 'var(--s3)', 'var(--s4)', 'var(--s5)', 'var(--s6)', 'var(--s7)', 'var(--s8)'],
    setLink: (id) => { try { history.replaceState(null, '', '#' + id); } catch (e) { /* file:// */ } },
    params: () => ({}), setParams: () => {}, resetParams: () => {}, refresh: () => {},
  };
})();
</script>
"""

FOOT = """
<footer class="site-foot">
  Data: supplementary life cycle inventory of Nair, Chougule, Gomez Trillos and Brand-Daniels,
  <a href="https://www.sciencedirect.com/science/article/pii/S0959652625014702">Journal of Cleaner Production</a>,
  licensed <a href="https://creativecommons.org/licenses/by-nc/4.0/">CC BY-NC 4.0</a>.
  Analysis and page by co-author Komal Chougule. Built with lcitools (build_site.py).
</footer>
</main>
</body>
</html>
"""


def main():
    tables = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(DATA.glob("*.json"))}
    blob = json.dumps(tables, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = PAGE.read_text(encoding="utf-8")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(HEAD + SHIM.replace("__DATA__", blob) + page + FOOT, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
