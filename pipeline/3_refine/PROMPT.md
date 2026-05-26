# Module 3 — Refine

## Goal
Iteratively polish text conciseness AND visual quality of the slides until a quality threshold is met.

## Inputs
- `run/<run_id>/slides/slide_NN.html` (from Module 2)
- `pipeline/3_refine/RUBRIC.md` — scoring rubric
- `state.json.refine_round` — current round counter (starts at 0)

## Process
Each refine round does:

1. **Self-eval pass** (Claude). For each slide:
   - Take Playwright screenshot at 1280×720, save to `run/<run_id>/screenshots/slide_NN_r<round>.png`.
   - Score against rubric (content, layout, visual, conciseness). Save scores to `run/<run_id>/scores_r<round>.json`.
2. **Text trimming pass** (Claude). For slides scoring < 4 on conciseness:
   - Shorten text in place (target: cut 30% of words per bullet without losing meaning).
   - Re-render and re-screenshot.
3. **Visual polish pass** (optional Manus API). For slides scoring < 4 on visual:
   - Send `slide_NN.html` to Manus REST API (`POST /v2/tasks` with prompt "improve the visual design while preserving every text element and image reference; obey constraints in DESIGN_RULES.md").
   - Wait for webhook callback. Replace `slide_NN.html` with returned content.
   - **Critical**: re-validate against DESIGN_RULES.md before accepting (regex check for `box-shadow`, `linear-gradient`, inline `<svg>`).
4. **Verify pass** (Claude). Run html2pptx in `--validate` mode. If any slide fails, revert that slide and re-do with stricter prompting.
5. Update `state.json.refine_round += 1`, `state.json.last_score = <avg>`.

## Exit conditions (any one stops the loop)
- `last_score >= 8.5` (out of 10)
- `refine_round >= 5`
- `last_score < previous_score` for 2 consecutive rounds (regressing — stop)
- `state.json.errors` non-empty (something's broken — pause for human)

When exit: set `current_module = "5_convert"`.

## Manus integration notes
- Auth: `MANUS_API_KEY` from `~/.config/auto-ppt/secrets`
- Endpoint: `https://api.manus.im/v2/tasks` (OpenAI-compat also at `/v1/chat/completions`)
- Cost: ~1 credit per slide per round
- Skip Manus if `state.json.config.use_manus == false` (Claude-only mode)

## Success criteria
- All slides re-rendered without converter errors.
- Average score increased vs previous round (otherwise: regression handled by exit condition).
