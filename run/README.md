# run/ — 本地工作区（不入版本控制）

每次生成 PPT 会在这里建一个 `<run_id>/`，包含 `plan.json`、`slides/*.html`、`final.pptx` 等。

**这些都是本地工作产物，且常含客户机密内容（提取的数字、内部路径、品牌素材），不推到公开仓库。** `.gitignore` 已忽略整个 `run/`（仅保留本 README）。

要分享一个**可公开的示例 run**时，用虚构数据生成，再手动 `git add -f run/<example>/`。
