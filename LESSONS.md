# Auto-PPT 实战经验库（LESSONS）

> 这是从**真实做 PPT 遇到的问题**里蒸馏出来的经验，按时间累积。
> 维护方式：`INSIGHTS_INBOX.md` 收集原始问题 → 每周 cron job（routine `auto-ppt-weekly-distill`）蒸馏成这里的条目 → 稳定后晋升进 `pipeline/2_design/DESIGN_RULES.md` 或 `converter/CAPABILITIES.md`。
> 每条格式：`## [日期] 标题` + 现象 / 根因 / 修法 / 已晋升到哪。

---

## [2026-05-28] CJK 在 PPTX 里比浏览器更宽更高 → 紧凑布局溢出

**现象**（Siemens 导线裁剥改善 PPT）：HTML 截图完美，但转 PPTX 后标题换行撞绿线、表格表头消失、深色数字框文字溢出、footer 断行、右对齐说明文字重叠。

**根因**：html2pptx 按**浏览器渲染宽度**把文本框尺寸写死，但 PowerPoint 用 **PingFang SC** 渲染中文更宽更高，且文本框有 ~19px 默认内边距 → 浏览器里刚好的布局，到 PPTX 就溢出/折行。

**修法**（已全部验证）：
1. 单行标题/footer 给**显式富余宽度**（`width: 560px`，实际文字才 ~260px）。`white-space:nowrap` 和 `padding-right` 都没用——前者框宽已写死仍折行，后者被当文本框内边距。
2. 固定高度的指标框给足 `height` + `align-items:center`，别让多行文字贴框底。
3. 表头禁止「`thead{background-color}` + 白字」——背景色被剥离→白字白底隐形。改用 petrol 深色文字 + `border-bottom` 下划线。
4. 右对齐多行禁止 `<br>`——会让 html2pptx 生成重叠文本框。改用多个独立 `<p>` 块各自右对齐。
5. **改完必须 LibreOffice 回渲染肉眼验证**（`soffice --convert-to pdf` + `pdftoppm -png`），不能只信 HTML 截图。预览里中文发虚是 LibreOffice 没装 PingFang 用了替代字，不是 PPTX 问题。

**已晋升**：`pipeline/2_design/DESIGN_RULES.md` → "⚠️ PPTX 渲染陷阱" 段。

---

## [2026-05-28] 方法论：Style-Spec → Skill → 批量生成保持风格一致

**来源**：业内文章（用 ChatGPT image / 即梦 / Codex Agent 模式批量生成 PPT 素材）。

**可迁移到 Auto-PPT 的 4 条**：
1. **风格规范先行**：先喂一批风格参考 → AI 定义出一套 style spec → 写进 Skill。这正是我们 `DESIGN_RULES.md` + `style_hint` 预设在做的事，验证了方向对。
2. **素材预生成应成为独立环节**：文章用图像模型批量生成书法字、地标 icon。我们 pipeline 目前只 `<img>` 引用、不生成。应加一个 **资源生成步骤**：按 plan 需要的图标/配图，用图像模型按锁定的 style spec 批量生成到 `run/<id>/assets/`，再被 HTML 引用。见 `pipeline/2_design/ASSET_GENERATION.md`。
3. **图标好用、AI 背景图不好用**：文章实测 icon 风格还原度高、批量生成省时；背景图死板、创意不足。结论——Auto-PPT 优先建/生成**风格统一的图标集**，慎用 AI 背景图。和我们已验证的「外部 icon 文件可用、inline SVG 会炸」完全吻合。
4. **「一句正文 + 一句加粗放大关键信息」是高冲击页型**（发布会产品页/数据页）。应加一个 `hero_statement` 布局：大号加粗关键数字/短语 + 一行正文，视觉冲击强、信息结构简单、易批量。

**待晋升**：第 2、4 条做成 pipeline 文档/新布局后，更新 README 路线图。
