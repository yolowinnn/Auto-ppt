# PPTAgent 源码研读笔记 — 借鉴清单

> 仓库版本：本地 clone 于 `research/PPTAgent/`
> 重点关注 `deeppresenter/`（新产品线，是 README 真正驱动 CLI 的代码）
> `pptagent/` 是旧的"模板替换法"实现，仅保留 PPTEval 和模板槽位生成两块还值得参考
> CLAUDE.md 已明确："treat `deeppresenter` as the primary product surface"

---

## 一、整体架构与你 5 模块的对应关系

| 你的模块 | PPTAgent 对应位置 | 关键文件 / 函数 |
|---|---|---|
| 0. CLI / 入口 | `pptagent` console script → `deeppresenter.cli.main` | `deeppresenter/cli/commands.py:310` (`generate()`)<br>`deeppresenter/main.py:44` (`AgentLoop.run`) |
| 1. 读文档 + 大纲 | Planner（可选）+ Research 双 Agent | `deeppresenter/agents/planner.py`<br>`deeppresenter/agents/research.py`<br>`deeppresenter/tools/any2markdown.py`（MinerU + MarkItDown）<br>`deeppresenter/tools/search.py`（SerpAPI/Tavily + Playwright）<br>`deeppresenter/utils/mineru_api.py` |
| 2. HTML 设计 | Design Agent + global.css 母版策略 | `deeppresenter/agents/design.py`<br>`deeppresenter/roles/Design.yaml`（关键 prompt） |
| 3. 多轮自评 + 修正 | 工具内置回写 + heavy_reflect 多模态校验 | `deeppresenter/tools/reflect.py:28`（`inspect_slide`）<br>`deeppresenter/main.py:58` 的 `heavy_reflect`<br>`deeppresenter/agents/agent.py:191` (`action`) + `:250` (`execute`)（toolcall 循环） |
| 4. 自主循环 | 单 Agent 内 while True，每轮 finalize 才能退出 | `deeppresenter/agents/design.py:8`<br>`deeppresenter/agents/agent.py:356`（`compact_history` 即超长上下文折叠）<br>`deeppresenter/utils/constants.py:23`（`CONTEXT_LENGTH_LIMIT=200_000`） |
| 5. HTML → PPTX | **Node + Playwright + PptxGenJS 的「语义解析 + 局部光栅化」混合管线** | `deeppresenter/html2pptx/html2pptx.js`（2987 行）<br>`deeppresenter/html2pptx/html2pptx_cli.js`<br>`deeppresenter/utils/webview.py`（Python 侧 subprocess 封装） |

整个 pipeline 形态（`AgentLoop.run`）：

```
[Planner 可选] → outline.json
       ↓
   Research → manuscript.md（含图）
       ↓
   ┌────分叉────┐
   │            │
 PPTAgent     Design
 路径         路径（推荐）
   │            │
 .pptx     slide_XX.html → html2pptx.js → .pptx
                                ↘ fallback → playwright print → .pdf
```

注意：`main.py:196-218` 始终调一次 PDF fallback，目的是 html2pptx 失败时不至于颗粒无收，PDF 作为兜底交付物。

---

## 二、Module 1（读文档 + 做大纲）—— 可借鉴

### 2.1 文档 → Markdown：`any2markdown` 工具
- 文件：`deeppresenter/tools/any2markdown.py:38`
- **核心策略**：PDF 优先走 MinerU（在线 API 或自部署），非 PDF 走微软 `MarkItDown`
- 关键路由代码：

```python
# any2markdown.py:57
if file_path.lower().endswith(".pdf") and (MINERU_API_KEY or MINERU_API_URL):
    if MINERU_API_KEY:
        await parse_pdf_online(file_path, str(output_path), MINERU_API_KEY)
    elif MINERU_API_URL:
        await parse_pdf_offline(file_path, str(output_path), MINERU_API_URL)
else:
    conver_result = MarkItDown().convert_local(file_path, keep_data_uris=True)
    markdown = parse_base64_images(conver_result.text_content, output_path / "images")
```

- MinerU 在线 API 调用细节在 `deeppresenter/utils/mineru_api.py:32`（POST → batch → 轮询 → 下载 zip → 解压）
- **副作用**：所有 base64 inline image 自动落盘到 `images/`，并把链接重写成绝对路径 → 这是后续 HTML 直接 `<img src="/abs/path">` 的前提

### 2.2 网页抓取：`fetch_url` 工具
- 文件：`deeppresenter/tools/search.py:232`
- 流程：先用 httpx HEAD 探一下 → 真要拉就 Playwright + bypass CSP + UA 伪装 → trafilatura 提取正文 → markdownify
- 关键点：搜索后端 SerpAPI（Google）和 Tavily 二选一（`search.py:102` `elif len(TAVILY_KEYS)`）

### 2.3 大纲数据结构
- 文件：`deeppresenter/utils/outline.py`（很短）和 `deeppresenter/roles/Planner.yaml:11`
- 结构（这是 Planner agent finalize 时写入的 JSON）：

```json
{
  "slides": [
    {"index": 1, "title": "≤15 字", "context": "≤100 字描述这页要呈现什么"}
  ]
}
```

- **流程亮点**（`planner.py:28`）：第一轮生成 outline 之后进入 `yield outcome` → 等用户 feedback。CLI 端 `commands.py:543` (`_edit_outline`) 用 `Rich Table` 展示并交互式修订。这正是你想要的"用户介入"机会。

### 2.4 Research Agent 系统 prompt 的精华（`deeppresenter/roles/Research.yaml`）
- 整个文档/网页/搜索接入是通过工具暴露给 Research，不在 prompt 里写死流程
- 强约束在风格指南上（信息美学、金字塔原则、图必须落到本地绝对路径、禁外链）

### 2.5 你已有 vs. 还差什么
- 你 `.claude/skills/auto-ppt/` 已经从 JSON spec → PPTX，相当于跳过了 Module 1/2/3/4 直接进入 Module 5（且只用 python-pptx + 固定模板）
- 直接可抄：
  - `any2markdown.py` 整套 PDF/docx → md 的策略选择
  - `Planner.yaml` 中"大纲 JSON schema + 用户介入"的设计
  - `inspect_manuscript` (`reflect.py:65`) 这种轻量校验函数模式：统计页数、检测图片 alt、外链警告——可以直接抄进你的 skill 做质量预检

---

## 三、Module 2（HTML 设计）—— 重点

### 3.1 关键事实：Design Agent 自己迭代调工具，不是一次性 N 张
- `deeppresenter/agents/design.py` 全文只有 21 行：

```python
class Design(Agent):
    async def loop(self, req: InputRequest, markdown_file: str):
        (self.workspace / "slides").mkdir(exist_ok=True)
        while True:
            agent_message = await self.action(...)
            yield agent_message
            outcome = await self.execute(self.chat_history[-1].tool_calls)
            if isinstance(outcome, list):
                for item in outcome:
                    yield item
            else:
                break   # outcome 是 str 表示调到 finalize
        yield outcome
```

- 即 **逐张生成 → 每张紧跟 `inspect_slide` 校验 → 通过才进下一张**
- 强制行为在 `roles/Design.yaml:15`：

```
3. 基于设计方案和文稿内容逐页生成独立的高质量HTML文件...
   - 每次仅生成一张幻灯片，并立即调用 inspect_slide 对其进行质量检查；
     若 inspect_slide 返回任何问题反馈，须完成全部修正并重新通过检查，
     直至该页达到可用标准，方可进入下一页生成流程
```

### 3.2 HTML 必须遵守的硬约束（关键！决定了 html2pptx 能不能转回去）

从 `roles/Design.yaml:21-29`（直接贴 zh 段）：

```
1. <body> 采用固定尺寸（16:9=1280x720、4:3=960x720、A1=2244x3178...）
   严格控制边界、其他元素采用相对定位防止溢出
   正文与底部应保持足够的间距；
   字号不小于 18px

2. 文本须被包裹在 <p>, <li>, <span> 等元素内，禁止裸文本；
   列表必须使用 <ul>/<ol>，禁止使用自定义 bullet

3. 行内元素禁止 margin/border/shadow，装饰性样式；
   背景图 url(...) 仅应用于 <div>
   仅用跨平台安全的字体（禁用网络字体资源和平台特定字体）
   禁止网页特有的设计（如单元格文本背景色、交互式样式等）

4. 完整显示的图片/表格：固定尺寸 + object-fit: contain
   背景/装饰图：object-fit: cover + 可叠遮罩层
```

**这些不是 prompt 的修辞，是 html2pptx.js 真实存在的限制条件**（见第五章）。例如"裸文本被禁"是因为 html2pptx 用 `<p>/<li>/<span>` 这些 tag 名来判断元素类型。

### 3.3 多张并发（subagent 模式）
- 配置开关：`config.yaml.example` 里的 `multiagent_mode`
- 当开启时 Design Agent 会被注入 `delegate_subagent` 工具（`main.py:73-78`）
- 触发规则（`constants.py:107` `MA_RRESENTER_PROMPT`）：

```
Use delegate_subagent when the manuscript contains 3 or more slides...
Do not use delegate_subagent when the manuscript contains fewer than 3 slides;
generate standalone HTML files page by page... immediately call inspect_slide
```

- **设计思想**：单 Agent 先产出 `global.css`（充当"母版"）+ delegation file（每张页面的局部 spec），然后 fan-out 给 SubAgent 并发渲染。子 Agent 上下文为空，全靠 context_file 自洽。这就是"并发出图 + 全局风格统一"的最佳方案。

### 3.4 配色/字体怎么控制？
- **不在 prompt 里写死配色**，而是要求第一步先产出 `slides/global.css`，由 LLM 根据文稿主题/受众自定
- 字体严格限定"跨平台安全字体"，避免转 PPTX 后回退
- 兜底：`html2pptx.js:735` 默认字体就是 `Microsoft YaHei`（适合中文）

---

## 四、Module 3 + 4（自评 & 循环）—— 重点

### 4.1 两套截然不同的"反思" 机制

#### A. 运行时自反思（在 generation loop 内）
- 工具：`deeppresenter/tools/reflect.py:28` 的 `inspect_slide`
- 流程：

```python
# reflect.py:43
await convert_html_to_pptx(html_path, aspect_ratio=aspect_ratio)
# ↑ 故意 validate-only 模式（不写 pptx），让 html2pptx 抛出所有验证错误回给 LLM

if REFLECTIVE_DESIGN:    # heavy_reflect=True 且 design_agent 是多模态
    # 把 HTML 用 Playwright print 成 PDF → 转 JPG → 作为图片回传给 LLM
    ...
    return ImageContent(type="image", data=base64_data, mimeType="image/jpeg")
else:
    return "This slide is valid."
```

- **两种返回值**：
  - 非 reflective：仅靠 html2pptx 的文本错误（overflow、image not found、字号离边距太近...）做修正
  - reflective：把渲染图回传 → 让多模态 LLM 自己看，自己反馈
- 控制开关：`config.yaml` 里的 `heavy_reflect: true` + design_agent 必须是多模态模型（gemini/claude/gpt 这种）

#### B. 离线评估（PPTEval，生成完再打分）
- 老 `pptagent/ppteval/` 子模块，仍可用
- 三维度评分（5 分制），各维度的 prompt 全在 `pptagent/prompts/ppteval/*.txt`：

| 维度 | prompt 文件 | 评判依据 |
|---|---|---|
| **content** | `ppteval_content.txt` | 文案清晰度、结构、图文配合（基于 VLM 描述） |
| **style** (vision) | `ppteval_style.txt` | 配色、装饰元素、视觉吸引力（基于 VLM 描述） |
| **logic** (coherence) | `ppteval_coherence.txt` | 整体叙事结构、背景信息完整度（基于全 deck 文本） |

- 实际打分流程（`pptagent/ppteval/ppteval.py:54`）：
  1. 用 `vision_model` 分别生成 style/content 的「描述」
  2. 用 `language_model` 喂这些描述 + scoring prompt → 返回 `{"reason": "...", "score": int}`
- 评分 schema（`pptagent/ppteval/typings.py:47`）：

```python
class SlideEvals(BaseModel):
    page: int
    content: float = 0.0
    style: float = 0.0
    constraints: list[ConstraintEvalResult] | None = None

class Evals(BaseModel):
    constraint: float = 0.0       # 来自 DataPoint.verify() 的硬约束（页数、宽高比、语言）
    constraint_vlm: float = 0.0
    content: float = 0.0
    style: float = 0.0
```

- 你应该看看 `pptagent/ppteval/score_exp.py:38` `score_workspace` 函数——这就是 batch eval 的标准入口

### 4.2 自主循环的几个关键阀门
- **finalize 才能退出**：`deeppresenter/tools/task.py:58`。LLM 必须调 `finalize(outcome=...)`，且会按 agent_name 做格式校验（Planner 必须 .json、Research 必须 .md、Design 必须包含 slide_*.html 的目录）
- **超长上下文自动 fold**：`agents/agent.py:356` `compact_history`。当 context_length > context_window 触发，调用 LLM 总结当前 chat，保留头尾，中间塞个 summary。默认 5 折，总 200K tokens
- **预算预警**：`agents/agent.py:325-336`，到 50% / 80% / 100% 分别插入提示消息让 LLM "感受到压力"
- **MAX_TOOLCALL_PER_TURN=7**（`constants.py:16`），防止 LLM 一口气并行调 30 个工具炸了 token

### 4.3 多 Agent 之间是怎么通信的？
- **不是**典型的 message passing。`AgentLoop.run` 是顺序调用，前一个 Agent 的 `finalize` 输出（file path）就是下一个 Agent 的 input
- Planner → outline.json → Research → manuscript.md → Design → slides/ 目录 → html2pptx
- 中间产物全落盘 `intermediate_output.json`（`main.py:226`）
- **思考**：你的 3+4 循环本质上是 Design 自己跟自己玩，不需要多 Agent。借用这套设计：把 Manus 视觉反馈封装为一个 MCP tool（类似 `inspect_slide` reflective 模式返回 ImageContent），Claude design agent 一调就拿到图，立刻在下一轮 chat 里修

### 4.4 用什么 LLM、几轮？
- `config.yaml.example` 默认：
  - research_agent: `anthropic/claude-sonnet-4.5`（OpenRouter）
  - design_agent: `google/gemini-3-pro-preview`
  - long_context_model: `glm-4.5`（智谱）
- 轮数没有硬上限——退出条件就是 finalize 被调或 context 爆掉
- 单 agent max_turns 默认 None，subagent 是 `MAX_SUBAGENT_TURNS=10`

---

## 五、Module 5（HTML → PPTX）—— 最关键

### 5.1 决定性结论：**混合方案**（语义解析为主 + 选择性光栅化兜底）

直接证据：`html2pptx.js:413-537`（`rasterizeGradients` 函数末段处理元素的部分）。

| 元素类型 | 处理方式 | 证据行号 |
|---|---|---|
| `<p>/<h1-6>`（普通文本） | **原生 `addText`** | 691 |
| `<ul>/<ol>`（列表） | **原生 `addText(items, listOptions)`**（PptxGenJS 列表格式） | 627 |
| `<table>` | **原生 `addTable(rows, ...)`** | 643 |
| 形状/带背景的 `<div>` | **原生 `addShape` 矩形 + 内嵌文本** | 560-608 |
| 普通 `<img>`（无 object-fit/border-radius/filter/shadow） | **原生 `addImage(path=...)`** | 549-556 |
| `<img>` 带 object-fit / border-radius / filter / box-shadow | **Playwright screenshot 单个元素 → PNG → addImage** | 446-459（条件 `shouldRender`） |
| SVG（inline 或 .svg 文件） | **screenshot → PNG → addImage** | 506-515 |
| CSS gradient 背景 | **screenshot 整块 → PNG → addImage** | 516-536 |
| box-shadow | screenshot 时扩展 clip 区域容纳阴影 | 258-268 |
| 边框 | 拆成 4 条 `addShape(line, ...)` 画上去 | 478-501 |

判定逻辑在 `html2pptx.js:430-446`：

```javascript
const isSvgImage = ...src.endsWith('.svg')...;
const shouldRender = isSvgImage
  || objectFit !== 'fill'
  || objectPosition !== '50% 50%'
  || borderRadius
  || (filter && filter !== 'none')
  || hasBoxShadow;
if (shouldRender) {
   // → screenshot 为 PNG，原 <img> 被替换成 type:'image' + 本地 PNG path
}
```

**意义**：你能在 PPT 里直接选中文字编辑（因为 `addText` 是原生 PptxGenJS 文本框），同时复杂视觉效果用图片不失真。这是 PptxGenJS + python-pptx 用户都梦寐以求的方案。

### 5.2 用了哪些 npm 包（真实依赖，从 `package.json`）

```json
{
  "dependencies": {
    "fast-glob": "^3.3.3",         // 文件匹配
    "minimist": "^1.2.8",          // CLI 参数解析
    "playwright": "^1.57.0",       // 浏览器渲染（headless chromium）
    "pptxgenjs": "^4.0.1",         // 关键：生成 .pptx 的 Node 库
    "sharp": "^0.34.5"             // 图像处理（虽然 package 中声明但 html2pptx.js 实际未直接 import）
  }
}
```

补充：Python 侧 `webview.py` 还会用 `pdf2image`（需要 poppler）+ `pypdf` 做 PDF 兜底。

### 5.3 字体怎么处理？（这是你担心"字号截断"的核心）

`html2pptx.js:2869-2899` 用 Chrome DevTools Protocol 抓真实渲染字体：

```javascript
// 用 CDP CSS.getPlatformFontsForNode 获取浏览器实际渲染该节点用的物理字体
const cdp = await page.context().newCDPSession(page);
await cdp.send('DOM.enable');
await cdp.send('CSS.enable');
...
for (const nodeId of nodeIds) {
  const { fonts } = await cdp.send('CSS.getPlatformFontsForNode', { nodeId });
  if (fonts && fonts.length > 0) {
    fonts.sort((a, b) => b.glyphCount - a.glyphCount);
    const primaryFont = fonts[0].familyName;
    // 把真实字体名写到 data-actual-font 属性上
    await cdp.send('DOM.setAttributeValue', { nodeId, name: 'data-actual-font', value: primaryFont });
  }
}
```

然后 `extractSlideData` (`html2pptx.js:729`) 读这个 attribute：

```javascript
const extractFontFace = (el, fontFamily) => {
  const actualFont = el?.getAttribute?.('data-actual-font');
  if (actualFont) return actualFont;   // 优先用真实字体
  ...
  return 'Microsoft YaHei';   // 终极兜底
};
```

**好处**：CSS 里写 `font-family: 'Inter', 'Microsoft YaHei', sans-serif`，最后 PPT 里写的字体是浏览器实际选中的那个（比如 macOS 上是 `Inter`，Windows 上是 `Microsoft YaHei`），避免 PPT 自己再做一次 fallback 导致宽度漂移。

### 5.4 验证机制（防止"字号刚刚好挤到边"）
- `html2pptx.js:50-79` `getBodyDimensions`：检测 scrollWidth/scrollHeight 是否超过 body → 报 overflow
- `html2pptx.js:120-150` `validateTextBoxPosition`：要求文本框距底部 ≥ 0.5 inch（PowerPoint 渲染 quirk）
- `html2pptx.js:646-665` 单行文本宽度补偿 +2%（PowerPoint 字号计算和浏览器有 2% 差异，硬编码 fix）

错误消息会随 `inspect_slide` 一路冒泡回到 LLM。例：
```
HTML content overflows body by 12.3pt vertically (Remember: leave 0.5" margin at bottom of slide)
```
这样 LLM 看到的不是黑盒错误，而是可操作的修复指令。

### 5.5 失败模式 + 兜底

| 失败 | 兜底 |
|---|---|
| html2pptx 报 validation error（强模式） | 抛 Exception 让 LLM 看到 → 修 HTML 重来 |
| html2pptx 报 validation error 但 `--soft` | 跳过有问题的元素，继续转，记 warning（`main.py:202` 默认 soft=True） |
| html2pptx 整个失败（如缺 node_modules） | `main.py:204-211` catch → 把错误写到 `.html2pptx-error.txt` → 改用 PDF 兜底 |
| 任何情况都会再跑一次 PDF | `main.py:213-218` `finally` 块强制 Playwright print 出一份 PDF（slide_images-pdf 文件夹也会留底） |

### 5.6 你能复用 Node 这段吗？

**结论：能且应该。** 这是 PPTAgent 最有差异化价值的代码，python-pptx 没有任何等价物。

落地路径建议：
1. 把 `deeppresenter/html2pptx/` 整个目录拷进你的项目
2. 你的 Python skill 调 `node html2pptx_cli.js --html_dir ./slides --output out.pptx --layout 16:9`（这正是 `deeppresenter/utils/webview.py:206` 的做法）
3. 不需要任何修改就能跑——它是个完全独立的 CLI

**不要尝试**：用 python-pptx 自己实现"DOM 解析 + 几何映射"。这一段是 PptxGenJS 生态独有的能力（PptxGenJS 的 API 比 python-pptx 干净得多，特别是 `addShape`/`addTable`/`addText` 的参数模型），自己接 python-pptx 等于重写 3000 行 + 浏览器侧逻辑，吃力不讨好。

---

## 六、Prompt 工程（roles/*.yaml 的提炼）

按可抄性排序（5 选 5，直接放进你的 .claude/skills/auto-ppt/）：

### 6.1 Planner（大纲规划）—— `deeppresenter/roles/Planner.yaml`
- **结构最干净**：先调研 → 设计三段式叙事弧（开篇/主体/结尾） → 输出 `{"slides":[{index, title, context}]}` → 调 finalize
- 直接可用：第 11-15 行的输出 schema 描述

### 6.2 Design（HTML 设计）—— `deeppresenter/roles/Design.yaml`
- 4 段 `<工作流程>` + 4 大 `<风格说明>`，把所有 html2pptx 约束以"风格指南"包装写出来
- **抄你的 skill 哪部分**：那 4 大 `<风格说明>` 块（第 20-30 行）。即便你不用 HTML 中转，这些"严格边界 / 禁裸文本 / 安全字体"原则对任何 LLM-driven slide 生成都成立

### 6.3 SubAgent（并发子任务）—— `deeppresenter/roles/SubAgent.yaml`
- 解决 fanout 时 "子 agent 没上下文" 的标准模式：所有 brief 都写在 `context_file` 里，task 字段只是动作指令
- 你做循环时可借用：每轮 Manus 视觉反馈封成 context_file，再启子 Claude 单独修

### 6.4 Layout Selector（旧版但好用）—— `pptagent/roles/layout_selector.yaml`
- 旧 PPTAgent 用法是从预定义版式池里选一个最合适的
- 适合你"内部周报 / 外部 pitch / 评估报告"这种已有模板的场景：把每种模板抽成 layout option，让 LLM 推理选哪个

### 6.5 Reflection prompts —— `pptagent/prompts/ppteval/*.txt`
- 三个评分 prompt 都很短（每个 ~30 行）、5 分制、要求输出 `{"reason": ..., "score": int}`
- 你想做 self-evaluation 时几乎可以原样套用 `ppteval_content.txt` 和 `ppteval_style.txt`

---

## 七、依赖清单（如果直接复用要装什么）

### 7.1 Python 端（关键依赖，从 `pyproject.toml:31`）
```
playwright>=1.55.0        # ←必装，html2pptx 兜底转 PDF 用
pdf2image                 # ←需要系统 poppler
pypdf>=6.1.1
fastmcp>=2.10.0,<2.14.0   # ←工具 server 框架
openai>=1.108.2           # ←统一走 OpenAI 协议
markitdown[all]           # ←PDF/docx → md
trafilatura>=2.0.0        # ←网页正文提取
fake-useragent>=2.2.0
pptagent-pptx>=0.0.1      # ←PPTAgent 自己 fork 的 python-pptx
```

可选：`litellm` (走 100+ provider)、`fasttext` (语种识别)、`docker` (sandbox 工具)

### 7.2 Node 端（html2pptx 必装）
```
playwright   ^1.57.0
pptxgenjs    ^4.0.1
fast-glob    ^3.3.3
minimist     ^1.2.8
sharp        ^0.34.5
```
+ Chromium 浏览器：`npx playwright install chromium`

### 7.3 系统依赖
- **poppler**（pdf2image）—— `brew install poppler` (macOS)
- **Chromium / Chrome**（Playwright）—— `playwright install`
- **Docker**（仅 sandbox 工具，可选）
- 可选：MinerU 自部署服务（PDF 高保真解析）

### 7.4 迁移成本估算
| 复用范围 | 增量代码量 | 增量依赖 | 难度 |
|---|---|---|---|
| 仅 `html2pptx/` Node 子目录 | ~3000 行 JS（一行不动） | playwright + pptxgenjs | ★（一周内可融入） |
| + reflect.py + Design.yaml | + ~200 行 Python + 1 yaml | fastmcp + jinja2 | ★★ |
| 完整 deeppresenter 框架 | 上万行 | 完整 pyproject 依赖 | ★★★★（不建议） |

---

## 八、最终建议：抄什么 / 不抄什么

### ✅ 直接拿来用
1. **整个 `deeppresenter/html2pptx/` 子目录**（含 `html2pptx.js` + `html2pptx_cli.js` + `package.json`）—— 这是 PPTAgent 最值钱的代码，3000 行的混合渲染管线。直接 fork 进你的项目，按 README 装好 npm 依赖即可。
2. **`Design.yaml` 中"严格边界 + 跨平台字体 + 禁裸文本 + object-fit"四条风格规则**—— 不管你后端用什么生成 HTML，这些约束都是 html2pptx 能正常工作的硬前提。
3. **`reflect.py` 里 `inspect_slide` 工具的双模式（validate-only + reflective image return）**—— 即给 LLM 文本错误又能选择性返图，复用度极高。
4. **`Planner.yaml` 的大纲 schema + `commands.py:543` 的 Rich Table 人机协同 outline 编辑器**—— 几乎照搬就能实现你 Module 1 的"用户介入" 体验。
5. **`pptagent/prompts/ppteval/ppteval_content.txt` + `ppteval_style.txt` 的 5 分制评分模板**—— 直接套用为 Module 3 的自评 prompt。

### ⚠️ 部分参考
1. **`any2markdown.py` 的"PDF 走 MinerU、其他走 MarkItDown"路由策略**—— MinerU 是付费/自部署，你也可以只用 MarkItDown 起步，需要时再补 MinerU。
2. **multiagent_mode 的 fan-out 设计（global.css + delegation file + SubAgent）**—— 如果你的 deck > 5 页且预算紧张，这个并发模式能省 50% 时间。但工程上需要 MCP 框架支撑，前期可不上。
3. **`agent.py:356` `compact_history` 的上下文折叠**—— 等你的循环真的跑到 200K 时再考虑。前期不需要。

### ❌ 不要用
1. **整套 deeppresenter 框架（含 fastmcp 工具 server、docker sandbox、AgentLoop）**—— 太重，强依赖 MCP 协议和 Docker。你 .claude/skills/ 已经是更轻的 agent runtime，没必要再套一层。
2. **`pptagent/` 的模板槽位生成路径（induct.py、pptgen.py、layout induction）**—— 这是论文实验代码，依赖 pre-built template `.pptx` 文件做 layout induction，逻辑老旧且和"HTML 设计"路线互斥。CLAUDE.md 也说了它是 legacy。
3. **`webui.py`（Gradio UI）**—— CLAUDE.md 明确："the root README.md is not fully current. It still references paths like webui.py that are not present in this checkout"。已废弃，别看。

---

## 九、下一步具体动作（3 条以内）

1. **先做最小集成试跑**：
   ```
   cp -r research/PPTAgent/deeppresenter/html2pptx ./html2pptx
   cd html2pptx && npm install && npx playwright install chromium
   # 手写一个最简 slide.html（带 <body style="width:1280px;height:720px">、几个 <p>、一张 <img>）
   node html2pptx_cli.js --html slide.html --output test.pptx --layout 16:9
   ```
   验证你的环境能跑通这条最关键的转换链路，再决定要不要继续往上叠。

2. **把 `Design.yaml` 的"风格说明"那一段（zh 版本第 20-30 行）和 `reflect.py` 的 `inspect_slide` 工具语义抄进你的 .claude/skills/auto-ppt/SKILL.md**，让 Claude 在生成 HTML 时遵守这些 html2pptx 约束。即使你暂时不接 Manus 视觉反馈，validate-only 模式的文本错误也已经够你做一轮自修。

3. **暂时不动 Planner/Research 工具链**。你的 Module 1（读文档 + 大纲）继续用现有 Claude 流程或简单 MarkItDown 即可。等 Module 2+5 跑通了，再回头看 PPTAgent 的工具是否值得吸收（特别是 MinerU，是否值得为更高 PDF 解析质量付费）。
