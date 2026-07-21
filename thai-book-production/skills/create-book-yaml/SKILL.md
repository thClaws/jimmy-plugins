---
name: create-book-yaml
description: >
  Convert book chapter Markdown files into slide decks: authoring Markdown (.slides.md) compiled to slide YAML for the in-plugin render/TTS/video pipeline.
  Use this skill whenever the user asks to create YAML slides, convert chapters to YAML, generate
  presentation YAML, or mentions "yaml-format", "slide YAML", "chapter to yaml", "สร้าง yaml",
  "แปลงบทเป็น yaml". Also trigger when the user references the book's YAML pipeline, video training
  slides, or wants to prepare chapters for the slide/video pipeline (build-slides-pptx / generate-tts / build-chapter-video).
  This skill reads chapter .md files and produces structured YAML with slide definitions and
  TTS-ready speaker notes. Even if the user just says "convert chapters" or "make slides from the book",
  use this skill.
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
| slides (source, แก้มือ) | `media/slides/chNN.slides.md` |
| slides (build artifact) | `media/slides/chNN.yaml` (compile จาก .slides.md) |
| screenshots (จริง, จับจากโปรแกรม) | `media/screenshots/` (+ `inventory.json`) |
| generated (AI, Pinn.ai) | `media/generated/` (+ `inventory.json`) |
| reports (QC ทุกชนิด) | `reports/chNN.audit.md`, `reports/chNN.proofread.md`, `reports/chNN.yaml-audit.md` |
| apparatus | `apparatus/glossary.md`, `apparatus/index.md` |
| translations | `translations/<lang>/chapters/chNN.md` |
| assets | `assets/` |
| build output | `build/` |


# Create Book YAML — Chapter-to-Video-Course Conversion

## Your Role

You are a **professional online course instructor** converting a book chapter into a structured video lesson. You are NOT a slide-maker — you are a **curriculum designer** who thinks about learning outcomes, pacing, and audience comprehension.

Your audience: Thai business professionals (managers, analysts, marketers, freelancers) who are NOT programmers. They learn by watching video lessons at their own pace. Every slide must earn its place — if a slide doesn't teach something new, cut it.

## Overview

This skill converts book chapter Markdown files into a video lesson. Each chapter becomes typed slides with Thai-language voice-over scripts (speaker notes) designed for TTS narration.

**Two artifacts — แก้มือที่ Markdown เท่านั้น:**
1. **`media/slides/chNN.slides.md`** — *authoring surface* (สิ่งที่มนุษย์แก้). รูปแบบตาม
   `references/slide-md-format.md`: สไลด์คั่นด้วย `---`, directive `<!-- slide: TYPE -->`,
   notes เป็น `::: notes` block. insert/edit/delete = ขยับบล็อกข้อความ ไม่มีเลขตำแหน่งให้ renumber.
2. **`media/slides/chNN.yaml`** — *build artifact* ที่ compile จาก `.slides.md` ตาม
   `references/yaml-format.md` **ห้ามแก้มือ** — แก้ที่ `.slides.md` แล้ว compile ใหม่.

ในโหมด "generate แล้วจูนต่อ": skill นี้ generate `.slides.md` จากบท → ผู้ใช้จูน `.slides.md`
→ compile เป็น `.yaml` The compiled YAML is rendered by:
- **`build-slides-pptx`** (in-plugin, standalone) — `chNN.yaml` → branded `.pptx` (no external repo)
- **`generate-tts`** (in-plugin, Pinn.ai text2speech) — per-slide voice-over WAV จาก notes
- **`build-chapter-video`** (in-plugin, ffmpeg) — สไลด์+เสียง → วิดีโอทั้งบท

## Project Folder Structure

**IMPORTANT:** Use these exact paths. Do NOT waste turns searching — the structure is fixed.

First, find the workspace root. Use `Glob` with pattern `**/chapters/ch*.md` to locate it. Once you find one file, the rest follows.

```
<book-folder>/                        ← book working folder (book.yaml at root)
├── outline/outline.md + plan.md      ← outline + learning objectives
├── refs/docs/ + refs/blogs/          ← reference material (enrich speaker notes)
├── chapters/chNN.md                  ← source chapters to convert
├── media/slides/
│   ├── chNN.slides.md                ← OUTPUT: authoring surface (this skill writes)
│   └── chNN.yaml                     ← OUTPUT: compiled build artifact
└── media/screenshots/ (+ info.md/index.md, inventory.json) · media/generated/
```

Read the YAML format specification (bundled in this skill):
```
Read: ${CLAUDE_PLUGIN_ROOT}/skills/create-book-yaml/references/yaml-format.md
```
This file defines every slide type, their fields, and the design system. You need it to produce valid output.

## Conversion Process

### Step 1: Read the Chapter and Understand the Lesson

Read the target chapter Markdown from `chapters/`. As you read, think like a course instructor preparing a lesson plan:

- **What's the learning goal?** After watching this lesson, what should the learner be able to do?
- **What are the key concepts?** List 3-5 things the learner MUST understand
- **What's the logical progression?** Which concept must come before which?
- **Where are the screenshots?** These are your "show, don't tell" moments — plan to place them right after the concept they illustrate

Extract from the chapter:
- Chapter number and title (from `# บทที่ N: ...`)
- All section headings (`## N.X ...`) — these become your lesson segments
- Image placeholders — **build a complete list of BOTH kinds, in order**:
  `{{screenshot:filename|description}}` (real UI, in `media/screenshots/`) and
  `{{image:id|caption}}` (AI figure, in `media/generated/<id>.png`). **Every image in the chapter
  must be preserved into the deck — don't drop any.**
- Tips, warnings, comparisons — these become callouts or two-column slides
- The chapter summary and hands-on project

**For short chapters (under 200 lines):** Read the book outline (`outline/outline.md`) and reference docs from `refs/docs/` to get deeper material for speaker notes. The chapter gives structure; the reference docs give depth.

### Step 2: Design the Learning Sequence

**Think like a course instructor, not a slide-maker.** Don't just convert sections into slides 1:1. Instead, design a learning path:

1. **Identify the chapter's learning goal** — What should the learner be able to DO after this lesson? (e.g., "Set up Connectors and use them to automate email workflows")
2. **Sequence for understanding** — Arrange slides so each builds on the previous one. The learner should never see a concept before its prerequisites are explained.
3. **Pace for comprehension** — One key idea per slide. If a section has 3 important concepts, that's 3 slides — not 1 cramped slide with 3 ideas.
4. **Use screenshots as proof points** — Place screenshot slides right after the concept they demonstrate, so the learner sees "here's the idea" → "here's what it looks like in practice".
5. **End each section with a takeaway** — Before moving to the next section, give the learner a mental anchor (a callout, a summary bullet, or a bridge in the speaker notes).

Target **15-25 slides per chapter** — enough to cover every section without rushing. One key idea per slide.

Here's how chapter elements map to slide types:

| Chapter Element | Slide Type | When to Use |
|----------------|------------|-------------|
| Chapter title + opening story | `cover` | Always the first slide |
| `## N.X Section Title` | `section` | Section divider with 2-5 summary cards |
| Bullet points or key facts | `content` | General information slides |
| Before/after, pros/cons, two sides | `two_column` | Side-by-side comparison |
| Step-by-step instructions | `process` | Numbered workflow (2-6 steps) |
| Data tables from markdown | `table` | Structured tabular data |
| `{{screenshot:filename\|desc}}` | `screenshot` | Real UI screenshot slide (file in `media/screenshots/`) |
| `{{image:id\|caption}}` | `screenshot` | AI figure slide — `screenshot: <id>.png` (file in `media/generated/`) |
| Tips, warnings, key concepts | `callout` | Highlighted callout boxes |
| Notable quotes or key takeaways | `quote` | Full-slide quote (dark background) |
| Hands-on project overview | `section` or `process` | Depending on structure |
| Chapter summary bullets | `content` | Final summary slide |
| Sequential timeline/history | `timeline` | Events in chronological order (3-5) |
| Live demo marker | `demo` | When the chapter calls for a demo |

### Step 3: Write the Markdown slides (`.slides.md`)

Author each slide in `media/slides/chNN.slides.md` following `references/slide-md-format.md`
(slides split by `---`, `<!-- slide: TYPE -->` directive, `::: notes` for narration). All the
instructional-design rules below — sequencing, speaker-note standards, no-emoji, screenshot
handling — apply to what you write **in the MD**. The YAML schema shown below is the **compile
target**: it defines exactly what each MD slide type must produce in Step 3b.

#### File Structure (compile target — see `yaml-format.md`)

```yaml
meta:
  book: claude-cowork
  chapter: <int>           # Chapter number (1-indexed)
  title: "<chapter title>"
  subtitle: "<chapter subtitle>"

slides:
  - type: cover
    chapter: "บทที่ <N>"
    title: "<short title>"
    subtitle: "<subtitle>"
    notes: |
      <speaker notes>

  # ... remaining slides
```

#### Slide Construction Rules

**Cover slide** — Always first. Extract the chapter title. Split into a short `title` (main idea, keep under 6 words) and `subtitle` (supporting context). The `chapter` field is the Thai label like "บทที่ 1".

**Section slides** — One per major `## N.X` heading. Create 2-5 cards that summarize the key points of that section. Cards should have:
- `label`: A very short keyword (1-3 words, Thai or English)
- `title`: Card heading (concise, under 8 words)
- `body`: 2-3 lines explaining the point

The card count determines the template variant automatically (section-2 through section-5).

**Content slides** — Break long sections into multiple content slides. Each should have 3-6 bullets. Bullets should be substantive sentences, not single words.

**Image slides (PRESERVE EVERY IMAGE)** — **CRITICAL: Every image placeholder in the chapter MUST
become a `type: screenshot` slide in the YAML — both `{{screenshot:filename|description}}` (real UI)
AND `{{image:id|caption}}` (AI figure).** Do NOT skip any. Do NOT replace them with content/section slides.

**MANDATORY: Before writing any YAML, scan the full chapter text to build a complete ordered list of
ALL image placeholders of BOTH kinds** (`{{screenshot:...}}` and `{{image:...}}`). Write the list as a
comment at the top of your notes. Then ensure every item becomes a `type: screenshot` slide with the
correct `screenshot:` field, at the position it appears in the chapter.

Map the placeholder to the `screenshot:` filename:
- `{{screenshot:file.png|...}}` → `screenshot: "file.png"` (append `.png` if missing) — resolves to
  `media/screenshots/`.
- `{{image:some-id|...}}` → `screenshot: "some-id.png"` — resolves to `media/generated/some-id.png`
  (the file `generate-image` produced; the renderer searches both media folders).

The `screenshot` field is **required** — never use the `title`/`description` placeholder style instead.

#### VISUAL INSPECTION — See Before You Write

**For every screenshot slide, you MUST visually inspect the actual image file before writing the speaker notes.** Use the `Read` tool on the PNG file — it supports images natively:

```
Read: <workspace>/media/screenshots/02-cowork-tab-home-screen.png
Read: <workspace>/media/screenshots/browser/01-chrome-webstore-listing.png
Read: <workspace>/media/screenshots/subagents/03-tasks-running.png
```

The screenshot path in `{{screenshot:filename.png|...}}` maps directly to `<workspace>/media/screenshots/filename.png`.

**Why this matters:** Generic notes like "นี่คือหน้าจอการตั้งค่า" are useless. When you SEE the actual screenshot, you can write notes that match reality: "สังเกตปุ่ม Enable ตรงมุมขวาบน" or "ในรายการจะเห็น 3 Connector ที่เชื่อมต่อแล้ว". The voice-over must align with what the learner actually sees on screen.

**Process for each screenshot slide:**
1. `Read` the PNG file to see what's in it
2. Identify 2-3 key visual elements the learner should notice
3. Write notes that **guide the learner's eyes** through the screenshot: "ตรงกลางจะเห็น...", "ด้านซ้ายมี...", "สังเกตว่า..."
4. Connect what they see to the concept just taught on the previous slide

**If the image is a mockup or placeholder** (solid color with text overlay), note this internally but still write notes based on the mockup's labeled elements. The notes should describe what the REAL UI would look like, guided by the chapter text and reference docs.

**If the image file doesn't exist** at the expected path, write notes based on the chapter's `{{screenshot:...|description}}` text and surrounding context. Add a YAML comment `# TODO: screenshot not found, notes based on chapter description`.

```yaml
# From: {{screenshot:02-cowork-tab-home-screen.png|แท็บ Cowork}}
# Step 1: Read media/screenshots/02-cowork-tab-home-screen.png to see it
# Step 2: Write notes that match what's actually in the image
- type: screenshot
  screenshot: "02-cowork-tab-home-screen.png"
  notes: |
    ที่เห็นคือหน้า Cowork เมื่อเปิดครั้งแรก ตรงกลางคือกล่องพิมพ์คำสั่ง
    ด้านล่างมีปุ่ม Work in a folder สำหรับเลือกโฟลเดอร์ที่ Cowork จะเข้าถึง
    ด้านซ้ายเป็น Sidebar มี New task, Search, Scheduled และ Customize
```

Rules for screenshot slides:
- The `screenshot` field must contain the **exact filename** from the `{{screenshot:...}}` tag (with `.png` extension)
- Include subdirectory paths if present (e.g., `subagents/03-tasks-running.png`)
- **ALWAYS `Read` the actual PNG before writing notes** — describe what you SEE, not what you guess
- Speaker notes should **guide the learner's eyes** through the screenshot — point out specific UI elements, buttons, labels
- If a filename appears multiple times in the chapter (duplicate placeholders), create only ONE screenshot slide for it
- Each screenshot slide should appear near the content it illustrates — not all grouped at the end
- **Never skip a screenshot placeholder to save slide count** — if the chapter has 8 screenshots, the YAML must have 8 screenshot slides

**Process slides** — Use for step-by-step workflows. Each step needs `number`, `title`, and `body`. Keep to 2-6 steps.

**Callout slides** — Use for tips, warnings, or key concepts from the chapter. Map the chapter's admonition style:
- Tips or recommendations -> `style: tip`
- Warnings or cautions -> `style: warning`
- Key concepts or definitions -> `style: concept`

**Two-column slides** — Use when the chapter explicitly compares two approaches (before/after, old way/new way, chat vs Cowork).

**Quote slides** — Use sparingly (0-1 per chapter). Good for the chapter's opening hook or a particularly impactful statement.

**Table slides** — Use when the chapter contains actual tabular data (pricing comparisons, feature matrices, etc.).

**Timeline slides** — Use when content describes a chronological sequence of events (3-5 events).

## Critical Rules

### No Emoji or Emoticons on Slides

The downstream PPTX conversion tool cannot render emoji characters. They appear as broken squares or missing glyphs.

**Never use these in any slide text field** (`title`, `subtitle`, `bullets`, `body`, `label`, `header`, `text`, `attribution`, `description`, `headers`, `rows`, `footer`):
- Unicode emoji: stars, checkmarks, arrows, faces, hands, objects
- Common offenders: ✅ ❌ 🔄 ⏳ ⚡ 💡 📝 ⚠️ ✦ ⏹️ ▶ 🎯 📊 🔑 ➡️
- Dingbats and symbols that look like emoji

**Replace them with plain text alternatives:**

| Instead of | Write |
|-----------|-------|
| ✅ | (completed) or just describe the state |
| ❌ | (incorrect) or "ไม่ดี" |
| 💡 | "เคล็ดลับ:" |
| ⚠️ | "ข้อควรระวัง:" |
| ⚡ | "โปรเจกต์ลงมือทำ:" |
| 🔄 | "กำลังทำ" |
| ⏳ | "รอดำเนินการ" |
| ➡️ | " -> " or " — " |
| ✦ ▲ ◆ | These are OK only in callout `style` rendering (handled by template), not in text |

**Speaker notes (`notes` field) are also emoji-free** — they go through TTS which reads raw text.

### Speaker Notes — Voice-Over Script for Video Course

The `notes` field is the voice-over script. It gets fed to TTS (Gemini TTS) and becomes the actual audio track. The slides are visual aids — the notes ARE the lesson.

#### Core Principle: Rich, Descriptive, and Engaging — The Notes ARE the Lesson

The slides are just visual cues. **The speaker notes are the actual teaching.** A learner who only LISTENS to the audio (without watching slides) should still understand the lesson completely. Write like a skilled instructor who explains thoroughly, gives vivid examples, uses analogies, and makes every concept feel tangible.

**The golden rule:** Each note should feel like a mini-lecture. The instructor introduces the concept, explains WHY it matters, gives a concrete example or analogy from the learner's work life, walks through the details, and smoothly transitions to what comes next.

**What GOOD notes do:**
- Paint a picture: "สมมติว่าคุณเป็นผู้จัดการทีมขาย ทุกสิ้นเดือนต้องรวบรวมตัวเลขจาก 5 ทีมย่อย..." — put the learner in a scenario
- Explain the WHY, not just the WHAT: Don't just say a feature exists — explain what problem it solves
- Use analogies: "เหมือนกับการจ้างผู้ช่วยส่วนตัวที่ทำงาน 24 ชั่วโมง" — connect to familiar experiences
- Add depth beyond the slide: If the slide shows 3 bullets, the notes should expand each with context, examples, or practical tips
- Bridge meaningfully: Preview what's coming next and WHY it connects

**Anti-patterns to AVOID:**
- Being too terse — notes that just name the topic without explaining it
- Repeating the exact same point in different words across consecutive sentences
- Starting every note the same way

#### Word Count Guidelines

These are HARD TARGETS — notes below the minimum are considered failures. **Be generous with explanation.** A thorough 200-word note that teaches with examples and analogies is what we want. Err on the side of MORE explanation, not less.

| Slide Type | Target Words | Hard Minimum | Sweet Spot |
|-----------|-------------|-------------|------------|
| `cover` | 120-180 | 100 | 150 |
| `section` | 150-220 | 120 | 180 |
| `content` | 180-280 | 150 | 220 |
| `two_column` | 180-280 | 150 | 220 |
| `process` | 180-280 | 150 | 220 |
| `table` | 150-220 | 120 | 180 |
| `callout` | 150-200 | 120 | 170 |
| `screenshot` | 120-180 | 100 | 150 |
| `quote` | 100-150 | 80 | 120 |
| `demo` | 80-120 | 60 | 100 |

**If your notes are under the Hard Minimum, you MUST expand them** — add examples, analogies, practical scenarios, or deeper explanation. Under-writing is a bigger problem than over-writing for video courses.

#### Tone and Style

Conversational Thai, like a friendly **male** instructor in an online course:
- **MALE speaker only**: Use "ครับ" — NEVER "ค่ะ", "คะ", "นะคะ", "จ้า", "จ๊ะ" or any female particles
- Use "ผม" (not "ฉัน/ดิฉัน") when referring to the speaker
- Use "ครับ" sparingly — once or twice per note, not every sentence
- Address the listener as "คุณ" — direct second person
- Present tense, as if the learner is following along right now
- Warm and clear, not academic or overly casual
- **NEVER start notes with "ครับคุณ"** — grammatically wrong. Start directly with content or use natural openers

#### Note Structure — Teach Like You're In The Room

Each note should follow this expanded flow:

1. **Hook** (1-2 sentences) — Open with a scenario, question, or real-world problem that makes the learner care. "สมมติว่าคุณต้องส่งรายงานภายในวันนี้..." or "หลายคนเคยเจอปัญหาแบบนี้..."
2. **Explain** (4-6 sentences) — This is the core teaching. Expand each key point with:
   - A concrete example from business/office life
   - An analogy that connects to something familiar
   - Practical tips on HOW to use this, not just WHAT it is
   - Mention edge cases or common mistakes if relevant
3. **Reinforce** (1-2 sentences) — Summarize the key takeaway in a memorable way, or give a practical tip the learner can apply immediately.
4. **Bridge** (1 sentence) — Connect to the next slide with context about WHY the next topic follows.

**Total: 7-12 sentences per slide.** Content and process slides should be on the higher end. Screenshot and quote slides can be on the lower end but still need to be descriptive.

#### Example — BAD (too short, just names the topic):

```yaml
# BAD — only 30 words, just restates slide bullets
notes: |
  Cowork สร้าง Excel ที่มีสูตรจริง Conditional Formatting หลายชีต
  เปิดได้ใน Excel, Google Sheets หรือ Numbers
```
This tells the learner WHAT but not WHY, HOW, or WHEN. No example, no scenario, no depth.

#### Example — BAD (says "important" without explaining):

```yaml
# BAD — vague filler, no teaching
notes: |
  ประเด็นนี้มีความสำคัญ เพราะมันเป็นพื้นฐานของสิ่งต่อไป
  ให้คุณจำไว้ นี่คือสิ่งที่จะทำให้ความเข้าใจของคุณลึกซึ้งขึ้น
```
This says "it's important" without explaining WHY. Every sentence must teach something concrete.

#### Example — GOOD (content slide, ~200 words, rich with scenario and examples):

```yaml
notes: |
  สมมติว่าคุณเป็นผู้จัดการฝ่ายขาย ทุกสิ้นเดือนต้องรวบรวมตัวเลขยอดขายจาก
  5 ทีมย่อย แล้วทำเป็นรายงานส่งผู้บริหาร ปกติใช้เวลาครึ่งวันเปิด Excel
  คัดลอกตัวเลข แล้วค่อย ๆ สร้างสูตร SUMIF ทีละเซลล์ครับ Cowork ทำทั้งหมด
  นี้ให้คุณได้ในไม่กี่นาที แค่บอกว่า สร้างสเปรดชีตสรุปยอดขายรายทีม
  รวมยอดตามประเภทสินค้า ใส่ Conditional Formatting สีเขียวสำหรับทีมที่ทำ
  ยอดถึงเป้า สีแดงสำหรับทีมที่ต่ำกว่าเป้า ผลที่ได้ไม่ใช่แค่ตารางสวย ๆ
  แต่เป็นสเปรดชีตที่มีสูตรทำงานจริงครับ สูตร SUMIF จะรวมยอดตามเงื่อนไข
  ที่คุณกำหนด เช่น รวมเฉพาะสินค้าประเภท A หรือรวมเฉพาะทีมภาคเหนือ
  Conditional Formatting เปลี่ยนสีเซลล์อัตโนมัติตามค่า ผู้บริหารมองปุ๊บ
  เข้าใจสถานการณ์ทันทีว่าทีมไหนทำได้ดี ทีมไหนต้องปรับปรุง ที่สำคัญ
  ไฟล์ที่ได้เปิดใน Microsoft Excel, Google Sheets หรือ Apple Numbers
  ได้เลยครับ ไม่ต้องแปลงฟอร์แมตอะไรเพิ่ม เพราะ Cowork สร้างเป็น .xlsx
  มาตรฐานตั้งแต่แรก ต่อไปเราจะดูตัวอย่างจริงว่าหน้าตาสเปรดชีตที่ Cowork
  สร้างออกมาเป็นอย่างไรครับ
```
Note: Opens with a scenario, explains the problem, shows how Cowork solves it, gives concrete examples of SUMIF and formatting, explains the benefit, and bridges to the next slide. ~200 words.

#### Example — GOOD (screenshot slide, ~140 words):

```yaml
notes: |
  ที่เห็นในหน้าจอคือหน้า Cowork เมื่อเปิดใช้งานครั้งแรกครับ ตรงกลาง
  ของหน้าจอจะเป็นกล่องพิมพ์คำสั่งขนาดใหญ่ ซึ่งเป็นจุดเริ่มต้นของทุกอย่าง
  ที่คุณจะทำกับ Cowork แค่พิมพ์ภาษาคนธรรมดาว่าอยากได้อะไร ไม่ต้องจำ
  คำสั่งพิเศษใด ๆ เลย เช่น สรุปยอดขายเดือนนี้จากไฟล์ Excel ที่แนบ
  หรือ ช่วยเขียนอีเมลตอบลูกค้าให้หน่อย ด้านล่างกล่องพิมพ์จะมีปุ่ม
  Work in a folder ปุ่มนี้สำคัญมากครับ เพราะเป็นการบอก Cowork ว่าให้
  เข้าถึงโฟลเดอร์ไหนบนเครื่องคุณ ถ้าไม่กดปุ่มนี้ Cowork ก็ยังสร้างไฟล์
  ได้ แต่ไฟล์จะอยู่ในพื้นที่ชั่วคราว ไม่ได้บันทึกลงเครื่องคุณโดยตรง
  ด้านซ้ายจะเป็น Sidebar ที่มีเมนู New task สำหรับเริ่มงานใหม่ Search
  สำหรับค้นหาประวัติ Scheduled สำหรับงานที่ตั้งเวลาไว้ และ Customize
  สำหรับปรับแต่งการทำงานครับ
```
Note: Describes each UI element with context on WHY it matters, gives examples of what to type, explains consequences of choices. ~140 words.

#### Example — GOOD (section divider, ~160 words):

```yaml
notes: |
  หัวข้อถัดไปเป็นเรื่องที่หลายคนอาจมองข้ามแต่สำคัญมากครับ นั่นคือ
  ความปลอดภัยในการใช้ Cowork หลายคนอาจสงสัยว่าทำไมต้องพูดเรื่องนี้
  ในเมื่อ Cowork แค่สร้างเอกสาร แต่ความจริงแล้ว Cowork ทำได้มากกว่านั้น
  เยอะครับ Cowork อ่านไฟล์ เขียนไฟล์ ลบไฟล์ได้ ค้นหาข้อมูลจากอินเทอร์เน็ต
  ได้ เชื่อมต่อกับ Gmail, Google Drive และแอปอื่น ๆ ได้ ทำหลายอย่าง
  พร้อมกันได้ ลองนึกภาพว่าคุณจ้างผู้ช่วยคนใหม่มาทำงานในออฟฟิศ คุณคง
  ไม่ให้กุญแจทุกห้องตั้งแต่วันแรก แต่จะค่อย ๆ บอกว่าห้องไหนเข้าได้
  ห้องไหนยังไม่ต้อง Cowork ก็เหมือนกันครับ เราต้องรู้ว่าจะตั้งขอบเขต
  อย่างไร ให้ Cowork เข้าถึงสิ่งที่จำเป็น แต่ไม่เข้าถึงข้อมูลที่ยังไม่พร้อม
  แชร์ ในหัวข้อนี้เราจะดู 4 ประเด็นหลัก ตั้งแต่สิทธิ์การเข้าถึงไฟล์ ไปจนถึง
  การป้องกันข้อมูลส่วนตัวครับ
```
Note: Motivates WHY security matters, uses the "new assistant + house keys" analogy expanded fully, previews all 4 subtopics. ~160 words.

#### What NOT to Do

- **Write too short** — This is the #1 problem. Notes under 100 words almost always lack examples, scenarios, or depth. If your note is under the Hard Minimum, you MUST expand it. Add a scenario, an analogy, or walk through a specific example step by step.
- **Just name the topic** — "นี่คือฟีเจอร์ Connector ครับ" is useless. Explain what it does, why someone would use it, give an example, and show how it fits into their work.
- **Repeat the slide verbatim** — Don't read bullets aloud. Instead, EXPAND on each bullet with examples and context.
- **Same opening every slide** — Vary openers. Don't start every note with "มาดูกัน" or "ทีนี้". Good openers: "สมมติว่า...", "ลองนึกภาพว่า...", "หลายคนเคยเจอปัญหา...", "ตรงนี้น่าสนใจ...", "ในชีวิตจริง...", or start with a scenario directly.
- **Bullet-style reading** — "ข้อแรก... ข้อสอง... ข้อสาม..." sounds robotic. Weave points into natural flowing speech.
- **Jargon without explanation** — This audience is non-technical. When you say VLOOKUP, add "เหมือนมีคนเปิดอีกหน้าหาข้อมูลมาให้". When you say API, add "คือช่องทางที่โปรแกรมต่าง ๆ คุยกัน".
- **Skip the scenario** — Every content and process slide should ideally open with a real-world scenario that makes the learner care BEFORE you explain the feature.

### YAML Formatting

- Use block scalar `|` for all multi-line text (notes, body, long bullets)
- Quote strings that contain colons, brackets, or special YAML characters
- Consistent 2-space indentation throughout
- No trailing spaces
- Ensure the `meta` block comes first, then `slides` as a list

### Content Quality — Instructor Standards

- **Every slide must have `notes`** — no exceptions. No notes = no voice-over = dead air in the video
- **One idea per slide** — if a slide covers two topics, the learner gets confused. Split it.
- **Notes must be the primary teaching medium** — the slide is just a visual outline. The notes should contain scenarios, examples, analogies, practical tips, and deeper explanation. If you removed the notes, the learner should lose 80% of the lesson's value.
- **Every note needs at least one concrete example or scenario** — abstract explanations don't stick. "สมมติว่าคุณเป็นนักบัญชี..." or "ตัวอย่างเช่น ถ้าคุณต้องส่งรายงาน..." makes the teaching tangible.
- **No empty filler** — delete sentences that say "this is important" without saying WHY. But DO add depth, examples, and practical tips — that's not filler, that's teaching.
- **Section slides preview the lesson segment** — cards aren't keywords, they tell the learner what they'll learn in the next few slides
- **Bullets should be complete thoughts** — not fragments or single words
- **Thai terminology consistency** — use "สั่งงาน" for prompts, "ผู้ช่วย" for Claude, "เซสชัน" for session, "โฟลเดอร์" for folder

### Step 3b: Compile `.slides.md` → `.yaml` (deterministic script)

Once `chNN.slides.md` is written/tuned, compile it with the bundled compiler — do **not**
hand-transcribe the YAML:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/create-book-yaml/scripts/slides_md2yaml.py \
  media/slides/chNN.slides.md            # writes media/slides/chNN.yaml
# validate only, no write:
python3 ${CLAUDE_PLUGIN_ROOT}/skills/create-book-yaml/scripts/slides_md2yaml.py \
  media/slides/chNN.slides.md --check
```

The script maps every `<!-- slide: TYPE -->` block to the `yaml-format.md` schema, turns
`::: notes` into literal-block `notes:`, and preserves document order (so insert/delete never
renumbers). Requires PyYAML. To verify the environment first, run the shared preflight:
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/build-slides-pptx/scripts/check_env.py` (warns + prints the
`pip install ...` line if anything is missing).

- **Never hand-edit `chNN.yaml`** — it is regenerated from the MD every time.
- The script exits non-zero and names the offending slide on malformed input (missing directive,
  unclosed `:::`, missing `::: notes`, unknown type). Fix the `.slides.md` and recompile — never
  patch the YAML.
- `id=` on a slide directive is reserved for stable output naming; wiring it into
  audio filenames is a follow-up (the pipeline pairs by document order today — see generate-tts).

## Step 4: Validate

Validate the **`.slides.md`** (the surface) and confirm it **compiles** cleanly:

1. **MD well-formed** — every slide has a `<!-- slide: TYPE -->` first line; every `:::` closed
2. **Compiles to valid YAML** — Step 3b produces parseable YAML with no errors
2. **All slides have `notes`** — check every slide entry, no exceptions
3. **No emoji anywhere** — scan all text fields
4. **Slide count in range** — 15-25 slides per chapter (may exceed 25 if chapter has many screenshots)
5. **Section coverage** — every `## N.X` section from the chapter is represented
6. **Image audit (BOTH kinds — mandatory)** — no image in the chapter may be dropped:
   - Extract every `{{screenshot:filename}}` AND every `{{image:id}}` from the chapter markdown (unique)
   - Extract every `screenshot:` value from your YAML slides
   - Confirm every chapter image appears: `{{screenshot:X.png}}` → `screenshot: X.png`;
     `{{image:id}}` → `screenshot: id.png`
   - If any are missing, add the slide before saving
7. **Card counts are valid** — section cards: 2-5, process steps: 2-6, timeline events: 3-5

**Image audit quick-check (run mentally or with bash):**
```bash
# Chapter images (both kinds) → expected screenshot filenames:
{ grep -oP '(?<={{screenshot:)[^|}]+' chapters/chNN.md;
  grep -oP '(?<={{image:)[^|}]+' chapters/chNN.md | sed 's/$/.png/'; } | sort -u

# Slide screenshot fields:
grep '  screenshot:' media/slides/chNN.yaml | sed 's/.*screenshot: *//; s/"//g' | sort -u

# The first set must be a subset of the second (every chapter image is on a slide)
```

## Output

Save two files per chapter to `media/slides/` (zero-padded):
```
ch{NN}.slides.md   ← authoring surface (แก้มือที่นี่)
ch{NN}.yaml        ← build artifact (compile จาก .slides.md; ห้ามแก้มือ)
```
(e.g., `ch01.slides.md` + `ch01.yaml`).

When converting multiple chapters, process them in parallel if possible — each chapter is independent.

## Quick Reference: Slide Type Cheat Sheet

| Type | Required Fields | Optional | Background |
|------|----------------|----------|------------|
| `cover` | chapter, title, subtitle | | Dark |
| `quote` | text, attribution | | Dark |
| `section` | number, title, cards[] | subtitle | Light |
| `content` | title, bullets[] | subtitle, numbered | Light |
| `two_column` | title, left{}, right{} | subtitle | Light |
| `timeline` | title, events[] | subtitle, callout{} | Light |
| `process` | title, steps[] | subtitle, footer | Light |
| `table` | title, headers[], rows[][] | subtitle | Light |
| `callout` | style, title, body | | Light |
| `demo` | subtitle | | Dark |
| `screenshot` | screenshot OR image | title, subtitle, description | Light |
| `video_demo` | title, description | duration | Dark |
