"""
Theme constants for the auto-ppt skill.

Colors and fonts are defined ONCE here and referenced by every style file.
If a value should change for all three styles, change it here. If it should
change for only one style, override it in styles/<style>.py.
"""
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor

# ---- Slide geometry (16:9) ---------------------------------------------------
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# ---- Brand colors (sampled from the three reference PDFs) -------------------
# Primary green — used for title underlines, accents, the report bottom bar
GREEN_PRIMARY = RGBColor(0x2E, 0x7D, 0x32)
# Deeper green — used for pitch-deck full-color cover
GREEN_DARK = RGBColor(0x1B, 0x5E, 0x20)
# Bright/lime green — INDUSTRIALMIND.AI wordmark on report cover
GREEN_BRIGHT = RGBColor(0x2E, 0xCC, 0x71)
# Light gray-green for callout boxes (report style)
GRAY_CALLOUT = RGBColor(0xF1, 0xF5, 0xF2)
# Border / divider gray
GRAY_DIVIDER = RGBColor(0xCF, 0xD8, 0xDC)
# Body text dark
TEXT_DARK = RGBColor(0x21, 0x21, 0x21)
TEXT_BODY = RGBColor(0x37, 0x47, 0x4F)
TEXT_MUTED = RGBColor(0x78, 0x90, 0x9C)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

# Semantic colors (KPI cards in report style)
KPI_GOOD = RGBColor(0x66, 0xBB, 0x6A)        # green
KPI_WARN = RGBColor(0xFF, 0xCA, 0x28)        # amber
KPI_BAD = RGBColor(0xEF, 0x53, 0x50)         # red
KPI_INFO = RGBColor(0x42, 0xA5, 0xF5)        # blue accent (cover side bar)

# Comparison table (pitch style)
NEG_GRAY = RGBColor(0x9E, 0x9E, 0x9E)
POS_GREEN = GREEN_DARK

# ---- Fonts ------------------------------------------------------------------
FONT_LATIN = "Calibri"          # safe default; users can change here
FONT_CJK = "Microsoft YaHei"    # CJK fallback used for 中文 text
FONT_TITLE_LATIN = "Calibri"
FONT_TITLE_CJK = "Microsoft YaHei"

# ---- Type scale -------------------------------------------------------------
SZ_COVER_TITLE = Pt(40)
SZ_COVER_SUB = Pt(20)
SZ_SECTION = Pt(36)
SZ_TITLE = Pt(24)
SZ_SUBTITLE = Pt(16)
SZ_BODY = Pt(14)
SZ_SMALL = Pt(11)
SZ_FOOTER = Pt(9)

# ---- Margins ----------------------------------------------------------------
MARGIN_X = Inches(0.5)
MARGIN_TOP = Inches(0.4)
TITLE_BAR_Y = Inches(0.45)
CONTENT_TOP = Inches(1.3)
FOOTER_Y = Inches(7.15)

# ---- Asset paths ------------------------------------------------------------
import os
_HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(_HERE, "assets")
LOGO_INDUSTRIALMIND = os.path.join(ASSETS_DIR, "logo_industrialmind.png")
LOGO_TAOMO = os.path.join(ASSETS_DIR, "logo_taomo.png")


def has_logo(path):
    return os.path.isfile(path)
