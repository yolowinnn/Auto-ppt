# Module 1 — Plan

## Goal
Read user source materials and produce a slide-by-slide outline (`plan.json`) for downstream modules.

## Inputs
- `state.json` → `inputs.materials[]` (paths to PDFs / markdown / images / links)
- `state.json` → `inputs.user_intent` (free text — what the deck is for, audience, tone)
- `state.json` → `inputs.target_slide_count` (optional, default 6-10)

## Process
1. Read every material in `inputs.materials[]`. For PDFs use Read tool with `pages:` for >10 pages.
2. Extract real facts (numbers, dates, names). **Never fabricate numbers** — if a value is uncertain, mark it `"verify": true` in plan.json.
3. Group facts by narrative arc: intro → progress → metrics → risks → next steps. Adapt to `user_intent`.
4. For each slide, pick layout from the allowed list (see `2_design/DESIGN_RULES.md`):
   - `title` (cover), `bullets`, `two_col`, `kpi_cards`, `metrics_strip`, `comparison_cards`, `image_with_callouts`, `data_table`, `three_line_table`, `section`, `thanks`
5. Write `run/<run_id>/plan.json` with the structure below. Cite source paths in `notes.source`.
6. Update `state.json`: set `current_module = "2_design"`, append plan.json path to `artifacts`.

## plan.json schema
```json
{
  "meta": { "title": "...", "subtitle": "...", "audience": "...", "date": "...", "footer": "..." },
  "style_hint": "internal | pitch | report",
  "slides": [
    {
      "id": "s01",
      "layout": "title",
      "title": "...",
      "subtitle": "...",
      "wordmark": "INDUSTRIALMIND.AI"
    },
    {
      "id": "s02",
      "layout": "comparison_cards",
      "title": "...",
      "headline": "...",
      "before": { "label": "...", "items": ["...", "..."] },
      "after":  { "label": "...", "items": ["...", "..."] },
      "notes": { "source": "Data/xxx.pdf p.3-5" }
    }
  ]
}
```

## Success criteria
- `plan.json` is valid JSON, loads without error.
- Every numeric claim has a `source` in notes.
- No layout used that isn't in the allowed list.
- Outline narrative actually answers `user_intent`.

## Failure handling
- If a PDF can't be read, log error in `state.json.errors[]`, continue with remaining materials.
- If `user_intent` is ambiguous, write a clarifying question to `state.json.questions[]` and pause (do NOT proceed to Module 2).
