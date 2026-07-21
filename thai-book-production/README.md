# thai-book-production

Plugin เดียวครอบทั้ง lifecycle การผลิตหนังสือ technical/tutorial ออกแบบสำหรับ **Claude Cowork**
โดยยึด **1 working folder = หนังสือ 1 เล่ม** ภาษาไทยเป็นหลัก คงศัพท์เทคนิคเป็นภาษาอังกฤษ

## หลักการออกแบบ

1. **1 folder ต่อ 1 เล่ม** — เปิด folder ใน Cowork แล้วทำงานได้ทั้ง pipeline
2. **`book.yaml` = single source of truth** — ทุก skill อ่าน path จาก `layout:` ไม่ hardcode
   เปลี่ยนโครงที่เดียวมีผลทั้งระบบ และเพิ่มเฟสใหม่ในอนาคตได้โดยไม่กระทบของเดิม
3. **`book-router` เป็น orchestrator** — scaffold folder ใหม่, ดู state, บอกเฟสถัดไป, ส่งต่อ

## โครงสร้าง folder

```
<book-slug>/
├── book.yaml            manifest (path + chapter registry + targets)
├── outline/             outline.md, plan.md
├── refs/                docs/, blogs/
├── chapters/            chNN.md            ← source of truth
├── media/               slides/chNN.slides.md→chNN.yaml; screenshots/ (จริง) + generated/ (AI) แต่ละที่มี inventory.json
├── apparatus/           glossary.md, index.md
├── translations/        <lang>/chapters/chNN.md
├── assets/              cover-front.png, cover-wrap.pdf
├── reports/             chNN.audit.md, chNN.proofread.md, chNN.yaml-audit.md
└── build/               <slug>.epub, <slug>.pdf, build-report.md
```

สเปกเต็ม: `skills/book-router/references/folder-structure.md`
template: `skills/book-router/references/book.yaml.template`

## Pipeline

```
PLAN        get-book-ref (seed) → outline-planner → get-book-ref (targeted)   ↺ loop
            ✋ HUMAN: อนุมัติ outline (outline/APPROVED.md) ก่อนเริ่มเขียน
WRITE       write-book-chapter + generate-image (AI) + mockup-screenshot (placeholder)
QC          audit-chapter  →  proofread  →  fix-chapter      (วนต่อบท)
            ✋ HUMAN: ปรับเนื้อหา · จับภาพจริงแทน mockup (inventory status: real)
MEDIA       create-book-yaml (สไลด์+VO script) → audit-yaml → build-slides-pptx (ภาพสไลด์)
            → generate-tts (Pinn.ai เสียงพากย์) → build-chapter-video (ffmpeg วิดีโอบท)
APPARATUS   index-glossary
LOCALIZE    translate
BUILD       cover-design  →  build-epub-pdf
```
> PLAN เป็นลูป: ดึง ref แกนก่อน → outline ตั้งบนของจริง → ดึง ref เจาะช่องว่าง

## Skills (18)

| Skill | เฟส | สถานะ |
|-------|-----|-------|
| book-router | orchestrator | ✅ เขียนเต็ม (scaffold + state + routing + book-level) |
| outline-planner | plan | ✅ เดิม |
| get-book-ref | plan | ✅ เดิม |
| write-book-chapter | write | ✅ เดิม (+ `{{image:...}}` สำหรับภาพ AI) |
| audit-chapter | qc | ✅ เขียนเต็ม (process + page-est + report) |
| proofread | qc | ✅ เดิม |
| fix-chapter | qc | ✅ เดิม |
| index-glossary | apparatus | ✅ เขียนเต็ม (EN A–Z + TH ก–ฮ, section locator) |
| create-book-yaml | media | ✅ MD authoring → compile YAML (gen .slides.md → chNN.yaml) |
| audit-yaml | media | ✅ ตรวจ/แก้ที่ .slides.md → recompile YAML |
| mockup-screenshot | media | ✅ ภาพจริง (`{{screenshot:}}`) เท่านั้น |
| generate-image | media | ✅ ภาพ AI content-first (Pinn.ai nano-banana-2 `{{image:}}`) — infographic/diagram, ตัวอักษรไทย+อังกฤษในภาพ |
| build-slides-pptx | media | ✅ standalone .pptx + **slides2preview** (font-proof: pptx→pdf→png→contact→image-pptx) |
| generate-tts | media | ✅ เสียงพากย์ต่อสไลด์ (Pinn.ai text2speech) → build/audio + manifest |
| build-chapter-video | media | ✅ deterministic ffmpeg: ภาพสไลด์+เสียง → build/video/chNN.mp4 |
| translate | localize | ✅ เขียนเต็ม (TM + preserve non-prose) |
| cover-design | build | ✅ nano-banana-2 (ปกตรง+รอยสัน+ชื่อไทยบนปก) + Canva/programmatic |
| build-epub-pdf | build | ✅ เขียนเต็ม (Pandoc epub + xelatex pdf + epubcheck) |

ทุก skill มีส่วน **## Paths** ที่ชี้ไปยัง `book.yaml → layout:` — path เดิมแบบ `book/chapters/`
ถูกแทนด้วยโครงใหม่ทั้งหมดแล้ว โครงบท = `ch01.md`; toolchain (cover/build) override ได้ที่
`book.yaml → cover:` / `build:`

## Requirements

- **Pinn.ai MCP connector** (เชื่อมใน Cowork ของผู้ใช้เอง — ไม่ได้ bundle มากับ plugin):
  ใช้โดย `generate-image` + `cover-design` (`text2image`, nano-banana-2) และ `generate-tts`
  (`text2speech`) — ต้องมีบัญชี/credits ของตัวเอง ถ้าไม่ได้เชื่อม: ภาพ AI จะค้างสถานะ `needed`,
  ปกใช้ Canva/programmatic แทนได้, TTS จะรายงานว่าขาดแล้วหยุด
- **Python libs**: `pyyaml`, `python-pptx`, `Pillow` — ตรวจด้วย
  `skills/build-slides-pptx/scripts/check_env.py` (บอกคำสั่ง pip ให้เมื่อขาด)
- **CLI (เฉพาะเฟสที่ใช้)**: `soffice` + `pdftoppm` + `fc-match` (render/preview สไลด์),
  `ffmpeg` (วิดีโอ), `pandoc` + `xelatex` + `epubcheck` (ประกอบเล่ม)

## ติดตั้ง & ทดสอบ (local)

Plugin นี้ install ได้เลยผ่าน local marketplace (`.claude-plugin/marketplace.json` มากับ plugin แล้ว
โดย marketplace ชื่อ `thaigpt`, plugin ชื่อ `thai-book-production`):

```
/plugin marketplace add /Users/jimmy/__2026/cw/book-production/thai-book-production
/plugin install thai-book-production@thaigpt
```

วนเทส (หลังแก้ไฟล์ใน plugin):
```
/plugin marketplace update thaigpt      # ดึงการเปลี่ยนแปลงล่าสุด
```

ปิด/ถอน:
```
/plugin disable thai-book-production@thaigpt
/plugin marketplace remove thaigpt
```

> หมายเหตุ: install จาก path เปล่าไม่ได้ — ต้องผ่าน marketplace catalog. `source: "./"` หมายถึง
> marketplace root กับ plugin เป็นโฟลเดอร์เดียวกัน (ตัว `thai-book-production/` นี้เอง).
> compiler สไลด์ใช้ `pyyaml` — ถ้าเครื่องไหนไม่มี: `pip install pyyaml --break-system-packages`.

## สถานะ (v1.0.0 — RELEASE)
- ✅ ครบ 18 skills — ครอบ workflow เต็ม: refs→manifest→outline→✋approve→บท+ภาพ→✋ภาพจริง→สไลด์+VO→render→TTS→วิดีโอ→ปก (nano-banana-2)→epub/pdf
- ✅ decisions 10 ข้อเคาะแล้ว (ดู SPEC §8 Decisions log)
- ✅ **PPTX renderer standalone**: `build-slides-pptx` + `scripts/slides2pptx.py` (python-pptx) —
  chNN.yaml → branded .pptx ไม่พึ่ง repo นอก, ครบ 12 slide type, ฟอนต์ Prompt+Sarabun bundle, custom theme ได้
  - ✅ `slides2preview.py` — font-proof pipeline: bake ทุกสไลด์เป็นรูป (pptx→pdf→png→contact sheet→image-pptx) + ด่านตรวจฟอนต์ (fc-match/--strict-fonts) เปิดที่ไหนก็เหมือนกัน
- ✅ preflight `check_env.py` — ตรวจ python lib (pyyaml/python-pptx/Pillow) + CLI ก่อนรัน, warn + บอกคำสั่ง pip
- ✅ PLAN เป็นลูป: get-book-ref (seed) → outline-planner → get-book-ref (targeted)
- ✅ สไลด์ authoring = Markdown (`chNN.slides.md`) → compile เป็น `chNN.yaml` (build artifact)
  - รูปแบบ: `skills/create-book-yaml/references/slide-md-format.md`
  - **compiler จริง (tested):** `skills/create-book-yaml/scripts/slides_md2yaml.py`
    รองรับครบ 12 slide type, fail ดังพร้อมชี้ slide ที่ผิด, `--check` mode
- ✅ ภาพ 2 ประเภท แยกโฟลเดอร์: `media/screenshots/` (จริง, `{{screenshot:}}`) +
  `media/generated/` (AI ผ่าน Pinn.ai nano-banana-2, `{{image:}}`, content-first infographic/diagram — render ตัวอักษรไทย+อังกฤษได้)
- ✅ ตอนสร้างสไลด์ preserve ทุกรูปจากบท: `{{screenshot:}}` และ `{{image:}}` → เป็น slide ครบ ไม่ตกหล่น (renderer ฝังไฟล์จริง)
- เหลือขั้น validate จริงตอนใช้งาน: install ใน Cowork แล้วรันกับหนังสือจริง 1 เล่ม (end-to-end)
