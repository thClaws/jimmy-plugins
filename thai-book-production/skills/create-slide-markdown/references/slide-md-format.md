# Markdown Slide Format — Authoring Surface (`.slides.md`)

**ทำไมมีไฟล์นี้:** `chNN.yaml` เป็น *build artifact* ที่ pipeline (build-slides-pptx / generate-tts / build-chapter-video) กิน —
มันแก้มือยากเพราะ YAML อ่อนไหวกับ indent, สไลด์เรียงตามตำแหน่ง (insert/delete แล้ว cascade),
และ `notes: |` block scalar พลาดง่าย **พื้นผิวที่มนุษย์แก้คือ `chNN.slides.md` ไฟล์นี้** แล้ว
`create-slide-yaml` compile เป็น `chNN.yaml` ให้ ไม่มีใครแก้ YAML ตรงๆ

**หลักการ:** ลำดับสไลด์ = ลำดับในเอกสาร → **insert/delete/reorder = ขยับบล็อกข้อความ ไม่มีเลข
ตำแหน่งให้ renumber** ข้อความอิสระ (notes) อยู่ใน fenced block ไม่แคร์ indent

---

## โครงไฟล์

ตัวอย่างข้างล่างใช้ `{slug}` / `{subject}` / `{title}` แทนค่าจริง — ค่าพวกนี้มาจาก `book.yaml`
(`book.slug`, `book.subject`, `book.title`) เสมอ **ห้ามฝังชื่อหนังสือหรือชื่อผลิตภัณฑ์ของเล่มอื่น
ลงในเทมเพลต** ที่ต้องดูคือ *โครง* ไม่ใช่ข้อความ

```markdown
---
book: {slug}                 # → meta.book  (จาก book.yaml → book.slug)
chapter: 1                   # → meta.chapter (int, ใช้ตั้งชื่อ output)
title: ทำไมต้อง {subject}      # → meta.title
subtitle: {title}            # → meta.subtitle (ชื่อเล่มบนปก)
---

<!-- slide: cover chapter="บทที่ 1" -->
# ทำไมต้อง {subject}
## {title}

::: notes
พิมพ์ speaker note ได้อิสระหลายบรรทัด ไม่ต้องกังวลเรื่องย่อหน้า
เพราะอยู่ใน fenced block ::: ปิดท้ายด้วย :::
:::

---

<!-- slide: content id=what-is-it -->
## {subject} คืออะไร

- ประโยคเดียวว่ามันคืออะไร
- อีกบรรทัดว่าใช้ทำอะไรได้

::: notes
...
:::
```

> **ทุกสไลด์ต้องมี `::: notes` ของตัวเอง** — compiler fail ถ้าขาด ตัวอย่างสั้น ๆ ข้างล่างตัด
> `::: notes` ออกเพื่อให้เห็นโครงชัด แต่ของจริงต้องมีทุกอัน

**กติกาแยกสไลด์:** บรรทัดที่มีแค่ `---` คั่นระหว่างสไลด์ บล็อก `---...---` แรกสุดคือ deck
front-matter (→ `meta`)

**Directive ต่อสไลด์:** บรรทัดแรกของแต่ละสไลด์เป็น HTML comment
`<!-- slide: TYPE [id=slug] [key="value"] ... -->`
- `TYPE` = ชนิดสไลด์ (ดูตารางล่าง)
- `id=` (optional) = ชื่อคงที่ของสไลด์ ใช้ล็อกชื่อ output (`ch01-<id>.wav`) ไม่ให้ขยับเวลา insert
- scalar field อื่นๆ (เช่น `style=`, `number=`, `numbered`, `duration=`, `screenshot=`) วางที่นี่
  บรรทัดเดียว **ห้ามมี multiline** → เลี่ยงความเปราะของ YAML

**Notes / B-roll:** ใช้ fenced div
```markdown
::: notes
ข้อความ TTS อิสระ
:::

::: broll
- screen | ภาพหน้าจอ chat | 0:15
- motion | ซูมเข้าปุ่ม + | 0:22
:::
```

---

## Mapping ต่อ slide type

| type | body ใน MD | scalar ใน directive |
|------|-----------|---------------------|
| `cover` | `# title` + `## subtitle` | `chapter="บทที่ 1"` |
| `quote` | blockquote `> ...`; บรรทัดขึ้นต้น `—` = attribution | — |
| `section` | `## title` + `### subtitle`(opt) + การ์ดเป็น `::: card` (2–5) | `number="1.1"` |
| `content` | `## title` + `### subtitle`(opt) + bullet `- ...` | `numbered` (ถ้าเป็นเลข) |
| `two_column` | `## title` + `::: left header="..."` / `::: right header="..."` | — |
| `timeline` | `## title` + **ตาราง** `year \| title \| body` (3–5 แถว) + `::: callout`(opt) | — |
| `process` | `## title` + ลิสต์เลข `1. **title** — body` (2–6) | `footer="..."` |
| `table` | `## title` + ตาราง Markdown ตรงๆ | — |
| `callout` | `## title` + แต่ละบรรทัด/บูลเล็ต = ข้อ (1. 2. 3.) | `style=tip\|warning\|concept` |
| `demo` | `## subtitle` (title ตายตัวเป็น "DEMO") | — |
| `screenshot` | `## title`(opt) + `### subtitle`(opt) + ย่อหน้า = description | `screenshot="f.png"` หรือ `image="/path"` |
| `video_demo` | `## title` + ย่อหน้า = description | `duration="2:30"` |

### ตัวอย่างชนิดที่มีโครงย่อย

**two_column**
```markdown
<!-- slide: two_column -->
## เทียบวิธีทำงาน

::: left header="แบบเดิม"
- เปิดหลายแอป
- ก็อปวางไปมา
:::
::: right header="แบบใหม่"
- สั่งทีเดียวจบ
- ได้ไฟล์จริง
:::
```

**timeline** (ตาราง = แก้ง่ายสุด)
```markdown
<!-- slide: timeline -->
## เส้นทางของผู้ช่วย AI

| year | title | body |
|------|-------|------|
| 2021 | ยุคที่ 1 | ทำได้แค่อย่างเดียว |
| 2023 | ยุคที่ 2 | ต่อกับเครื่องมืออื่นได้ |
| 2025 | ยุคที่ 3 | ลงมือทำงานจริงแทนเรา |

::: callout title="สังเกต"
- แต่ละก้าวเพิ่ม "การลงมือทำ"
:::
```

**section** (การ์ด)
```markdown
<!-- slide: section number="1.1" -->
## ภาพรวม
### สามสิ่งที่ต้องรู้

::: card label="ข้อ 1" title="ไฟล์จริง"
ทำงานกับไฟล์ในเครื่องได้ตรงๆ
:::
::: card label="ข้อ 2" title="สั่งเป็นภาษาคน"
ไม่ต้องเขียนโค้ด
:::
```

**callout**
```markdown
<!-- slide: callout style=tip -->
## เคล็ดลับ
- ใส่ตัวอย่างจริงเสมอ
- บอกบริบทให้ครบ
- ตรวจงานก่อนส่ง
```

---

## ความสัมพันธ์กับ `yaml-format.md` + compiler

`slide-md-format.md` (ไฟล์นี้) = **พื้นผิว authoring** — `yaml-format.md` = **สเปกของ build
artifact** ที่ pipeline กิน field ใดที่ directive/บอดี้ MD ไม่ได้ระบุ → ใช้ default ตาม `yaml-format.md`

**compiler (deterministic):** `scripts/slides_md2yaml.py` แปลง `.slides.md` → `.yaml` ตามสเปกนี้
```bash
python3 <plugin>/skills/create-slide-yaml/scripts/slides_md2yaml.py ch01.slides.md
python3 .../slides_md2yaml.py ch01.slides.md --check      # validate อย่างเดียว
```
> `<plugin>` = พาธจริงของปลั๊กอิน ไฟล์นี้ถูกอ่านดิบ ๆ จึงไม่มีการแทนค่าให้ — เอาพาธเต็มที่ resolve
> แล้วจาก `create-slide-yaml/SKILL.md` (มันใช้ `{skill_dir}` ซึ่ง engine แทนค่าตอนโหลด skill)
สคริปต์ fail ดังพร้อมชี้ slide ที่ผิด (ไม่มี directive / `:::` ไม่ปิด / ไม่มี notes / type ไม่รู้จัก)

## กติกา (สำหรับ compiler + audit)
- 1 สไลด์ = 1 บล็อกระหว่าง `---` เรียงตามลำดับเอกสาร
- directive ต้องเป็นบรรทัดแรกของบล็อก และมี `TYPE` เสมอ
- `::: name` ต้องปิดด้วย `:::` ทุกอัน (notes, broll, left, right, card, callout, event)
- ไม่มี multiline ใน directive — ข้อความยาวไปอยู่ในบอดี้/`::: notes`
- `id=` ถ้ามี ต้อง unique ภายในบท (compiler ใช้ตั้งชื่อ output; ไม่มี → ใช้ลำดับ `slide-NN`)
