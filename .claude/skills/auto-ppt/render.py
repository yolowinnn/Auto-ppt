#!/usr/bin/env python3
"""
render.py — turn a JSON spec into a .pptx file.

Usage:
    python3 render.py <spec.json> <output.pptx>

The spec file's directory is used as the base for resolving relative
image paths inside the spec.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from builder import PptxBuilder
from styles.internal import InternalStyle
from styles.pitch import PitchStyle
from styles.report import ReportStyle


STYLE_REGISTRY = {
    "internal": InternalStyle,
    "pitch": PitchStyle,
    "report": ReportStyle,
}

# layout name -> PptxBuilder method
LAYOUT_DISPATCH = {
    "title":               "add_title_slide",
    "toc":                 "add_toc_slide",
    "section":             "add_section_slide",
    "bullets":             "add_bullets_slide",
    "two_col":             "add_two_col_slide",
    "image_grid":          "add_image_grid_slide",
    "kpi_cards":           "add_kpi_cards_slide",
    "data_table":          "add_data_table_slide",
    "comparison":          "add_comparison_slide",
    "flow":                "add_flow_slide",
    "thanks":              "add_thanks_slide",
    "chart_bar":           "add_chart_bar_slide",
    "image_with_callouts": "add_image_with_callouts_slide",
    "metrics_strip":       "add_metrics_strip_slide",
    "three_line_table":    "add_three_line_table_slide",
    "comparison_cards":    "add_comparison_cards_slide",
    "video":               "add_video_slide",
}


def render(spec_path, out_path):
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    style_key = spec.get("style", "internal")
    if style_key not in STYLE_REGISTRY:
        raise ValueError(
            f"Unknown style {style_key!r}. Choose one of: "
            f"{list(STYLE_REGISTRY)}")
    style = STYLE_REGISTRY[style_key](spec.get("meta", {}))
    spec_dir = os.path.dirname(os.path.abspath(spec_path))
    builder = PptxBuilder(style, spec_dir=spec_dir)
    for i, slide_spec in enumerate(spec.get("slides", [])):
        layout = slide_spec.get("layout")
        if layout not in LAYOUT_DISPATCH:
            raise ValueError(
                f"Slide {i}: unknown layout {layout!r}. Supported: "
                f"{list(LAYOUT_DISPATCH)}")
        method = getattr(builder, LAYOUT_DISPATCH[layout])
        method(slide_spec)
    builder.save(out_path)
    return out_path


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    spec_path, out_path = argv[1], argv[2]
    if not os.path.isfile(spec_path):
        print(f"spec not found: {spec_path}", file=sys.stderr)
        return 1
    out = render(spec_path, out_path)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
