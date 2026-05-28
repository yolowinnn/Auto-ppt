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

## ⚠️ PPTX 渲染陷阱（CJK 实测，2026-05-28 踩坑）

浏览器渲染 ≠ PowerPoint 渲染。html2pptx 按浏览器测得的盒宽/盒高写死文本框，但 PowerPoint 用 PingFang SC 渲染中文**更宽更高**，且文本框有 ~19px 默认内边距 → 紧凑布局会**换行错位 / 溢出 / 文字撞线**。必须主动留余量：

1. **单行标题/footer 必须给富余宽度**。只加 `white-space: nowrap` 没用（盒宽已写死，框内仍折行）。也不要靠 `padding-right`（会被当文本框内边距，文字区不变宽）。正确做法：给元素**显式 `width`**，比中文实际宽度多留 ~1 倍。
   - 例：`.title { width: 560px; }`（中文实际约 260px）。flex 里再加 `flex-shrink: 0`。
2. **固定高度的指标框**（深色大数字块等）：给足 `height` + `align-items: center`，别让多行文字贴着框底，否则 PPTX 里会溢出框外。
3. **表格表头禁止 `thead { background-color }` + 白字**。单元格背景色会被剥离 → 白字白底变隐形。改用：表头**深色/petrol 文字 + `border-bottom` 下划线**，无填充。
4. **右对齐多行文字禁止用 `<br>`**。`<br>` + `display:block` span 会让 html2pptx 生成重叠文本框（重复/错位）。改用多个独立 `<p>` 块，各自 `text-align: right; white-space: nowrap;`。
5. **改完必须用 LibreOffice 回渲染验证**，不能只看 HTML 截图：
   ```bash
   soffice --headless --convert-to pdf --outdir out final.pptx
   pdftoppm -png -r 100 out/final.pdf out/slide   # 然后逐张肉眼检查
   ```
   （LibreOffice 预览里中文略毛糙是它没装 PingFang 用了替代字体，不是 PPTX 本身问题；Mac PowerPoint 打开会用 PingFang SC 正常显示。要看的是换行/溢出/隐形文字。）

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
