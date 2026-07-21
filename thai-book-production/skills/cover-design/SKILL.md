---
name: cover-design
description: >
  Design the book cover — front (and optionally spine + back for print). Use when the
  user asks to "ออกแบบปก", "ทำปกหนังสือ", "book cover", "cover design", "หน้าปก", or
  when the router reaches the BUILD stage. Produces cover art plus the correctly-sized
  export for epub (front only) or print (full wrap).
---

## Paths (thai-book-production layout)

หนึ่ง working folder = หนังสือหนึ่งเล่ม Resolve ทุก path จาก `book.yaml → layout:` ที่ root
ของ folder — **ห้าม hardcode** ถ้าไม่มี `book.yaml` แปลว่าไม่ได้อยู่ใน book folder ให้ให้
`init-book` scaffold ก่อน ค่า default:

| what | path |
|------|------|
| chapters | `chapters/chNN.md` |
| outline | `outline/outline.md`, `outline/plan.md` |
| references | `refs/docs/`, `refs/blogs/` |
| slides | `media/slides/chNN.yaml` |
| screenshots (จริง, จับจากโปรแกรม) | `media/screenshots/` (+ `inventory.json`) |
| generated (AI, built-in TextToImage) | `media/generated/` (+ `inventory.json`) |
| reports (QC ทุกชนิด) | `reports/chNN.audit.md`, `reports/chNN.proofread.md`, `reports/chNN.yaml-audit.md` |
| apparatus | `apparatus/glossary.md`, `apparatus/index.md` |
| translations | `translations/<lang>/chapters/chNN.md` |
| assets | `assets/` |
| build output | `build/` |


# Cover Design

Produce the cover artwork and correctly-sized exports.

## Config (from `book.yaml`)
Read `book → {title, subtitle, author, publisher, language}` and the `cover:` block:
`tool` (**`nano-banana`** (default) | `canva` | `programmatic`), `aspect` (default `3:4`),
`art_style` / `motif` (art direction for the AI path), `epub_px` (default `[1600, 2560]`),
`print_trim_mm` (default `[152, 229]` = 6×9in), `bleed_mm` (default `3`),
`paper_thickness_mm` (default `0.0572`). All overridable per book.

## Inputs to gather
- Confirm title / subtitle / author spelling (cover typos are expensive).
- Format: **epub** (front cover only) vs **print** (front + spine + back wrap).
- If print: page count (from `build/` output or the page plan) — needed for spine width.
- Visual direction / brand (if `agentic-press-brand` is in use, pull its tokens).

## Spine width (print only)
```
spine_mm = page_count × cover.paper_thickness_mm
wrap_width_mm  = (print_trim_mm[0] × 2) + spine_mm + (bleed_mm × 2)
wrap_height_mm =  print_trim_mm[1]        +           (bleed_mm × 2)
```
State the computed spine/wrap size to the author before rendering.

## Generation path — `cover.tool`

### `nano-banana` (built-in TextToImage — DEFAULT, AI cover art with on-cover text)
Use the built-in **`TextToImage`** tool, model **`flash`** (Gemini nano-banana — renders Thai +
English text), `aspect_ratio` = `cover.aspect` (default `3:4`), `size` `2K`. Needs `imageToolsEnabled:
true` + a provider key/gateway. The LLM authors the prompt from the book's title/subtitle/author +
subject + `cover.art_style`/`cover.motif`.

**House cover look — proven prompt recipe (flat front, not a 3D mockup).** Build the prompt from
these mandatory pieces:
- **Geometry (verbatim):** `"STRAIGHT-ON, no rotation, no perspective, no visible spine"`.
- **Frame (verbatim, when `cover.frame: flat`):** `"rounded corners, thin edge, soft drop shadow on
  off-white background"` (this gives the subtle hardcover-hinge look on an off-white field). For
  `cover.frame: bleed`, drop this line and make the artwork full-bleed instead.
- **Artwork:** deep navy field (`#0D1B2A`) + gentle teal glow + the subject **motif** (e.g. a glowing
  teal node/diagram for a technical book). House palette: navy / teal / gold accents.
- **On-cover text — take the strings from `book.yaml`** (`title`, `subtitle`, `author`, optional
  tagline/label), NOT hardcoded. Put **one line per bullet, each wrapped in quotes**, top→bottom
  (nano-banana renders Thai + English). The exact set of lines is per book — a cover might be just
  title + author, or title + subtitle + tagline + author. Illustrative example (do not reuse literally):
  `"<label>"` / `"<TITLE>"` / `"<thai subtitle>"` / `"<thai tagline>"` / `"<author>"`.
- **Always end the prompt with:** `"All text must be crisp, correctly spelled, no garbled text."`
- `TextToImage` writes the file under `output/img-…`; **move** it to `{assets}/cover-front.png`
  (`mv "<output/img-… path>" {assets}/cover-front.png`, transcode to PNG if needed) and store the
  final prompt in the build report.
- Print wrap (spine + back) still uses canva/programmatic.

**Prompt skeleton:**
```
<cover.art_style>. STRAIGHT-ON, no rotation, no perspective, no visible spine.
rounded corners, thin edge, soft drop shadow on off-white background.
Deep navy #0D1B2A with teal glow. <cover.motif>.
Text on the cover, each line exactly:
"<label>"
"<TITLE>"
"<thai subtitle>"
"<thai tagline>"
"<author>"
Thin gold divider above the tagline. Legible Thai + English typography.
All text must be crisp, correctly spelled, no garbled text.
```
Confirm every string's spelling with the author before rendering.

### `canva` (when the Canva connector is preferred / for editable source)
1. Use the Canva tools (`generate-design` / `create-design-from-brand-template` →
   `perform-editing-operations` for title/author text → `export-design`) to build the
   front cover at `epub_px`. For print, size the design to `wrap_width_mm × wrap_height_mm`
   at 300 DPI including bleed.
2. Export front cover as PNG and, for print, the full wrap as PDF.
3. Keep the Canva design link in the build report as the editable source.

### `programmatic` (offline fallback — no Canva)
1. Render with Pillow using the bundled Sarabun font
   (`../mockup-screenshot/assets/fonts/Sarabun/`). Compose title/subtitle/author on a
   solid or gradient field; keep safe margins ≥ `bleed_mm` from every trimmed edge.
2. epub: export `epub_px` PNG. print: build a `wrap_width_mm × wrap_height_mm` @ 300 DPI
   canvas (front | spine | back), place spine text rotated 90°, export as PDF.

## Outputs (to `{assets}/`)
- `cover-front.png` — front cover at `epub_px` (always; epub needs this).
- `cover-wrap.pdf` — full print wrap with computed spine (print only).
- Editable source reference (Canva link) or the generating script (programmatic).

## Guardrails
- Confirm final title/subtitle spelling with the author before rendering — cover typos
  are expensive.
- Get explicit approval before any publish/export-to-store action (that is a separate,
  permissioned step).
- No copyrighted characters or licensed imagery in the artwork.
