# Refine Rubric — score each slide 0-10 on four axes

> Borrowed/adapted from PPTAgent's PPTEval (content/style/logic).

## 1. Content (信息密度与准确性) 0-10
- 10: Every claim is backed by a number or source from plan.json
- 7: Most claims sourced, ≤ 1 vague statement
- 4: Generic statements ("performance improved") with no numbers
- 1: Fabricated or contradictory facts

## 2. Layout (视觉布局) 0-10
- 10: Uses canvas effectively, clear visual hierarchy, no overflow, no large blank areas
- 7: Minor whitespace issues but readable
- 4: Cramped or scattered, hierarchy unclear
- 1: Text overlapping or pushed off-canvas

## 3. Visual (设计美感) 0-10
- 10: Visually compelling, brand-consistent, uses color/icon/border purposefully
- 7: Clean and professional but unremarkable
- 4: Plain wall of text, no visual interest
- 1: Visually broken (bad colors, wrong fonts)

## 4. Conciseness (文本精简) 0-10
- 10: Every word earns its place. Bullets ≤ 12 chars where possible. No filler.
- 7: Slightly verbose in 1-2 spots
- 4: Multiple sentences where bullets would do
- 1: Paragraph-style prose, hard to read at a glance

## Scoring procedure
1. Open the slide HTML in Playwright at 1280×720 → screenshot.
2. Send screenshot + rubric to multimodal eval (Claude with vision OR `inspect_slide`-style tool).
3. Get JSON back: `{"content": n, "layout": n, "visual": n, "conciseness": n, "reasoning": "..."}`.
4. Total = average of four axes.

## Exit threshold
- Average per slide ≥ 8.5 → accept
- Average per slide < 6.5 after round 2 → flag for manual intervention
