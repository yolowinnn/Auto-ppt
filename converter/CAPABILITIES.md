# html2pptx 能力/边界清单

> 基于 2026-05-26 在 slides/slide_01..04.html 上的实测（fork 自 PPTAgent v2，含 SVGAnimatedString 补丁）。
> 是给 Module 2 (Claude HTML 设计) 的 prompt 约束依据。

## ✅ 完美保留（原生可编辑）

| 项 | 证据 |
|---|---|
| 中文/英文混排文本 | slide_01-04 全部文本零截图，字符无乱码 |
| 字号 / 字色 / 加粗 / 斜体 | 32px → 24pt、44px → 33pt 等都精确匹配；颜色 hex 精确 |
| 字体跨平台自适应 | CDP 自动给 CJK 段落标 `PingFang SC`，Latin 标 `Helvetica Neue` |
| 绝对/相对/flex/grid 定位 | KPI 三列 flex (3.91in × 3) 精确还原；padding 64px → 0.67in |
| HTML `<table>` | 转成原生 PPTX TABLE shape，整行可在 PPT 里编辑单元格 |
| `<img>` 引用 PNG/JPG | logo_industrialmind.png 按 object-fit:contain 缩放，48px → 0.5in |
| 单色背景的 `<div>` | 转成带填充色的 AUTO_SHAPE（border-radius 也保留） |
| 圆角 pill / 卡片 | border-radius 保留，背景色保留 |
| 边框 (border / border-top) | 转成 AUTO_SHAPE 的描边 |
| `<ul>/<ol>/<li>` 列表 | 转成多段落 text frame |

## ⚠️ 简化或退化（不报错，但视觉损失）

| 项 | 实际行为 |
|---|---|
| `linear-gradient` / `radial-gradient` 背景 | **退化为单色**（取渐变中第一个 color stop） |
| 整页 `body { background: gradient }` | **完全丢失** — slide 背景空白 |
| `box-shadow` | 不渲染 |
| `backdrop-filter` (毛玻璃) | 不渲染 |
| `rgba()` 半透明 | 可能转为不透明 fallback |
| `transform` / `rotate` | 未测试，预期不支持 |

## ❌ 触发截图回退（变成 PICTURE）

| 项 | 实际行为 |
|---|---|
| Inline `<svg>` icon (小) | 单元素截图 → PNG 嵌入 → 视觉保留但不可编辑 |
| Inline `<svg>` (大尺寸 / 复杂路径) | **可能直接丢失**（slide_03 hero 图标未出现在输出） |

## 🐛 已修补的 bug

- `el.className.includes` 对 SVG 元素的 `SVGAnimatedString` 不安全 → 用 `?.includes?.(` 全局替换（12 处）

## 🔧 替代写法（workaround patterns）

实测过的等效替换。Module 2 的 prompt 应当内置这些 mapping：

### 1. 整页 gradient 背景 → 全屏 div + 纯色

❌ 不要：
```css
body { background: linear-gradient(135deg, #0f766e, #064e3b); }
```

✅ 改成：
```html
<body>
  <div class="bg"></div>             <!-- 全屏纯色 -->
  <div class="bg-accent"></div>      <!-- 装饰色条 -->
  <div class="slide"> ...内容... </div>
</body>
```
```css
.bg { position:absolute; left:0; top:0; width:1280px; height:720px; background-color:#064e3b; }
.bg-accent { position:absolute; left:0; top:0; width:6px; height:720px; background-color:#10b981; }
```

实测：两个 div 都进入 PPTX 作为带 fill 色的 AUTO_SHAPE，slide 不再空白。

### 2. Inline `<svg>` 图标 → 外部 .svg 文件 + `<img>`

❌ 不要：
```html
<svg viewBox="0 0 24 24"><path d="..."/></svg>
```

✅ 改成（同时切实把图标存到磁盘）：
```html
<img class="icon" src="icons/check.svg" alt="check">
```

实测：`<img src="icons/*.svg">` 走原生 PICTURE 路径，hero/badge 三个图标全部进入 PPTX，尺寸精确。inline SVG 走的是单元素截图路径，hero 大尺寸 SVG 会丢。

### 3. box-shadow 营造层次 → border 营造层次

❌ 不要：
```css
.card { box-shadow: 0 8px 32px rgba(0,0,0,0.28); }
```

✅ 改成：
```css
.card { border: 1px solid #047857; border-radius: 16px; }
.card-accent { position:absolute; top:0; left:0; width:100%; height:4px; background:#10b981; border-radius:16px 16px 0 0; }
```

### 4. backdrop-filter 毛玻璃 → 半暗色块

直接放弃毛玻璃，用 `background-color: rgba(...)` 或更深一档的纯色。

### 5. gradient 的 pill / badge → 纯色 + border

❌ 不要：
```css
.badge { background: linear-gradient(135deg, #34d399, #10b981); }
```

✅ 改成：
```css
.badge { background-color: #064e3b; border: 1px solid #34d399; color: #6ee7b7; }
```

## Module 2 prompt 硬约束（最终）

写给 Claude 的设计 prompt 必须包含：

1. **背景**: 用 `background-color: <hex>;`，禁 gradient。需要色块就单独画 div。
2. **阴影/毛玻璃**: 禁 `box-shadow` / `backdrop-filter`。用 `border` 营造层次。
3. **图标**: 优先 `<img src="icons/xxx.svg">` 或 `<img src="icons/xxx.png">`（外部文件引用，会被原生当 PICTURE 处理）；避免 inline `<svg>`。
4. **表格**: 始终用 `<table>`（会变原生可编辑 TABLE），不要用 div 模拟。
5. **字体**: 只列跨平台字体（Helvetica Neue / Arial / PingFang SC / Microsoft YaHei / sans-serif）。
6. **正文字号**: ≥ 18px。
7. **裸文本**: 全部包 `<p>/<li>/<span>`。
8. **body 尺寸**: 16:9 必须 `width:1280px; height:720px`。

## 测试命令

```bash
cd /Users/jiaweili/main_folder/projects/pending_project/Auto-ppt/converter
node html2pptx_cli.js --html_dir slides --output out/demo.pptx --layout 16:9
python3 verify_pptx.py out/demo.pptx
open out/demo.pptx
```
