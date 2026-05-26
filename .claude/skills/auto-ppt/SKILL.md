---
name: auto-ppt
description: Generate PPTX decks in TaomoAI / IndustrialMind house style (internal weekly-tracking, external pitch, or assessment report). Use when the user asks for a Siemens / Taomo / IndustrialMind presentation, weekly report, pitch deck, or evaluation slide deck — especially when source materials live in a local folder and the user wants consistent corporate styling.
---

# auto-ppt — TaomoAI / IndustrialMind 固化 PPT 工作流

**目的**:把 `Data/` 下三类范本风格固化下来,从用户提供的素材+指令自动生成风格一致的 .pptx。

## When to use this skill

Invoke when the user asks for any of:
- Siemens / TaomoAI 周报、tracking、评估报告
- IndustrialMind 对外 pitch deck、产品介绍、客户汇报
- "做一份 PPT"、"生成幻灯片"、"出一份汇报材料",并且语境涉及上述公司或工业 AI 主题
- 用户指向了 `Data/`(或类似文件夹)作为素材源

If the request is for a non-corporate, generic deck — do NOT use this skill, write a one-off instead.

## Three fixed styles (固化风格)

| key | 用途 | 视觉特征 |
|---|---|---|
| `internal` | 内部周报、tracking、数据汇总 | 白底,左上角粗体标题+绿色细线分隔,右上角 logo,底部 "Copyright @ TaomoAI 2024. Business Confidential" |
| `pitch` | 对外 pitch、产品介绍 | 深绿封面/尾页,白底正文,绿色标题,图标网格、对比表、Before/After,底部 "© 2026 IndustrialMind AI \| All Rights Reserved." |
| `report` | 综合评估/100份测试报告 | 封面双侧色条+INDUSTRIALMIND.AI 字标,正文绿色章节标题+灰色 callout box+KPI 卡片+底部绿色全宽条 |

Color & font specifics live in [theme.py](theme.py). Do not redefine them in prompts — adjust the file if the user wants a permanent change.

## Workflow (two-step, ALWAYS)

### Step 1 — Draft a spec, get user confirmation

1. Read user's source materials. Use the `Read` tool for PDFs in `Data/` (use `pages:` for big PDFs), Markdown notes, CSV data, etc.
2. Decide which of the three styles fits. If unclear, ask the user once.
3. Draft `output/<topic>_spec.json` following the schema in [examples/](examples/). Pick layouts from the supported list (see "Supported layouts" below). Each slide is one object.
4. Show the user the slide outline (just titles + layout types, not full JSON) and ask for confirmation or edits before rendering.

### Step 2 — Render

```
python3 .claude/skills/auto-ppt/render.py output/<topic>_spec.json output/<topic>.pptx
```

Tell the user the output path. If `python-pptx` is missing, run `pip3 install python-pptx` first.

## Supported layouts (v1)

All three styles support these layouts; the style file decides the look. See [builder.py](builder.py) for exact field names per layout.

**Text layouts**
- `title` — cover slide. Style-dependent: split-image / full-color / side-bars. In `internal` style, the right half image resolves via: spec `image` field → `assets/cover_bg.png` (industrial cityscape from the Siemens template) → dark green panel with logo fallback. So if `cover_bg.png` is present you don't need to specify an image in the spec.
- `toc` — agenda / content list
- `section` — section divider (e.g. "BACK UP")
- `bullets` — title + bullet list. Items are strings or `{text, sub:[..], bold?}`. Renders as ONE multi-paragraph textbox with hanging indent — long Chinese wraps cleanly.
- `two_col` — left & right columns; each can be `{type: text|bullets|image|table, heading?, ...}`
- `thanks` — closing slide; style-dependent

**Visual / data layouts** (use these to make it credible — pure text decks look weak)
- `kpi_cards` — title + headline + row of N (3–6) metric cards. Each `{value, label, status: good|warn|bad|info}`. Optional `caption`.
- `metrics_strip` — title + headline + row of hero metric tiles + optional `body` bullet block + optional `caption`. Use when a metric needs sub-text (`{value, label, sub}`).
- `chart_bar` — title + headline + native bar chart + optional `caption`. Spec: `{categories:[..], series:[{name, values:[..]}], horizontal?: bool}`. Edits in PowerPoint as a real chart.
- `image_with_callouts` — title + headline + left image + right bullet callouts. Image gets a thin border. Use for screenshots / generated visualizations from the actual product.
- `image_grid` — title + N images (1–6) in grid; each with caption
- `data_table` — title + headline + table; `highlight_col` can color the value cell green/amber/red based on % thresholds
- `comparison` — Before vs After two-column comparison with ✗ / ✓ rows (plain layout)
- `comparison_cards` — Manus-style card comparison: two rounded-corner cards side by side, each with a colored header bar and bullet rows with ✗/✓ icons. Optional `footer_quote` pill at the bottom. Spec: `{title, before:{label, items:[]}, after:{label, items:[]}, footer_quote?}`. Use this instead of `comparison` for executive-facing slides — it looks significantly more polished.
- `three_line_table` — 三线表 (no vertical rules, thick top/bottom border, thin header-separator). Spec: `{title, headline?, columns:[{text, width}], rows:[[...]], caption?, row_height?}`. `width` is a 0–1 fraction of total content width. `row_height` (default `0.44`, unit=inches) controls vertical spacing — increase to `0.75–0.85` for milestone-style tables with longer text.
- `flow` — simple horizontal flow of N boxes connected by arrows

If a needed layout doesn't exist, add it: implement `add_<name>_slide` in [builder.py](builder.py), document the spec fields, then add a sample to [examples/](examples/).

## Spec format

A spec is JSON:

```json
{
  "style": "internal",
  "meta": {
    "title": "Siemens AI Tracking",
    "subtitle": "TaomoAI",
    "date": "2026-04-27",
    "footer": "Copyright @ TaomoAI 2026. Business Confidential"
  },
  "slides": [
    {"layout": "title", "title": "...", "subtitle": "...", "image": "assets/cover.jpg"},
    {"layout": "toc", "title": "CONTENT", "items": ["...", "..."]},
    {"layout": "bullets", "title": "...", "subtitle": "...", "items": ["..."]},
    ...
  ]
}
```

Image paths can be absolute, or relative to the spec file's directory. If a referenced image is missing, the renderer leaves a labeled placeholder rectangle (does not crash).

## Source material handling

- `Data/*.pdf` — read with `Read` tool, `pages:` parameter for files >10 pages. Look at the visual structure not just text.
- Charts the user wants reproduced: extract the data points if visible, encode as a `data_table` or `kpi_cards` slide. Don't try to embed the original chart image unless you exported it first.
- If the user gives you raw numbers/CSV, prefer `data_table` or `kpi_cards` over re-rendering charts (v1 has no chart layout — Step 2 todo).

## Improving the skill (when the user asks to "make it better")

1. **Add a layout** — implement in [builder.py](builder.py), wire into the dispatch in [render.py](render.py), add example spec.
2. **Tweak a style** — edit the relevant file in [styles/](styles/). Change colors in [theme.py](theme.py) only if it should affect ALL styles.
3. **Add a real logo** — drop PNG at `assets/logo_industrialmind.png` (and `assets/logo_taomo.png` for the report style). Renderer auto-detects and uses it; without it, draws a text wordmark. The `report` style header prefers `logo_taomo.png` over `logo_industrialmind.png`.
4. **Add an example** — every new layout/style variation should ship with a spec in [examples/](examples/) so future-you (or future-Claude) can copy it.

See [README.md](README.md) for the maintenance contract.

## Quality bar — what makes a deck good enough for an executive audience

These rules came from real corrections. Re-read them before drafting the spec.

### Real data, never round-number guesses

Specs going to a director / 工艺总监 / customer-facing audience MUST cite numbers from the actual repo or dataset. Source-of-truth checklist before writing the spec:

1. **Open the actual files**, don't extrapolate. For Siemens-wirelayout-style projects:
   - `dataset/<work-order>/*_导线线长计算(Vendor).xlsx` — count rows = wire counts
   - `demo/output/wire_length_list.csv` — actual wires processed
   - `demo/output/summary.json` — route distribution, counts
   - `demo/output/annotation.svg` — convert to PNG and embed as visualization
   - `IMapps/apps/IM3D/backend/long_routing_engine.py` — line numbers for cited functions
   - `IMapps/apps/IM3D/backend/long_routing_rules.json` — count families/rules
2. **Cite paths in the deck footer or caption** — proves the number is real.
3. **If a number is uncertain, say so on the slide**, don't paper over it. Example: "Vendor 准确性基线尚未建立 — 不向客户承诺数字". Lying to a process director loses the project.
4. **If you're delegating data extraction to an Explore agent, instruct it to flag missing data clearly**. E.g. ask "is there comparison/diff data? if not, say no" — never let the agent silently return inferred numbers.

### Visual mix > pure text

A 4-content-slide executive deck should have:
- ≥ 1 slide with a real visualization (`image_with_callouts` using a generated artifact)
- ≥ 1 slide with quantitative tiles (`kpi_cards` or `metrics_strip`)
- ≥ 1 slide with a chart OR table (`chart_bar` / `data_table`)
- ≤ 1 slide that is purely bullets

A pure-text deck signals "we have nothing to show". For technical projects, generate a visualization from the system itself (SVG annotation, screenshot, dashboard) and embed it.

### Layout safety rules (enforced by builder, but spec-side too)

- Do NOT cram more than ~6 bullets into a `bullets` slide; split into `two_col` if needed.
- Do NOT exceed 6 cards in `kpi_cards` (5 is the sweet spot at 16:9).
- For long Chinese strings, prefer `metrics_strip` over `kpi_cards` (it has a `sub` line so the value/label can stay short).
- After rendering, run `python3 .claude/skills/auto-ppt/verify_layout.py <out.pptx>` — flags shapes that fall off the slide canvas.

### Two-step workflow (still required)

Even with great content, ALWAYS show the user the slide-by-slide outline (titles + layout types + 1-line content summary) BEFORE rendering. They want control. The exception is when the user explicitly says "just do it" and you have high confidence.

## What NOT to do

- Don't render the spec without showing the outline first — the user wants control.
- Don't invent new colors / fonts in spec files. Style is defined ONCE in theme/styles.
- Don't write content into `assets/` — that folder is for logos/cover images only.
- Don't put PowerPoint XML or oddly-formatted text into spec values; if you need formatting beyond bold-on-first-word, add a layout.
- Don't fabricate accuracy / performance / scale numbers. If the data isn't in the repo, say so on the slide and propose a baseline task in milestones.
- Don't ship a deck that's all bullets — add at least one chart/image/table/metric layout.
