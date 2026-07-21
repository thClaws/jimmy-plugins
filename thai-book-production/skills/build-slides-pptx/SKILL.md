---
name: build-slides-pptx
description: >
  Render a chapter's slide YAML into a branded PowerPoint (.pptx) — fully STANDALONE, no external
  pipeline required. Uses the bundled `scripts/slides2pptx.py` (python-pptx) with a built-in
  "Agentic Press" design theme (Prompt + Sarabun fonts, navy/parchment/teal/gold palette, layouts
  for all 12 slide types). Use when the user asks to "สร้าง pptx", "ทำสไลด์ PowerPoint", "build pptx",
  "render slides", "แปลง yaml เป็น pptx", "ออกไฟล์สไลด์", or when the router reaches slide rendering.
  A custom theme can be supplied later via `--theme` or `book.yaml → style.pptx_theme`.
  Also bundles `scripts/slides2preview.py` — a one-shot preview/font-proof pipeline (yaml → pptx →
  PDF → per-slide PNGs → contact sheet → image-pptx) with a font guardrail; use it when the user asks
  for "preview สไลด์", "gen preview", "สไลด์แบบรูปภาพ", "image pptx", or reports fonts looking wrong
  on their machine.
---

## Paths (thai-book-production layout)

หนึ่ง working folder = หนังสือหนึ่งเล่ม Resolve ทุก path จาก `book.yaml → layout:` ที่ root
ของ folder — **ห้าม hardcode** ถ้าไม่มี `book.yaml` แปลว่าไม่ได้อยู่ใน book folder ให้ให้
`book-router` scaffold ก่อน ค่า default:

| what | path |
|------|------|
| chapters | `chapters/chNN.md` |
| slides | `media/slides/chNN.slides.md` → `chNN.yaml` (build artifact) |
| screenshots (จริง, จับจากโปรแกรม) | `media/screenshots/` (+ `inventory.json`) |
| generated (AI, Pinn.ai) | `media/generated/` (+ `inventory.json`) |
| **slides pptx (output)** | `build/slides/chNN.pptx` |
| reports (QC ทุกชนิด) | `reports/chNN.audit.md`, `reports/chNN.proofread.md`, `reports/chNN.yaml-audit.md` |
| build output | `build/` |


# Build Slides PPTX — Standalone Renderer

Renders `media/slides/chNN.yaml` (the compiled slide build artifact) into a branded `.pptx`.
**No external `yaml2pptx.py` / template repo needed** — the whole design lives in
`scripts/slides2pptx.py` and the bundled fonts.

## Inputs & output
- Input: `{slides}/chNN.yaml` (produced by `create-book-yaml` → `slides_md2yaml.py`).
- Output: `{build}/slides/chNN.pptx` (create the folder if missing).
- Images: `{{screenshot:}}`→`{screenshots}/`, `{{image:}}`→`{generated}/` are resolved by filename.

## Run
**Preflight first** — check the machine has the required Python libs and warn before doing work:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/build-slides-pptx/scripts/check_env.py
# exits 1 and prints the exact `pip install ...` line if anything REQUIRED is missing.
# If it fails, install what it lists, then continue. Add --json for machine-readable output.
```
Then render:
```bash
mkdir -p build/slides
python3 ${CLAUDE_PLUGIN_ROOT}/skills/build-slides-pptx/scripts/slides2pptx.py \
  media/slides/chNN.yaml -o build/slides/chNN.pptx \
  --book book.yaml \
  --media-dir media/screenshots --media-dir media/generated
```
Requires `python-pptx` and `pyyaml` (Pillow recommended). The shared preflight
`check_env.py` covers every plugin script's deps (pyyaml, python-pptx, Pillow) plus optional
CLI tools (curl, soffice, pandoc, xelatex, epubcheck) — run it any time to verify the environment.

## Design theme (default = in code)
The default **Agentic Press** theme is defined inside `slides2pptx.py`:
- Fonts: **Prompt** (headings) + **Sarabun** (body) — bundled in `assets/fonts/`. Thai is written to
  the complex-script slot so it renders correctly. If those fonts aren't installed on the machine that
  opens the file, the app substitutes — install them for pixel-accurate output (or embed, see below).
- Palette: `bg_dark #0D1B2A`, `parchment #F8F6F0`, `teal #007A6E`, `gold #B8860B`, card `#FFFFFF`,
  navy `#16324F`, red `#CC3333`.
- Backgrounds: dark for `cover/quote/demo/video_demo`; parchment for the rest.
- Slide size 13.333×7.5in (16:9). Speaker `notes` are written into each slide's notes pane.
- Text-fit guards: bullets capped at 6, table rows at 8, long titles auto-shrink.

Covers all 12 types: cover, quote, section, content, two_column, timeline, process, table, callout,
demo, screenshot, video_demo.

## Custom theme (hook — usable now, expand later)
Override any token without touching the script:
- `--theme mytheme.json` — deep-merged over the default. Shape:
  ```json
  { "palette": {"teal":"0F766E","gold":"CA8A04"},
    "fonts": {"heading":"Prompt","body":"Sarabun"},
    "sizes": {"title":34} }
  ```
- or `book.yaml → style.pptx_theme:` — an inline dict, or a path to a JSON theme. Same shape.

(Planned v-next: full custom *template* .pptx swap + font embedding for portable decks.)

## Preview & font-proof pipeline (`slides2preview.py`)

**ปัญหาที่แก้:** `.pptx` เก็บแค่*ชื่อ*ฟอนต์ — เครื่องที่ไม่มีฟอนต์นั้นจะสุ่มฟอนต์อื่นมาแทนแบบเงียบๆ
(PowerPoint บน Mac, ตัว preview ของแอป, LibreOffice — แทนคนละตัวกัน) เด็คเดียวกันจึงหน้าตาไม่เหมือนกัน
สคริปต์นี้เรนเดอร์*ครั้งเดียว*ด้วยฟอนต์บนเครื่อง build แล้ว bake แต่ละสไลด์เป็นรูปภาพ → เปิดที่ไหนก็เหมือนกัน

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/build-slides-pptx/scripts/slides2preview.py \
  media/slides/chNN.yaml --book book.yaml \
  --media-dir media/screenshots --media-dir media/generated \
  --out build/slides --strict-fonts
```

Outputs (ต่อ input `chNN.yaml`):
| file | คืออะไร |
|------|---------|
| `build/slides/chNN.pptx` | native deck (แก้ไขได้ — แสดงถูกเฉพาะเครื่องที่มีฟอนต์) |
| `build/slides/chNN-slides.pdf` | PDF ฝังฟอนต์ ตรงดีไซน์ 100% ทุกเครื่อง |
| `build/slides/preview/chNN/slide-*.png` | ภาพ preview รายสไลด์ (default 150dpi) |
| `build/slides/preview/chNN-contact.png` | contact sheet ไว้ QC ทั้งเด็คในภาพเดียว |
| `build/slides/chNN-image.pptx` | **font-proof deck** — ทุกสไลด์เป็นรูป + speaker notes ครบ |

Flags: `--dpi N` (ความละเอียด PNG), `--strict-fonts` (fail ถ้าฟอนต์ในธีมไม่มีจริง — **แนะนำให้ใส่เสมอ**),
`--skip-image-pptx`, `--skip-contact`, `--skip-native`

**Font guardrail:** ก่อนเรนเดอร์ สคริปต์เช็คทุกฟอนต์ในธีมผ่าน `fc-match` — ถ้าชื่อฟอนต์ resolve
ไปเป็นฟอนต์อื่น (เช่นไฟล์ฟอนต์โหลดมาเสีย/ยังไม่ได้ติดตั้ง) จะเตือนดังๆ หรือ abort ทันทีเมื่อใช้
`--strict-fonts` ป้องกันการ bake ภาพด้วยฟอนต์ fallback ผิดตัวโดยไม่รู้ตัว

**QC ทุกครั้ง:** หลังรันเสร็จ ให้เปิด `preview/chNN-contact.png` ดูด้วยตา (Read tool) ก่อนส่งมอบเสมอ —
เช็คฟอนต์ตรงดีไซน์ รูป resolve ถูกไฟล์ ข้อความไม่ล้นกรอบ

ต้องมีเพิ่มจาก renderer หลัก: `soffice` (libreoffice) + `pdftoppm` (poppler-utils) + fontconfig

## Guardrails
- Reads the **compiled** `chNN.yaml`, never `.slides.md` — if the YAML is stale, recompile first
  (`slides_md2yaml.py`).
- Fail loudly if the YAML has no `slides`. Don't invent slides.
- Writes only under `{build}/`. Never edits `media/` or chapter sources.
