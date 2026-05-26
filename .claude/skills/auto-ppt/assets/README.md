# assets/

Drop logo PNGs here. The renderer auto-detects them; without them it draws a
text/triangle wordmark fallback (renders fine, just less branded).

## Expected files

| filename | used by | recommended | what it is |
|---|---|---|---|
| `logo_industrialmind.png` | `internal`, `pitch`, `report` | ~600×400 px, transparent bg, green | The 3-peak ▲▲▲ logo seen in all three reference PDFs. White-on-green for `pitch` cover, green-on-white elsewhere — supply the green-on-transparent version, the renderer doesn't currently recolor. |
| `logo_taomo.png` | (reserved, not used yet) | — | If/when we want a separate Taomo wordmark distinct from IndustrialMind. |

## Cover images

The `internal` style cover uses a right-half full-bleed image (the cityscape in
the original deck). Pass its path as `slides[0].image` in your spec — relative
to the spec file's directory. Drop reusable cover images here too; reference as
`assets/cover_industrial.jpg` from a spec.

## Where the renderer looks

The exact paths are defined in [../theme.py](../theme.py) at the bottom
(`LOGO_INDUSTRIALMIND`, `LOGO_TAOMO`). Change them there if you want a
different layout.
