# 资源预生成（Asset Generation）— 可选增强环节

> 灵感来自业内实践：先用风格参考定义 **style spec**，再用图像模型**批量生成**风格统一的素材（图标、配图），做 PPT 时直接引用。
> 在 Auto-PPT 里这是 Module 2（设计）之前的可选前置步骤：plan 确定后，先把这一页页需要的素材生成好，HTML 再 `<img>` 引用。

## 何时启用

`state.json.config.generate_assets: true` 时启用。默认 false（纯文本/数据型 PPT 不需要）。

## 两类素材（按实测优先级）

### 1. 图标集（icon set）— ⭐ 强烈推荐，效果好

实战结论：图像模型生成图标**风格还原度高、批量省时**，远好于网上找素材。

流程：
1. **定义 style spec**：喂 3-5 张风格参考图 → 让模型总结出一套规范（线条粗细、圆角、配色、是否描边、视角），写到 `run/<id>/assets/icon_style.md`。
2. **批量生成**：按 plan 里需要的图标清单（如「裁线机 / 剥线机 / 压接机 / 端子」），逐个按 style spec 生成 → 存 `run/<id>/assets/icons/<name>.png`（或 .svg）。
3. HTML 用 `<img src="assets/icons/<name>.png">` 引用（**外部文件**，html2pptx 走原生 PICTURE，安全）。

约束：**禁 inline `<svg>`**（html2pptx 会炸/丢，见 CAPABILITIES.md）；图标统一尺寸、统一留白，便于网格排布。

### 2. 背景图 / 配图 — ⚠️ 谨慎，效果一般

实战结论：AI 背景图**死板、缺创意**，好背景太依赖创意，不强求。
- 优先用纯色 + 装饰色块（见 DESIGN_RULES）而非 AI 背景。
- 确需配图时：用图像模型生成到 `run/<id>/assets/bg/`，object-fit:cover 铺底 + 遮罩层压暗保证文字可读；生成后**人工过一眼**再用。

## 生成工具（按可得性选其一）

- ChatGPT image / DALL·E、即梦（Jimeng）、Codex agent 批量模式、或本地 ComfyUI text2image
- 关键不是用哪个模型，而是**先锁 style spec 再批量**，保证整套 PPT 视觉一致

## 与现有 pipeline 的衔接

```
Module 1 (plan) → [可选] Asset Generation (按 plan 生成 assets/) → Module 2 (HTML 引用 assets) → ... → Module 5 (转 PPTX)
```

未实现时的降级：Module 2 直接用已有 logo + 手写小图标 SVG 文件（当前 demo 的做法）。
