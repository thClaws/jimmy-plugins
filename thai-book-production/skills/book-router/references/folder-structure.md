# Book Project Layout — thai-book-production

**หลักการ:** 1 working folder = หนังสือ 1 เล่ม (ออกแบบสำหรับ Claude Cowork)
`book.yaml` ที่ root คือ single source of truth — ทุก skill อ่าน `layout:` จากไฟล์นี้เพื่อ resolve path
**ห้าม hardcode path** ในโค้ด/คำสั่ง ให้อ่านจาก manifest เสมอ เพื่อให้ย้าย/เปลี่ยนโครงได้ทีเดียว

## โครงสร้างมาตรฐาน

```
<book-slug>/                     ← Cowork working folder (1 เล่ม)
├── book.yaml                    ← manifest / single source of truth
│
├── outline/
│   ├── outline.md               ← ภาค → บท → subtopics       (outline-planner)
│   └── plan.md                  ← learning objectives + page plan
│
├── refs/                        ← (get-book-ref)
│   ├── docs/                    ← official documentation (.md)
│   └── blogs/                   ← blog posts (.md)
│
├── chapters/                    ← source of truth ของ prose
│   ├── ch01.md                  ← (write-book-chapter)
│   └── chNN.md
│
├── media/
│   ├── slides/
│   │   ├── chNN.slides.md       ← source (แก้มือ) — authoring surface
│   │   └── chNN.yaml            ← build artifact (compile จาก .slides.md; ห้ามแก้มือ)
│   ├── screenshots/             ← ภาพจริงจับจากโปรแกรม ({{screenshot:...}})
│   │   ├── inventory.json       ← registry ภาพจริง (list/mockup-screenshot)
│   │   └── *.png
│   └── generated/               ← ภาพ AI สร้างด้วย Pinn.ai ({{image:...}})
│       ├── inventory.json       ← registry ภาพ AI (id, caption, prompt, model, status) — generate-image
│       └── <id>.png
│
├── apparatus/
│   ├── glossary.md              ← (index-glossary)
│   └── index.md
│
├── translations/
│   └── <lang>/chapters/chNN.md  ← (translate)  เช่น translations/en/chapters/ch01.md
│
├── assets/
│   ├── cover-front.png          ← (cover-design)
│   └── cover-wrap.pdf
│
├── reports/                     ← QC reports ทุกชนิดอยู่ที่นี่ที่เดียว
│   ├── chNN.audit.md            ← audit-chapter   → fix-chapter อ่านตัวนี้
│   ├── chNN.proofread.md        ← proofread log
│   └── chNN.yaml-audit.md       ← audit-yaml
│
└── build/                       ← artifact สุดท้าย (สร้างใหม่ได้เสมอ)
    ├── slides/chNN.pptx         ← (build-slides-pptx) สไลด์ PowerPoint ต่อบท
    ├── slides/preview/chNN/*.png ← (slides2preview) ภาพสไลด์รายใบ + contact sheet
    ├── audio/chNN/slide-NN.wav   ← (generate-tts) เสียงพากย์ต่อสไลด์ + manifest.json
    ├── video/chNN.mp4            ← (build-chapter-video) วิดีโอบท
    ├── <slug>.epub              ← (build-epub-pdf)
    ├── <slug>.pdf
    └── build-report.md
```

## กติกาการตั้งชื่อ

- บท: `ch{NN}.md` — zero-padded 2 หลัก เรียงลำดับได้ (`ch01`, `ch02`, … `ch12`)
- slides: `ch{NN}.yaml` ใน `media/slides/`
- report: `ch{NN}.<kind>.md` ใน `reports/` โดย kind ∈ {audit, proofread, yaml-audit}
- translation: `translations/<lang>/chapters/ch{NN}.md` (lang = ISO 639-1: en, ja, …)
- ภาพจริง (screenshot): ไฟล์ `.png` ใน `media/screenshots/` — อ้างในบทด้วย `{{screenshot:ไฟล์|คำอธิบาย}}`
- ภาพ AI (generated): ไฟล์ `<id>.png` ใน `media/generated/` — อ้างในบทด้วย `{{image:id|คำอธิบาย}}`
  โดย `generate-image` (Pinn.ai) เป็นตัวสร้าง; LLM แต่ง prompt ตอน generate
- ทุก path config อยู่ใน `book.yaml → layout:` — ค่าข้างบนคือ default หากไม่ override

## การตรวจว่าอยู่ใน book folder หรือไม่

มี `book.yaml` ที่ working folder root = ใช่ ไม่มี = ให้ `book-router` scaffold ใหม่ ห้ามเดา path เอง

## Extensibility

เพิ่มเฟส/artifact ใหม่ในอนาคต = เพิ่ม key ใน `layout:` + โฟลเดอร์ใหม่ ไม่กระทบของเดิม
เพราะ skill อ่าน path จาก manifest ไม่ผูกกับชื่อโฟลเดอร์ตายตัว
