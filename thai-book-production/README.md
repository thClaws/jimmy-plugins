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
INIT        init-book (ไม่มี book.yaml → intake wizard: metadata + targets + style → scaffold)
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

## Skills (19)

| Skill | เฟส | สถานะ |
|-------|-----|-------|
| init-book | init | ✅ intake wizard (metadata + targets + style + cover) → เขียน book.yaml + scaffold → ส่งต่อ get-book-ref |
| book-router | orchestrator | ✅ เขียนเต็ม (state + routing + book-level; scaffold แยกไป init-book) |
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
| generate-image | media | ✅ ภาพ AI content-first (built-in `TextToImage` / Gemini nano-banana `{{image:}}`) — infographic/diagram, ตัวอักษรไทย+อังกฤษในภาพ; แทรก `![]()` preview ใต้ placeholder (คง placeholder) ให้รีวิวใน .md |
| build-slides-pptx | media | ✅ standalone .pptx + **slides2preview** (font-proof: pptx→pdf→png→contact→image-pptx) |
| generate-tts | media | ✅ เสียงพากย์ต่อสไลด์ (Pinn.ai text2speech) → build/audio + manifest |
| build-chapter-video | media | ✅ deterministic ffmpeg: ภาพสไลด์+เสียง → build/video/chNN.mp4 |
| translate | localize | ✅ เขียนเต็ม (TM + preserve non-prose) |
| cover-design | build | ✅ built-in `TextToImage` (Gemini nano-banana; ปกตรง+รอยสัน+ชื่อไทยบนปก) + Canva/programmatic |
| build-epub-pdf | build | ✅ เขียนเต็ม (Pandoc epub + xelatex pdf + epubcheck) |

ทุก skill มีส่วน **## Paths** ที่ชี้ไปยัง `book.yaml → layout:` — path เดิมแบบ `book/chapters/`
ถูกแทนด้วยโครงใหม่ทั้งหมดแล้ว โครงบท = `ch01.md`; toolchain (cover/build) override ได้ที่
`book.yaml → cover:` / `build:`

## Requirements

- **ภาพ AI = built-in `TextToImage`** (ใช้โดย `generate-image` + `cover-design`) — เปิดด้วย
  `imageToolsEnabled: true` ใน `.thclaws/settings.json` + provider key (`GEMINI_API_KEY`/
  `GOOGLE_API_KEY` หรือ `OPENAI_API_KEY`) หรือ thClaws Gateway key. **ไม่ต้องใช้ Pinn.ai สำหรับภาพ**
  ถ้ายังไม่เปิด: ภาพ AI จะค้างสถานะ `needed`, ปกใช้ Canva/programmatic แทนได้
- **Pinn.ai MCP connector — เฉพาะ TTS** (`generate-tts` → `text2speech`; ไม่มี built-in TTS ใน
  engine) ต้องมีบัญชี/credits ของตัวเอง ใน **thClaws** plugin นี้ **ประกาศ server `pinn-ai`
  (`https://pinn.ai/mcp`) ให้อัตโนมัติ** ในตัว manifest — ผู้ใช้เพียง authorize ครั้งเดียว
  (ดู "ติดตั้ง & auth ใน thClaws"). ถ้ายังไม่ auth: TTS จะรายงานว่าขาดแล้วหยุด
- **Python libs**: `pyyaml`, `python-pptx`, `Pillow` — ตรวจด้วย
  `skills/build-slides-pptx/scripts/check_env.py` (บอกคำสั่ง pip ให้เมื่อขาด)
- **CLI (เฉพาะเฟสที่ใช้)**: `soffice` + `pdftoppm` + `fc-match` (render/preview สไลด์),
  `ffmpeg` (วิดีโอ), `pandoc` + `xelatex` + `epubcheck` (ประกอบเล่ม)

## ติดตั้ง & auth ใน thClaws

thClaws อ่าน Claude Code plugin format ได้ตรงๆ (`.claude-plugin/plugin.json` + โฟลเดอร์ `skills/`)
แต่ **ไม่ใช้** `marketplace.json` — ติดตั้งผ่าน `/plugin install <git-url | .zip>` แทน โดยไม่ใส่
`--user` = ลงที่ **workspace folder ปัจจุบัน** (`<workspace>/.thclaws/plugins/`):

```
# 1) ติดตั้ง plugin (skills + commands ใช้ได้ทันทีใน session นี้)
/plugin install https://github.com/<org>/thai-book-production.git
#   หรือจาก local git repo:  /plugin install /path/to/thai-book-production
#   เจาะ subpath จาก monorepo:  <git-url>#<branch>:<subpath>

# 2) ภาพ AI = built-in TextToImage → เปิดใน .thclaws/settings.json + มี provider key/gateway
#    { "imageToolsEnabled": true }   (+ GEMINI_API_KEY/GOOGLE_API_KEY หรือ OPENAI_API_KEY หรือ gateway)

# 3) ⚠ restart thClaws — MCP server (pinn-ai, ใช้เฉพาะ TTS) spawn ตอน startup เท่านั้น
/quit        # แล้วเปิด thclaws ใหม่

# 4) authorize pinn-ai ครั้งเดียว — สำหรับ generate-tts (เปิด browser → วาง API key pk_... บนหน้า pinn.ai)
/mcp reauth pinn-ai
```

เสร็จแล้ว `generate-image` / `cover-design` ใช้ built-in `TextToImage` ได้ทันที (ไม่ผ่าน pinn-ai) ส่วน
`generate-tts` เรียก `mcp__pinn-ai__text2speech` — token เก็บฝั่ง pinn.ai (ไม่อยู่ใน plugin),
thClaws refresh ให้อัตโนมัติ ไม่ต้อง auth ซ้ำ

**เกร็ด**
- `/mcp` (ไม่มี arg) — ดูรายชื่อ MCP + สถานะ auth เช็คว่า `pinn-ai` ขึ้นและ authed แล้วหรือยัง
- ถ้าเรียก skill แล้วเจอ error ว่าไม่มี tool `mcp__pinn-ai__*` → ลืม restart ให้ `/quit` แล้วเปิดใหม่
- token เพี้ยน/หมดสิทธิ์ภายหลัง → รัน `/mcp reauth pinn-ai` ซ้ำได้ (invalidate ตัวเก่าให้เอง)
- ถ้าผู้ใช้ตั้ง MCP ชื่อ `pinn-ai` ไว้เองอยู่แล้ว: manifest ของ plugin จะถูก**ข้าม** (user config
  ชนะเมื่อชื่อซ้ำ) — auth เดิมไม่โดนแตะ
- **hosted/cloud runner** (headless ไม่มี browser): OAuth อาจทำไม่ได้ ต้อง pre-auth ไว้ก่อน —
  desktop (ตัวหลัก) ใช้ได้ปกติ
- ถอน: `/plugin remove thai-book-production`  ·  ปิดชั่วคราว: `/plugin disable thai-book-production`

## ติดตั้ง & ทดสอบ (Claude Cowork / Claude Code — local marketplace)

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

## สถานะ (v1.4.0 — RELEASE)
- ✅ **ภาพ AI → built-in `TextToImage`** — generate-image + cover-design เลิกใช้ Pinn.ai MCP,
  ใช้ tool ในตัว engine (Gemini `flash`/nano-banana, `pro`, gpt-image-2, qwen) เปิดด้วย
  `imageToolsEnabled: true` + provider key/gateway; ไฟล์เขียนที่ `output/…` แล้ว move ไป `media/generated/`.
  Pinn.ai เหลือใช้เฉพาะ `generate-tts` (ไม่มี built-in TTS)
- ✅ **generate-image preview** — หลัง gen ภาพ แทรก `![]()` (มี marker `<!-- gen-preview:id -->`) ใต้
  `{{image:id}}` placeholder ให้รีวิวภาพใน chapter .md ได้ทันที **โดยคง placeholder ไว้**; build-epub-pdf
  strip preview ก่อน resolve → ไม่ render ซ้ำ; create-book-yaml มองข้าม preview (นับเฉพาะ `{{...}}`)
- ✅ **init-book** — intake wizard แยกจาก book-router: เคาะ metadata + targets (epub/pdf/แปล) +
  style ภาพ/เสียง + ปก ตั้งแต่ต้น แล้ว scaffold; book-router เหลือหน้าที่ state+routing ล้วน (delegate scaffold)
- ✅ **thClaws-ready**: manifest ประกาศ MCP `pinn-ai` (`https://pinn.ai/mcp`, OAuth) อัตโนมัติ +
  README มีขั้นตอนติดตั้ง & auth สำหรับ thClaws (`/plugin install` → restart → `/mcp reauth pinn-ai`)
- ✅ ครบ 19 skills — ครอบ workflow เต็ม: init→refs→manifest→outline→✋approve→บท+ภาพ→✋ภาพจริง→สไลด์+VO→render→TTS→วิดีโอ→ปก (built-in TextToImage)→epub/pdf
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
  `media/generated/` (AI ผ่าน built-in `TextToImage` / Gemini nano-banana, `{{image:}}`, content-first infographic/diagram — render ตัวอักษรไทย+อังกฤษได้)
- ✅ ตอนสร้างสไลด์ preserve ทุกรูปจากบท: `{{screenshot:}}` และ `{{image:}}` → เป็น slide ครบ ไม่ตกหล่น (renderer ฝังไฟล์จริง)
- เหลือขั้น validate จริงตอนใช้งาน: install ใน Cowork แล้วรันกับหนังสือจริง 1 เล่ม (end-to-end)
