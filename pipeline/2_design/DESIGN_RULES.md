# Module 2 Design Rules — what html2pptx actually preserves

> This is the constraint cheat-sheet for writing slide HTML.
> Authoritative source: `converter/CAPABILITIES.md` (实测数据).

## Always allowed ✓

- Text in `<p>/<li>/<span>` with font-size, color, font-weight, font-style, line-height, letter-spacing
- Font families from cross-platform whitelist:
  - `"Helvetica Neue", Helvetica, Arial, sans-serif` (Latin)
  - `"PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif` (CJK)
- `<div>` with `background-color`, `border`, `border-radius`, `padding`, `margin`
- Absolute / relative / flex / grid positioning
- `<table>` with `<thead>/<tbody>/<tr>/<th>/<td>` (becomes native editable PPTX TABLE)
- `<img src="...">` referencing PNG / JPG / SVG **files** (becomes native PICTURE)
- `<ul>/<ol>/<li>` (becomes paragraphed text)
- Pill / badge with `border-radius: 999px` + solid `background-color`

## Forbidden ✗ (silently dropped or distorted)

- `background: linear-gradient(...)` or `radial-gradient(...)` — degrades to single color
- `body { background: ... }` for anything but `background-color: <hex>;`
- `box-shadow` — not rendered
- `backdrop-filter` — not rendered
- `transform: rotate/scale/translate` — untested, assume broken
- `rgba()` with alpha < 1.0 — may convert to opaque fallback
- Inline `<svg>` — small ones screenshot OK, large ones may be dropped entirely
- Web fonts (`@font-face`, Google Fonts) — falls back to system font

## Workaround mapping

| Want | Use instead |
|---|---|
| Full-page dark/colored background | Full-bleed `<div class="bg">` with `background-color: <hex>` |
| Gradient accent | Two adjacent `<div>` blocks, each with solid color |
| Card with elevation (shadow) | `border: 1px solid <hex>; border-radius: 16px;` + optional thin colored `<div class="card-accent">` strip on top |
| Inline SVG icon | Save as `run/<run_id>/icons/<name>.svg`, reference via `<img src="icons/<name>.svg">` |
| Glass / blur background | Solid darker color, no blur |
| Gradient text | Single hex color (pick the dominant one) |

## Page setup boilerplate (16:9)

```html
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  width: 1280px; height: 720px;
  position: relative;
  font-family: "Helvetica Neue", Helvetica, Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #1a1a1a; background: #ffffff; overflow: hidden;
}
.slide { position: absolute; left: 0; top: 0; width: 1280px; height: 720px; padding: 56px 64px; }
</style>
</head>
<body>
  <div class="slide">
    <!-- content here -->
  </div>
</body>
</html>
```

## Style presets

Three brand styles map directly to user's existing decks. Pick one based on `plan.json.style_hint`.

### `internal` (TaomoAI weekly tracking — white)
- bg: `#ffffff`
- accent: `#00a86b` (green divider line under title)
- title: 32px bold `#1a1a1a`
- subtitle / body: 18-20px `#1f2937` / `#6b7280`
- footer: 12px `#9ca3af`, "Copyright @ TaomoAI 2026. Business Confidential"

### `pitch` (IndustrialMind — dark hero)
- bg cover: full-bleed `<div>` `#064e3b`
- bg interior: `#ffffff`
- accent: `#10b981` (left vertical stripe 6px)
- title: 40px bold `#ffffff` on dark, `#1a1a1a` on white
- footer: 12px `#6ee7b7` on dark, "© 2026 IndustrialMind AI"

### `report` (assessment / 100-份测试)
- bg: `#ffffff`
- accent: bold `#10b981` chapter title bar
- callout box: `#f3f4f6` bg, `#374151` text
- KPI card: white bg, `border-top: 4px solid` (status color: `#00a86b` good / `#f59e0b` warn / `#ef4444` bad)
- footer: thin green full-width bar
