---
name: create-slide-markdown
description: >
  Author a chapter's slide deck as Markdown (`media/slides/chNN.slides.md`) — the human-editable
  authoring surface for the in-plugin slide/TTS/video pipeline. This is STEP 1 of two: write the
  slide Markdown here, then compile it to YAML with **create-slide-yaml**. Use whenever the user asks
  to "create slides", "make slides from the chapter", "เขียนสไลด์", "สร้างสไลด์ markdown", "ทำสไลด์จากบท",
  or to draft/author a chapter's video-lesson slides. You act as a course instructor: design a
  learning sequence, write typed slides, and write rich Thai voice-over speaker notes. Output is
  `.slides.md` ONLY — the `.yaml` build artifact is produced by the separate create-slide-yaml skill.
---

## Paths (thai-book-production layout)

หนึ่ง working folder = หนังสือหนึ่งเล่ม Resolve ทุก path จาก `book.yaml → layout:` ที่ root
ของ folder — **ห้าม hardcode** ถ้าไม่มี `book.yaml` แปลว่าไม่ได้อยู่ใน book folder ให้
`init-book` scaffold ก่อน ค่า default:

| what | path |
|------|------|
| chapters | `chapters/chNN.md` |
| outline | `outline/outline.md`, `outline/plan.md` |
| references | `refs/docs/`, `refs/blogs/` |
| **slides (source, แก้มือ — THIS skill writes)** | `media/slides/chNN.slides.md` |
| slides (build artifact — create-slide-yaml writes) | `media/slides/chNN.yaml` |
| screenshots (จริง, จับจากโปรแกรม) | `media/screenshots/` (+ `inventory.json`) |
| generated (AI, built-in TextToImage) | `media/generated/` (+ `inventory.json`) |
| reports (QC) | `reports/chNN.audit.md`, `reports/chNN.proofread.md`, `reports/chNN.yaml-audit.md` |

---

# Create Slide Markdown — Chapter → Video-Lesson authoring

## Your Role

You are a **professional online course instructor** turning a book chapter into a structured video
lesson. You are NOT a slide-maker — you are a **curriculum designer** who thinks about learning
outcomes, pacing, and audience comprehension.

Your audience: Thai business professionals (managers, analysts, marketers, freelancers) who are NOT
programmers. They learn by watching video lessons at their own pace. **Every slide must earn its
place — if a slide doesn't teach something new, don't create it.**

## Where this fits (2-step workflow)

```
create-slide-markdown  →  chNN.slides.md   (this skill — author, human-editable)
create-slide-yaml      →  chNN.yaml        (next skill — deterministic compile + validate)
```
You write **only** `media/slides/chNN.slides.md`. Do NOT write or hand-edit the `.yaml` — that is
compiled from your Markdown by **create-slide-yaml**. The compiled YAML then feeds
`build-slides-pptx` (RenderSlides) → `generate-tts` → `build-chapter-video`.

Read the Markdown authoring format (bundled in this skill) before writing:
```
Read: ${CLAUDE_PLUGIN_ROOT}/skills/create-slide-markdown/references/slide-md-format.md
```
It defines the surface you author: slides split by `---`, a `<!-- slide: TYPE -->` directive per
slide, and a `::: notes` block for narration. (The compile-target YAML schema — the fields each
type produces — lives in create-slide-yaml's `references/yaml-format.md`; read that only if you
need to know what a type compiles into.)

## Process

### Step 1 — Read the chapter and understand the lesson

Read the target chapter Markdown from `chapters/chNN.md`. Think like a course instructor preparing a
lesson plan:
- **What's the learning goal?** After watching, what should the learner be able to DO?
- **What are the key concepts?** List the things the learner MUST understand.
- **What's the logical progression?** Which concept must come before which?
- **Where are the images?** These are your "show, don't tell" moments.

Extract from the chapter:
- Chapter number + title (from `# บทที่ N: ...`) and all `## N.X` section headings.
- Image placeholders — **build a complete ordered list of BOTH kinds**:
  `{{screenshot:filename|description}}` (real UI, in `media/screenshots/`) and
  `{{image:id|caption}}` (AI figure, in `media/generated/<id>.png`). **Every image in the chapter
  must become a slide — never drop one.**
- Tips, warnings, comparisons, tables, timelines, the summary, and any hands-on project.

For short chapters (under ~200 lines), also read `outline/outline.md` and `refs/docs/` for deeper
material to enrich the speaker notes. The chapter gives structure; the references give depth.

### Step 2 — Design the learning sequence

**Think like a course instructor, not a slide-maker.** Don't convert sections 1:1. Design a path:
1. **Identify the learning goal** — what the learner can DO afterward.
2. **Sequence for understanding** — each slide builds on the previous; never show a concept before
   its prerequisites.
3. **One key idea per slide** — if a section has 3 important concepts, that's 3 slides, not one
   cramped slide. Conversely, don't split a single idea across slides just to add slides.
4. **Use images as proof points** — place a screenshot/figure slide right after the concept it
   illustrates ("here's the idea" → "here's what it looks like").
5. **End each section with a takeaway** — a callout, a summary, or a bridge in the notes.

**Slide count: let the content decide — do NOT target a number.**
Create exactly as many slides as the chapter genuinely needs to teach it well, and no more. A tight
chapter might be 8 slides; a rich one with many screenshots might be 30+. **Never pad to hit a
target, and never cut substance to stay under one** — both produce irrelevant or cramped slides.
The only hard rule is coverage: every `## N.X` section is represented, and every image gets its
slide. Beyond that, one key idea per slide and cut anything that doesn't teach.

How chapter elements map to slide types:

| Chapter Element | Slide Type | When to Use |
|----------------|------------|-------------|
| Chapter title + opening story | `cover` | Always the first slide |
| `## N.X Section Title` | `section` | Section divider with 2-5 summary cards |
| Bullet points or key facts | `content` | General information slides |
| Before/after, pros/cons, two sides | `two_column` | Side-by-side comparison |
| Step-by-step instructions | `process` | Numbered workflow (2-6 steps) |
| Data tables from markdown | `table` | Structured tabular data |
| `{{screenshot:filename\|desc}}` | `screenshot` | Real UI screenshot (file in `media/screenshots/`) |
| `{{image:id\|caption}}` | `screenshot` | AI figure — `screenshot: <id>.png` (in `media/generated/`) |
| Tips, warnings, key concepts | `callout` | Highlighted callout boxes |
| Notable quotes or key takeaways | `quote` | Full-slide quote (dark background) |
| Chapter summary bullets | `content` | Final summary slide |
| Sequential timeline/history | `timeline` | Events in chronological order (3-5) |
| Live demo marker | `demo` | When the chapter calls for a demo |

### Step 3 — Write the slide Markdown (`chNN.slides.md`)

Author each slide in `media/slides/chNN.slides.md` per
`references/slide-md-format.md` (slides split by `---`, `<!-- slide: TYPE -->` first line,
`::: notes` for narration). Preserve document order — insert/edit/delete is just moving text blocks;
there are no position numbers to renumber. All the rules below apply to what you write **in the MD**.

#### Slide construction rules

**Cover** — Always first. Split the chapter title into a short `title` (main idea, ≤6 words) and a
`subtitle` (supporting context). `chapter` is the Thai label like "บทที่ 1".

**Section** — One per major `## N.X` heading. 2-5 cards summarizing the section. Each card:
`label` (1-3 word keyword), `title` (≤8 words), `body` (2-3 lines). Card count picks the template
variant automatically.

**Content** — Break long sections into multiple content slides. 3-6 bullets each; bullets are
substantive sentences, not single words.

**Image slides (PRESERVE EVERY IMAGE)** — **CRITICAL: every image placeholder in the chapter MUST
become a `type: screenshot` slide** — both `{{screenshot:filename|description}}` (real UI) AND
`{{image:id|caption}}` (AI figure). Never skip any; never replace with content/section slides.

**MANDATORY: before writing, scan the whole chapter to build a complete ordered list of ALL image
placeholders of both kinds.** Put that list as a comment at the top of your notes, then ensure every
item becomes a screenshot slide at the position it appears.

> Only the `{{...}}` placeholders count. Ignore any `<!-- gen-preview:<id> -->` comment and the
> `![...](...)` line after it — those are review-only previews generate-image adds beside a
> `{{image:...}}`, NOT separate images. One slide per placeholder, never per preview.

Map placeholder → screenshot filename:
- `{{screenshot:file.png|...}}` → `screenshot: "file.png"` (append `.png` if missing) → resolves to
  `media/screenshots/`.
- `{{image:some-id|...}}` → `screenshot: "some-id.png"` → resolves to `media/generated/some-id.png`.

The `screenshot` field is **required** — never use a `title`/`description` placeholder style instead.

##### VISUAL INSPECTION — see before you write

**For every screenshot slide, you MUST visually inspect the actual image file before writing the
notes.** Use `Read` on the PNG (it supports images):
```
Read: <workspace>/media/screenshots/02-cowork-tab-home-screen.png
Read: <workspace>/media/generated/ch01-architecture-vs-weights.jpg
```
Generic notes like "นี่คือหน้าจอการตั้งค่า" are useless. When you SEE the image you can write notes
that match reality: "สังเกตปุ่ม Enable ตรงมุมขวาบน", "ในรายการจะเห็น 3 Connector ที่เชื่อมต่อแล้ว".
For each screenshot slide: (1) Read the file, (2) note 2-3 key visual elements, (3) write notes that
guide the learner's eyes ("ตรงกลางจะเห็น...", "ด้านซ้ายมี...", "สังเกตว่า..."), (4) connect it to the
concept just taught.

- If the image is a mockup (solid color + text overlay), describe what the REAL UI would look like,
  guided by the chapter text and its labeled elements.
- If the file doesn't exist, write notes from the `{{...|description}}` text + surrounding context and
  add a comment `# TODO: screenshot not found`.
- Use the **exact filename** from the tag (with `.png`, include subdir if present). If a filename
  appears twice, create only ONE slide for it. Place each near the content it illustrates.

**Process** — step-by-step workflows. Each step: `number`, `title`, `body`. 2-6 steps.

**Callout** — tips/warnings/key concepts. Map the chapter's admonition: tip → `style: tip`,
warning → `style: warning`, key concept/definition → `style: concept`.

**Two-column** — when the chapter explicitly compares two approaches (before/after, old/new).

**Quote** — sparingly (0-1 per chapter): the opening hook or an impactful statement.

**Table** — actual tabular data (pricing, feature matrices).

**Timeline** — a chronological sequence of events (3-5).

## Critical rules

### No emoji or emoticons on slides
The downstream renderer + TTS choke on emoji. **Never use emoji in any text field** (`title`,
`subtitle`, `bullets`, `body`, `label`, `header`, `text`, `attribution`, `description`, `headers`,
`rows`, `footer`, and `notes`). Replace with plain words:

| Instead of | Write |
|-----------|-------|
| ✅ | (completed) / describe the state |
| ❌ | (incorrect) / "ไม่ดี" |
| 💡 | "เคล็ดลับ:" |
| ⚠️ | "ข้อควรระวัง:" |
| ➡️ | " -> " or " — " |

### Speaker notes — the voice-over script (the notes ARE the lesson)

The `::: notes` block is the voice-over script fed to TTS — it becomes the actual audio. The slide is
a visual aid; **the notes are the teaching.** A learner who only LISTENS should still understand the
lesson completely. Write like a skilled instructor: introduce the concept, explain WHY it matters,
give a concrete example or analogy from the learner's work life, walk through the details, and bridge
to what's next.

**What GOOD notes do:** paint a scenario ("สมมติว่าคุณเป็นผู้จัดการทีมขาย..."), explain the WHY not
just the WHAT, use analogies ("เหมือนกับการจ้างผู้ช่วยส่วนตัว..."), add depth beyond the slide's
bullets, and bridge meaningfully to the next slide.

#### Word-count guidelines (HARD TARGETS — under the minimum is a failure)

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

Err on MORE explanation. Under-writing is a bigger problem than over-writing for video courses.

#### Tone and style
Conversational Thai, a friendly **male** instructor:
- **MALE speaker only**: use "ครับ" — NEVER "ค่ะ", "คะ", "นะคะ", "จ้า", "จ๊ะ" or any female particles.
- Use "ผม" (not "ฉัน/ดิฉัน"); use "ครับ" sparingly (once or twice per note); address the listener as "คุณ".
- Present tense, warm and clear. **NEVER start a note with "ครับคุณ"** (grammatically wrong).

#### Note structure — teach like you're in the room
1. **Hook** (1-2 sentences) — a scenario/question/problem that makes the learner care.
2. **Explain** (4-6 sentences) — the core teaching: concrete example, analogy, HOW to use it, common
   mistakes.
3. **Reinforce** (1-2 sentences) — the key takeaway, memorably.
4. **Bridge** (1 sentence) — why the next slide follows.

**Total: 7-12 sentences per slide.** Content/process on the higher end; screenshot/quote lower but
still descriptive.

#### GOOD note example (content slide, ~200 words — scenario + examples + bridge)
```
สมมติว่าคุณเป็นผู้จัดการฝ่ายขาย ทุกสิ้นเดือนต้องรวบรวมตัวเลขยอดขายจาก 5 ทีมย่อย แล้วทำเป็น
รายงานส่งผู้บริหาร ปกติใช้เวลาครึ่งวันเปิด Excel คัดลอกตัวเลข แล้วค่อย ๆ สร้างสูตร SUMIF ทีละเซลล์ครับ
เครื่องมือนี้ทำทั้งหมดให้คุณได้ในไม่กี่นาที แค่บอกว่าอยากได้อะไร ... ผลที่ได้ไม่ใช่แค่ตารางสวย ๆ แต่เป็น
สเปรดชีตที่มีสูตรทำงานจริง ... ต่อไปเราจะดูตัวอย่างจริงว่าหน้าตาออกมาเป็นอย่างไรครับ
```
Opens with a scenario, explains the problem, shows the solution with concrete examples, and bridges.

#### What NOT to do
- **Too short** — the #1 problem. Under the Hard Minimum → expand with a scenario/analogy/example.
- **Just naming the topic** — "นี่คือฟีเจอร์ Connector ครับ" is useless; explain what/why/how + example.
- **Reading the bullets aloud** — EXPAND each bullet with context, don't restate it.
- **Same opener every slide** — vary: "สมมติว่า...", "ลองนึกภาพว่า...", "หลายคนเคยเจอปัญหา...", a scenario.
- **Jargon without a plain-language gloss** — VLOOKUP → "เหมือนมีคนเปิดอีกหน้าหาข้อมูลมาให้".

### Content quality — instructor standards
- **Every slide must have `notes`** — no exceptions (no notes = dead air).
- **One idea per slide** — split a two-topic slide.
- **Notes are the primary teaching medium** — remove them and the learner loses 80% of the lesson.
- **Every note needs a concrete example or scenario.**
- **No empty filler** — cut "this is important" without a WHY; but DO add examples/tips (that's teaching).
- **Thai terminology consistency** — "สั่งงาน" (prompt), "ผู้ช่วย" (the assistant), "เซสชัน", "โฟลเดอร์".

## Validate (the `.slides.md` surface)
Before handing off to create-slide-yaml, check:
1. **MD well-formed** — every slide's first line is `<!-- slide: TYPE -->`; every `:::` is closed.
2. **All slides have `::: notes`.**
3. **No emoji** anywhere.
4. **Section coverage** — every `## N.X` section from the chapter is represented.
5. **Image audit (both kinds, mandatory)** — every `{{screenshot:...}}` and `{{image:...}}` in the
   chapter has a screenshot slide. Do NOT drop any to trim the deck.
6. **Card counts valid** — section cards 2-5, process steps 2-6, timeline events 3-5.

Image audit quick-check:
```bash
{ grep -oP '(?<={{screenshot:)[^|}]+' chapters/chNN.md;
  grep -oP '(?<={{image:)[^|}]+' chapters/chNN.md | sed 's/$/.png/'; } | sort -u
grep -oP '(?<=screenshot: )["'"'"']?[^"'"'"']+' media/slides/chNN.slides.md | tr -d '"'"'"'"' | sort -u
# first set ⊆ second (every chapter image is on a slide)
```

## Output
Write **one file**: `media/slides/ch{NN}.slides.md` (zero-padded, e.g. `ch01.slides.md`).
**Do NOT produce the `.yaml`** — that's the next step. When done, hand off to **create-slide-yaml**
to compile + validate. Converting multiple chapters: each is independent (parallelizable).
