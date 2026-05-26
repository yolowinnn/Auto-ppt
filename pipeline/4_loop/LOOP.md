# Module 4 — The loop driver (`/loop` entrypoint)

> This is the file `/loop` reads each wake-up to decide what to do next.
> Path: `pipeline/4_loop/LOOP.md` is symlinked from `.claude/loop.md` (or copy it).

## Each wake-up, do exactly:

1. **Read state**: `state.json` from project root.
2. **Branch on `current_module`**:
   - `"1_plan"` → load `pipeline/1_plan/PROMPT.md`, execute it on `state.json.inputs`.
   - `"2_design"` → load `pipeline/2_design/PROMPT.md`, execute.
   - `"3_refine"` → load `pipeline/3_refine/PROMPT.md`, execute one refine round.
   - `"5_convert"` → run `node converter/html2pptx_cli.js --html_dir run/<run_id>/slides --output run/<run_id>/final.pptx --layout 16:9`, then run `python3 converter/verify_pptx.py run/<run_id>/final.pptx > run/<run_id>/verify.log`. Set `current_module = "done"`.
   - `"done"` → say "converged" and stop the loop.
3. **Always** end with: write updated `state.json` to disk.

## Exit rules
- If `state.json.errors` is non-empty → output errors and stop (do not silently retry).
- If `state.json.questions` is non-empty → ask the user the first question and stop.
- If `state.json.refine_round >= 5` → set `current_module = "5_convert"` (force exit refine loop).
- If `state.json.last_score >= 8.5` → set `current_module = "5_convert"`.

## Model selection per module (cost control)
- Module 1 (plan): Sonnet — needs reading comprehension, not creativity
- Module 2 (design): Opus — visual design quality matters
- Module 3 (refine): Sonnet — iterative cleanup
- Module 5 (convert): no LLM, just Node + Python

## Hard guardrails
- NEVER modify files outside `run/<run_id>/`, `state.json`, or pipeline configs.
- NEVER call `rm -rf` on `run/`.
- If a Manus API call fails, log to `state.json.errors[]` and continue with Claude-only.
- If conversion fails 2 times in a row, set `current_module = "done"` and surface the error.

## Killswitch
- If `STOP` file exists at project root → set `current_module = "done"` and stop.

## How to start the loop (for the user)

```bash
cd /Users/jiaweili/main_folder/projects/pending_project/Auto-ppt
# Edit state.json to set inputs.materials and inputs.user_intent
caffeinate -i claude --permission-mode acceptEdits
# inside Claude:
> /loop run auto-ppt pipeline until converged
```
