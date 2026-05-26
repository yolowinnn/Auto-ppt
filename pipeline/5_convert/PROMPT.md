# Module 5 — Convert (HTML → PPTX)

## Goal
Produce a final `.pptx` from the refined HTML deck and verify no layout / font / icon issues.

## Inputs
- `run/<run_id>/slides/slide_*.html`
- `run/<run_id>/icons/` (referenced by slides)

## Process
1. Run conversion:
   ```bash
   node converter/html2pptx_cli.js \
     --html_dir run/<run_id>/slides \
     --output run/<run_id>/final.pptx \
     --layout 16:9
   ```
2. Run verify:
   ```bash
   python3 converter/verify_pptx.py run/<run_id>/final.pptx > run/<run_id>/verify.log
   ```
3. Check verify.log for red flags:
   - Slide count != `len(plan.json.slides)` → re-run from Module 2 with stricter prompt
   - Picture (screenshot) count > expected (each slide should have ≤ 2 PICTURE for icons) → likely inline `<svg>` slipped through, fix offending slide and re-run
   - Text shape inventory looks empty → fonts didn't apply, check CSS
4. Set `current_module = "done"` on success, or re-queue specific failed slides.

## Success criteria
- `final.pptx` exists, size > 30KB
- `verify.log` shows expected slide count and shape counts within expected range
- File opens cleanly in PowerPoint / Keynote (manual verification by user)

## Failure → re-queue
If verify finds issues attributable to specific slides, write `state.json.requeue_slides = ["s03", "s07"]`, set `current_module = "2_design"` and let the loop redo just those slides.
