# Auto-PPT

HTML-first 自动 PPT 生成 pipeline。Claude 多轮自迭代生成幻灯片，最终转换为格式保真的 `.pptx`。

> 借鉴 [autoresearch](https://github.com/karpathy/...) 的 LOOP FOREVER 模式 + [PPTAgent](https://github.com/icip-cas/PPTAgent) 的 HTML→PPTX 引擎。

## 5 模块流水线

```
┌────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────┐  ┌─────────────┐
│ 1. Plan    │→ │ 2. Design    │→ │ 3. Refine  │→ │ 4. Loop  │→ │ 5. Convert  │
│ PDF→Outline│  │ Outline→HTML │  │ Iterate UI │  │ Driver   │  │ HTML→PPTX   │
└────────────┘  └──────────────┘  └────────────┘  └──────────┘  └─────────────┘
   plan.json     slides/*.html    scores.json     state.json     final.pptx
```

每个模块的指令在 `pipeline/<n>_<name>/PROMPT.md`，由 Claude 在 `/loop` 中逐步执行。

## 目录结构

```
Auto-ppt/
├── pipeline/                       # 5 模块 prompt 库 (Claude 的指令)
│   ├── 1_plan/PROMPT.md
│   ├── 2_design/PROMPT.md + DESIGN_RULES.md
│   ├── 3_refine/PROMPT.md + RUBRIC.md
│   ├── 4_loop/LOOP.md
│   └── 5_convert/PROMPT.md
├── converter/                      # PPTAgent html2pptx fork (Node)
│   ├── html2pptx.js                # 已 patch SVGAnimatedString bug
│   ├── html2pptx_cli.js
│   ├── verify_pptx.py              # 自检脚本
│   └── CAPABILITIES.md             # 实测能力清单 + workaround
├── research/                       # 调研笔记 (不入版本控制?)
│   ├── PPTAGENT_NOTES.md
│   └── PPTAgent/                   # 完整 clone (gitignored)
├── run/                            # 每次跑生成一个 <run_id>/
│   └── demo01/
│       ├── plan.json
│       ├── slides/
│       │   ├── slide_01.html       # 深色封面
│       │   ├── slide_02.html       # before/after 对比卡
│       │   ├── slide_03.html       # 5 KPI 指标条
│       │   └── icons/{check,x}.svg
│       └── final.pptx              # 127KB / 3 张 / 零截图回退
├── Data/                           # 用户素材源 (PDF/PNG)
├── output/                         # 现有 auto-ppt skill 的产物 (legacy)
├── .claude/skills/auto-ppt/        # 已有的 JSON→PPTX skill (legacy, 仍可用)
└── state.json                      # pipeline 当前状态
```

## 快速开始

### 1. 一次性环境准备

```bash
cd converter && npm install && npx playwright install chromium
pip3 install python-pptx
```

### 2. 跑当前 demo

```bash
# state.json 已配好 demo01
node converter/html2pptx_cli.js \
  --html_dir run/demo01/slides \
  --output run/demo01/final.pptx \
  --layout 16:9
open run/demo01/final.pptx
```

### 3. 跑你自己的 PPT

```bash
# 编辑 state.json，填入：
# - inputs.materials: 你的 PDF / md / 链接路径
# - inputs.user_intent: PPT 给谁看、目标
# - run_id: new-deck-name
# - current_module: "1_plan"

# 然后启动自迭代循环 (需 Claude Code v2.1.72+)
caffeinate -i claude --permission-mode acceptEdits
# 进入 Claude 后：
> 读 pipeline/4_loop/LOOP.md，然后 /loop run auto-ppt 直到收敛
```

放笔记本上一晚，第二天醒来 `run/<run_id>/final.pptx` 就是收敛后的成品。

## 杀手锏

| 痛点 | 解决 |
|---|---|
| HTML→PPTX 格式漂移 / 文字截断 / 图标形变 | 实测 4 类布局零损失；CSS 限制清单在 `converter/CAPABILITIES.md` |
| Module 2 写出 PPT 不支持的 HTML | `pipeline/2_design/DESIGN_RULES.md` + 自校验 |
| 跑一晚怕翻车 | `state.json` 单文件断点续传、`STOP` 文件 killswitch、`refine_round` 上限、`max_budget_usd` |
| 成本失控 | tier 模型：Module 1/3 Sonnet、Module 2 Opus、Module 5 无 LLM |

## 已知限制

- `box-shadow` / `linear-gradient` / `backdrop-filter` / inline `<svg>` 不可用（DESIGN_RULES.md 给了 workaround）
- 视频幻灯片 (`<video>`) 当前不支持，会被忽略
- Manus 集成是可选项；默认 `use_manus: false` 走 Claude-only
- macOS 上 html2pptx 用系统 Chrome (`channel: 'chrome'`)；Chrome 没装会回退 chromium

## 参考资料

- 调研笔记: [`research/PPTAGENT_NOTES.md`](research/PPTAGENT_NOTES.md)
- 转换器能力清单: [`converter/CAPABILITIES.md`](converter/CAPABILITIES.md)
- 现有 skill (legacy): [`.claude/skills/auto-ppt/SKILL.md`](.claude/skills/auto-ppt/SKILL.md)
