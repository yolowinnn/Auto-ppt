# auto-ppt — maintenance & extension guide

Skill at `.claude/skills/auto-ppt/`. Generates TaomoAI / IndustrialMind-styled
PPTX decks from a JSON spec. See [SKILL.md](SKILL.md) for the user-facing
workflow; this file is for *upgrading the skill itself*.

## Layout of files

```
auto-ppt/
├── SKILL.md            # entry point — Claude reads this when invoked
├── README.md           # you are here — maintenance guide
├── theme.py            # colors, fonts, sizes, asset paths (single source of truth)
├── builder.py          # PptxBuilder + add_<layout>_slide methods
├── render.py           # CLI driver: spec.json → output.pptx
├── styles/
│   ├── internal.py     # Style A: Siemens / TaomoAI weekly tracking
│   ├── pitch.py        # Style B: external IndustrialMind pitch
│   └── report.py       # Style C: assessment / evaluation report
├── examples/           # one spec per style — start here when adding a new variant
└── assets/             # logo PNGs (optional; see assets/README.md)
```

## Render manually

```bash
python3 .claude/skills/auto-ppt/render.py path/to/spec.json path/to/out.pptx
```

Requires `python-pptx` (`pip3 install python-pptx`).

## Add a new layout

1. Implement `add_<name>_slide(self, spec)` in [builder.py](builder.py).
   - Use the helpers `_add_text`, `_add_rect`, `_add_line`, `_add_image_or_placeholder`.
   - Pull style-dependent values via `self.style.<attr>`. Don't hard-code colors.
2. Register the layout in `LAYOUT_DISPATCH` at the top of [render.py](render.py).
3. Document the spec fields in [SKILL.md](SKILL.md) under "Supported layouts".
4. Add a slide to one of the example specs in [examples/](examples/).
5. Re-render the example to verify it doesn't crash.

## Add a new style

1. Create `styles/<name>.py` with a class implementing the same interface as
   `InternalStyle`:
   - class attrs: `name`, `bg_color`, `table_header_bg`, `table_header_fg`,
     `default_footer`
   - `__init__(self, meta)`
   - `draw_header(self, slide, *, title, subtitle=None)`
   - `draw_logo(self, slide)`
   - `draw_footer(self, slide)`
   - `draw_title_slide(self, slide, spec, spec_dir)`
   - `draw_section_slide(self, slide, spec)`
   - `draw_thanks_slide(self, slide, spec, spec_dir)`
2. Register it in `STYLE_REGISTRY` in [render.py](render.py).
3. Add a sample spec in [examples/](examples/).

## Tweak existing colors / fonts

- **Used by all styles** → edit [theme.py](theme.py). One commit, three styles change.
- **Used by one style only** → put the override in the relevant `styles/*.py`
  class as a class attribute.

## Drop in real logos

See [assets/README.md](assets/README.md). The renderer auto-detects PNGs;
without them it falls back to a text/triangle wordmark.

## Testing

Just re-render the three example specs after any change:

```bash
cd /Users/jiaweili/main_folder/projects/Auto-ppt
for s in internal_weekly pitch_product report_assessment; do
  python3 .claude/skills/auto-ppt/render.py \
    .claude/skills/auto-ppt/examples/${s}.json \
    output/test_${s}.pptx || echo "FAILED: $s"
done
```

If they all render without exception, the basics work. Open them in PowerPoint
to eyeball the visuals.

## Roadmap (to make it sharper over time)

- [ ] Native bar/line chart layout (`chart_bar`) so we don't have to reduce charts to tables.
- [ ] Native CJK font embedding so the deck looks identical on Windows/Mac/Linux.
- [ ] An `image_with_callouts` layout for annotated screenshots (red boxes + labels).
- [ ] A `process_diagram` layout with branching arrows (the current `flow` is linear only).
- [ ] Screenshot-extraction helper: given a PDF, dump page-N as PNG into `assets/` for cover use.
- [ ] Pull KPI numbers / table rows directly from a CSV path in the spec.
