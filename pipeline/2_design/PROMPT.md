# Module 2 — Design (HTML)

## Goal
Convert `plan.json` into beautiful, html2pptx-safe HTML slides at `run/<run_id>/slides/slide_NN.html`.

## Inputs
- `run/<run_id>/plan.json` (from Module 1)
- `pipeline/2_design/DESIGN_RULES.md` — full constraint list (READ THIS FIRST)
- `converter/CAPABILITIES.md` — what survives PPTX conversion

## Process
1. Read `DESIGN_RULES.md` end to end. The constraints are not negotiable — they are hard limits enforced by the html2pptx converter.
2. For each slide in `plan.json`:
   - Pick a layout pattern matching `slide.layout`. See `pipeline/2_design/templates/` for working examples.
   - Write `run/<run_id>/slides/slide_NN.html` (NN = 01, 02, ...) — one HTML per slide, self-contained.
   - Inline all CSS in `<style>` block (file:// CSS links work but are fragile — inline is safer).
   - Use ONLY: text content from plan.json, image refs to files that actually exist (logos, charts), external `<img src="icons/*.svg">` for icons.
3. After writing each slide, run a self-check: open the HTML in Playwright, screenshot it, look for: overflow past 1280×720, text smaller than 18px, raw text outside `<p>/<li>/<span>`. Fix and re-write before moving to next slide.
4. Update `state.json`: append all slide paths to `artifacts`, set `current_module = "3_refine"`.

## Hard constraints (from html2pptx实测)
- body MUST be `width:1280px; height:720px; position:relative;` (or 960×720 for 4:3)
- Font: ONLY `"Helvetica Neue", Helvetica, Arial, "PingFang SC", "Microsoft YaHei", sans-serif`
- Background color: use full-bleed `<div class="bg">`, never `body { background: gradient }`
- Icons: external `<img src="icons/*.svg">` files, NEVER inline `<svg>`
- Layout: prefer `border` for separation, NEVER `box-shadow` or `backdrop-filter`
- All text MUST be wrapped in `<p>/<li>/<span>` — no bare text nodes
- Lists: use `<ul>/<ol>/<li>`, no custom bullets
- Tables: use `<table>` (converts to native editable PPTX TABLE)

## Success criteria
- One HTML file per slide in plan.json, named `slide_NN.html`.
- Each file passes the self-check screenshot (no overflow, no <18px text).
- `node converter/html2pptx_cli.js --html_dir run/<run_id>/slides --output /tmp/probe.pptx --validate` exits 0.

## Failure handling
- If a layout has too much content for one slide, split into two slides and update plan.json accordingly.
- If you can't find an image referenced in plan.json, use a labeled placeholder div (gray background, source path text).
