# Charts and numbers

## Is it a chart?

- One number: write it in a sentence with its comparison ("12% lower than last quarter").
- A few exact numbers: a table with `tabular-nums`.
- Change over time: line chart. Categories compared: bar chart, horizontal when labels are long. Part of a whole with 2 to 5 parts: one stacked bar (a pie only for 2 or 3 parts). Distribution: histogram or dot plot. Relationship between two measures: scatter.
- If the reader needs exact values more than the shape, use a table.

## Pick the tool

- **Hand-written SVG** for static charts with up to about 20 marks. Zero bytes, crisp, themeable with CSS variables like the diagrams in `references/explain.md`.
- **Chart.js 4.5.1** (bundled, MIT, 208,522 bytes, about 209 kB inlined) when the reader needs tooltips, a toggleable legend, or many points. Reference `<script src="vendor/chart.umd.min.js"></script>` and run `scripts/inline.py`.
- Nothing else without asking: every other library adds weight and must be vendored first.

## Color by job

- **Categorical:** up to 6 distinct hues; group the rest into "Other". Keep a series the same color across every chart on the page.
- **Sequential:** one hue from light to dark for ordered magnitude.
- **Diverging:** two hues around a meaningful midpoint (zero, target, average).
- **Status:** good, warning, bad, always with a text label or icon as well.
- Marks need 3:1 contrast against the background in both themes. Text is never set in a series color; labels use the ink color with a colored key beside them.
- Emphasis: color the series that carries the point with the accent and mute the rest.

## Chart.js with the page's tokens

```html
<figure>
  <div class="chart-box" style="position: relative; height: 320px"><canvas id="c1" aria-label="Weekly orders, last 12 weeks" role="img"></canvas></div>
  <figcaption>Orders doubled after the checkout fix in week 7.</figcaption>
</figure>
<script src="vendor/chart.umd.min.js"></script>
<script>
const token = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
let chart;
function draw() {
  chart?.destroy();
  Chart.defaults.color = token("--muted");
  Chart.defaults.borderColor = token("--rule");
  Chart.defaults.font.family = token("--font-body");
  chart = new Chart(document.getElementById("c1"), {
    type: "line",
    data: { labels: [/* ... */], datasets: [{ label: "Orders", data: [/* ... */], borderColor: token("--accent"), backgroundColor: token("--accent"), pointRadius: 0, borderWidth: 2 }] },
    options: { animation: false, maintainAspectRatio: false, plugins: { legend: { display: false } }, interaction: { mode: "index", intersect: false } }
  });
}
draw();
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
</script>
```

- `animation: false` keeps screenshots deterministic and respects reduced motion.
- Give the canvas a sized container and `maintainAspectRatio: false`, or it collapses on narrow screens.
- Redraw on a theme change so axis and grid colors follow the tokens.

## Labels and access

- The caption states what the chart shows, not what it is ("Orders doubled after week 7", not "Orders chart").
- Label lines directly at their end when there are few; drop the legend then.
- Offer exact values for important charts: a `<details>` with the data table below the chart.
- Avoid dual axes, truncated bar baselines, 3D, and rainbow palettes.
