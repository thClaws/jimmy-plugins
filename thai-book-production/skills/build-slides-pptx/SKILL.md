---
name: build-slides-pptx
description: >
  Render a chapter's slide YAML into a polished, design-first slide deck (PDF + per-slide PNGs)
  using the built-in **`RenderSlides`** tool (Marp + a CSS theme rendered by Chromium). This is the
  DEFAULT and preferred renderer — no LibreOffice, no python-pptx, no ad-hoc scripts. Use when the
  user asks to "สร้างสไลด์", "ทำสไลด์", "render slides", "build slides/pptx", "แปลง yaml เป็นสไลด์",
  "gen preview", "preview สไลด์", "ออกไฟล์สไลด์", or when the router reaches slide rendering. A
  standalone python-pptx path (`slides2pptx.py`) is bundled ONLY as an offline fallback for when the
  RenderSlides tool is unavailable or an editable `.pptx` is explicitly required.
---

## Paths (thai-book-production layout)

หนึ่ง working folder = หนังสือหนึ่งเล่ม Resolve ทุก path จาก `book.yaml → layout:` ที่ root
ของ folder — **ห้าม hardcode** ถ้าไม่มี `book.yaml` แปลว่าไม่ได้อยู่ใน book folder ให้
`init-book` scaffold ก่อน ค่า default:

| what | path |
|------|------|
| chapters | `chapters/chNN.md` |
| slides | `media/slides/chNN.slides.md` → `chNN.yaml` (build artifact) |
| screenshots (จริง, จับจากโปรแกรม) | `media/screenshots/` (+ `inventory.json`) |
| generated (AI, built-in TextToImage) | `media/generated/` (+ `inventory.json`) |
| **slides output (PDF + PNGs)** | `build/slides/chNN.marp.md`, `build/slides/preview/chNN/deck.pdf` + `slide.*.png` |
| reports (QC ทุกชนิด) | `reports/chNN.audit.md`, `reports/chNN.proofread.md`, `reports/chNN.yaml-audit.md` |
| build output | `build/` |

---

# ⭐ Render slides — the ONLY default path (RenderSlides)

**Two steps. That is the whole procedure. Do NOT run `check_env.py`, do NOT call `slides2pptx.py`,
and do NOT write your own Python/Pillow/HTML renderer — the renderer is the `RenderSlides` tool.**

### Step 1 — compile `chNN.yaml → Marp markdown` (+ collect its images)
The only dependency is `pyyaml`. If it's missing, install it inline (`pip install pyyaml` or
`.venv/bin/python -m pip install pyyaml`) and move on — nothing else is needed.
```bash
mkdir -p build/slides
python3 {skill_dir}/scripts/slides_yaml2marp.py \
  media/slides/chNN.yaml -o build/slides/chNN.marp.md
# → "✓ NN slides → build/slides/chNN.marp.md"
# → "✓ K image(s) copied → build/slides/assets/chNN  (pass as RenderSlides image_dir)"
```
The converter **resolves each `{{image:}}`/`{{screenshot:}}` ref to the REAL file on disk**
(matching by stem, so a ref to `foo` finds `foo.jpg` — TextToImage writes `.jpg`, not `.png`) and
**copies it into `build/slides/assets/chNN/`**, emitting `<img src="realname.ext">`. That's why the
deck's images actually render — never rely on the raw `.png`-guessed name. It scans
`media/generated` + `media/screenshots` by default (override with `--media-dir`). Watch its stderr:
a `⚠ … NOT found` line means a figure is missing/misnamed — fix that before rendering, don't ship a
blank slide. (Resolve `media/*` and `build` from `book.yaml → layout:` — defaults shown.)

### Step 2 — render with the `RenderSlides` tool
Call the built-in tool directly (it is a first-class tool, NOT a shell command). Point `image_dir`
at the **assets dir Step 1 populated** so every `<img src>` resolves:
```
RenderSlides(
  markdown_path = build/slides/chNN.marp.md,
  theme         = thai-tech,
  image_dir     = build/slides/assets/chNN,   # the dir Step 1 copied the real figures into
  out_dir       = build/slides/preview/chNN,
)
→ writes build/slides/preview/chNN/deck.pdf + slide-01.png, slide-02.png, …
```
- Endpoint resolves automatically: `SLIDE_RENDER_API` env (self-hosted) → else the thClaws Gateway
  (cloud login). No token handling on your side — the engine injects it.
- Requires `imageToolsEnabled: true` in `.thclaws/settings.json` (same gate as TextToImage). If the
  tool isn't listed by `/tools`, tell the user to enable it and restart the session — **do not fall
  back to writing a renderer.**
- Output PNGs are named `slide-NN.png` (dash) so they pair 1:1 with `generate-tts`'s `slide-NN.wav`
  in the video step.
- **QC:** after it returns, open a couple of `build/slides/preview/chNN/slide-*.png` with the Read
  tool before delivering — check Thai fonts, images resolved, no overflow.

If `RenderSlides` returns an error, report it and stop — do NOT silently switch to python. The only
time the fallback below is allowed is when `RenderSlides` is genuinely not registered (older engine
without the tool) or the user explicitly needs an editable `.pptx`.

Service + theme + the 12-slide-type ↔ Marp-md mapping live in `slide-render/` (sibling of this
plugin) and `scripts/slides_yaml2marp.py`.

## Guardrails (read before rendering)
- Read the **compiled** `chNN.yaml`, never `.slides.md` — if stale, recompile with `slides_md2yaml.py`.
- Fail loudly if the YAML has no `slides`. Don't invent slides.
- Write only under `build/`. Never edit `media/` or chapter sources.
- **Never hand-roll a renderer** (no Pillow, no raw HTML-to-image, no custom python drawing). The
  approved renderer is `RenderSlides`. `slides2pptx.py` is fallback-only (see below).

---

# Fallback only: standalone PPTX (offline / editable deck required)

**Use this section ONLY when `RenderSlides` is unavailable OR the user explicitly asks for an
editable `.pptx`.** It's a python-pptx renderer with a built-in "Agentic Press" theme — lower design
ceiling than the Marp path and it needs LibreOffice for previews (flaky on macOS).

Preflight the python deps first (this checks python-pptx/pyyaml/Pillow + optional CLI tools):
```bash
python3 {skill_dir}/scripts/check_env.py   # add --json for machine-readable
```
Render the `.pptx`:
```bash
mkdir -p build/slides
python3 {skill_dir}/scripts/slides2pptx.py \
  media/slides/chNN.yaml -o build/slides/chNN.pptx \
  --book book.yaml --media-dir media/screenshots --media-dir media/generated
```
Custom theme: `--theme mytheme.json` (deep-merged) or `book.yaml → style.pptx_theme`. Shape:
`{ "palette": {"teal":"0F766E"}, "fonts": {"heading":"Prompt","body":"Sarabun"}, "sizes":{"title":34} }`.

Font-proof preview (bakes each slide to an image so it looks identical everywhere — needs `soffice`
+ `pdftoppm` + fontconfig):
```bash
python3 {skill_dir}/scripts/slides2preview.py \
  media/slides/chNN.yaml --book book.yaml \
  --media-dir media/screenshots --media-dir media/generated \
  --out build/slides --strict-fonts
```
Outputs: `chNN.pptx` (editable), `chNN-slides.pdf` (font-embedded), `preview/chNN/slide-*.png`,
`preview/chNN-contact.png` (QC contact sheet), `chNN-image.pptx` (font-proof, images + notes).
`--strict-fonts` aborts if a theme font resolves to a substitute (recommended). QC the contact sheet
with the Read tool before delivering.
