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
3. **Consolidate — prefer FEWER, well-organized slides.** Group closely related points onto one
   slide instead of giving each its own. A section's several sub-points usually belong together, not
   spread across 3 thin slides. Only start a new slide when the topic genuinely shifts. Before adding
   a slide, ask: *can this fold into the previous one?* A good instructor covers more ground per
   slide and explains it concisely — not one tiny idea per slide.
4. **Use images as proof points** — place a screenshot/figure slide right after the concept it
   illustrates ("here's the idea" → "here's what it looks like").
5. **Don't over-scaffold short sections** — a lean `## N.X` section can be a single slide, not a
   divider + several content slides + a summary.

**Aim for a LEAN deck — fewer slides, each explaining concisely.**
The chapter's content decides the count, but **bias toward consolidation**: a tight deck the learner
can move through efficiently beats a long one that fragments every point into its own slide. Do NOT
create a slide per minor idea. The only hard rule is coverage — every image gets its slide, and each
`## N.X` section is represented (as few slides as cleanly cover it). **When in doubt, merge.** Padding
the deck with thin, one-idea slides is a defect, not thoroughness.

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

#### On-slide text: short phrases, but DON'T split slides to shorten them

On-slide text is a visual aid — keep each line a short phrase, not a full sentence (the explanation
lives in `::: notes`). But **do NOT create extra slides just to keep bullet counts low** — a single
slide comfortably holds a coherent group of related bullets. Denser-but-clear beats many thin slides.

- **Bullets: short phrases (not full sentences).** "สูตร SUMIF รวมยอดตามเงื่อนไข" ✓ — the detailed
  explanation of it goes in the notes, not on the slide.
- **A content slide can hold several related bullets** — group them; don't spill related points onto
  a second slide to reduce the count on the first.
- **`body`/card text: a phrase, not a paragraph.** Titles: a short phrase, not a sentence.
- Strip filler ("ในหัวข้อนี้เราจะ...", "สิ่งสำคัญคือ...") from slide text — put it in the notes.

#### Slide construction rules

**Cover** — Always first. Split the chapter title into a short `title` (main idea, ≤6 words) and a
`subtitle` (supporting context). `chapter` is the Thai label like "บทที่ 1".

**Section** — One per major `## N.X` heading. 2-5 cards summarizing the section. Each card:
`label` (1-3 word keyword), `title` (≤8 words), `body` (≤2 short lines — a phrase, not a paragraph).
Card count picks the template variant automatically.

**Content** — Group a section's related points onto as few content slides as read cleanly (a slide
can carry several bullets). **Don't split into extra slides just to lower the bullet count** — that
inflates the deck. Each bullet is a short phrase, not a sentence; the teaching goes in the notes.

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

### Speaker notes — the voice-over script (descriptive, but not padded)

The `::: notes` block is the voice-over script fed to TTS — it becomes the actual audio. The slide is
a visual aid; **the notes carry the teaching, and they must be DESCRIPTIVE enough to convey the
chapter's actual substance.** The chapter is detailed — the notes should reflect that detail, not
flatten it to a sentence. A learner listening to the audio alone should genuinely understand the
concept, not just hear its name.

**The one rule that governs length: information DENSITY, not a word count.** Every sentence must add
new information drawn from the chapter — an explanation, the *why*, a concrete specific, a real
example, a caveat. Write as much as the concept genuinely needs to be understood — and stop there.

- **Descriptive (do this):** explain what the concept is, why it matters, how it works, and give a
  concrete example or number from the chapter. A rich concept gets a full, substantive note.
- **Padded (avoid this):** repeating the same point in different words, empty scenarios that add no
  information, filler ("สิ่งสำคัญคือ...", "อย่างที่บอกไป..."), reading the slide bullets aloud verbatim.

Cut PADDING, never DETAIL. If a chapter section is dense, the note should be dense too — that's
descriptive, not verbose. Verbose = words with no new content; descriptive = every word earns its place.

#### Length guide — for the `::: notes` (voice-over) ONLY

**Typical word ranges for a normally-rich concept. NOT quotas to fill and NOT ceilings to fear —
they track how much real content the concept carries.** A simple point runs shorter; a dense,
detail-heavy section from the book runs longer (and should). The test is always density: is every
sentence carrying chapter substance?

| Slide Type | Typical words | Notes |
|-----------|--------------|-------|
| `cover` | 60-110 | set up the chapter's arc |
| `section` | 80-140 | preview what the section teaches + why it matters |
| `content` | 120-220 | the core teaching — explain fully, with the chapter's detail + an example |
| `two_column` | 120-220 | explain BOTH sides substantively, then the trade-off |
| `process` | 120-220 | walk each step with enough detail to actually follow it |
| `table` | 90-170 | interpret the data — what it shows, why it matters, the standout rows |
| `callout` | 90-160 | the tip/warning + the reasoning behind it + consequences |
| `screenshot` | 90-160 | guide the eye through the UI + connect it to the concept |
| `quote` | 50-90 | unpack why the quote matters |
| `demo` | 60-110 | what the demo shows + what to watch for |

A dense chapter concept may exceed the typical range — that's fine when the extra words carry real
content. What is NOT fine is exceeding it with repetition or filler. Under-writing a rich concept
(a one-line note where the chapter has three paragraphs of substance) is just as much a defect as padding.

#### Tone and style
**Banned calques:** follow the shared Thai style rules in
`${CLAUDE_PLUGIN_ROOT}/skills/write-book-chapter/references/thai-style.md` for BOTH slide text
and notes — never use ❌ terms (e.g. "ใต้ฝากระโปรง" → "เจาะลึก"/"เบื้องหลังการทำงาน").

Conversational Thai, a friendly **male** instructor:
- **MALE speaker only**: use "ครับ" — NEVER "ค่ะ", "คะ", "นะคะ", "จ้า", "จ๊ะ" or any female particles.
- Use "ผม" (not "ฉัน/ดิฉัน"); use "ครับ" sparingly (once or twice per note); address the listener as "คุณ".
- Present tense, warm and clear. **NEVER start a note with "ครับคุณ"** (grammatically wrong).

#### Note structure — teach the concept fully
Cover the concept the way the chapter does: **state the point → explain HOW/WHY it works (this is the
substance — pull the real detail from the chapter) → a concrete example or specific number → a short
bridge.** Use as many sentences as the concept's depth needs — a rich concept naturally runs longer.
The discipline is not "few sentences", it's "every sentence adds new chapter content." Don't repeat,
don't pad, but don't flatten a detailed concept into one thin line either.

#### GOOD note example (content slide, ~160 words — descriptive, carries real detail, no padding)
```
เวลาคุณสั่งงานโมเดลภาษา สิ่งที่มันทำจริง ๆ ไม่ใช่การ "เข้าใจ" ประโยคแบบคน แต่เป็นการทำนายคำถัดไปทีละคำจาก
สถิติที่เรียนรู้มาจากข้อความมหาศาลครับ พูดง่าย ๆ คือมันถามตัวเองตลอดว่า "จากคำที่มีอยู่ตอนนี้ คำไหนน่าจะตามมา
มากที่สุด" แล้วเลือกคำนั้น จากนั้นก็เอาคำใหม่มาต่อ แล้วทำนายคำถัดไปอีก วนแบบนี้จนจบประโยค ยกตัวอย่างถ้าเราพิมพ์ว่า
"เมืองหลวงของประเทศไทยคือ" โมเดลจะคำนวณความน่าจะเป็นของคำถัดไป แล้วพบว่า "กรุงเทพ" มีน้ำหนักสูงสุด จึงตอบออกมา
สิ่งที่ทำให้มันเก่งขึ้นเรื่อย ๆ คือขนาดของข้อมูลที่เรียนและจำนวนพารามิเตอร์ ยิ่งเยอะ โมเดลยิ่งจับรูปแบบภาษาได้ละเอียด
แต่ข้อควรระวังคือมันทำนายจากสถิติ ไม่ได้ตรวจสอบว่าจริงหรือไม่ จึงมั่นใจแม้ตอนที่ผิดได้ ต่อไปเราจะดูว่าโมเดลเรียนรู้
รูปแบบเหล่านี้จากข้อมูลได้อย่างไรครับ
```
Note: this teaches the mechanism (next-token prediction), the why (statistics not understanding), a
concrete example (เมืองหลวง→กรุงเทพ), what improves it (data + parameters), and a caveat (confident when
wrong) — every sentence carries chapter substance. That's descriptive, not padded.

#### What NOT to do
- **Too thin — flattening a rich concept.** If the chapter spends three paragraphs on something and
  your note is one line, you dropped the substance. Expand with the chapter's actual detail.
- **Padding (the other failure):** repeating the same point in different words, empty setup scenarios
  that add no information, filler ("สิ่งสำคัญคือ...", "อย่างที่กล่าวไป..."). Cut these — they aren't detail.
- **Reading the bullets aloud verbatim** — explain the idea, don't restate the slide.
- **Jargon without a gloss** — VLOOKUP → "เหมือนเปิดอีกหน้าไปหาข้อมูลมาให้".
- The line to hold: **descriptive detail from the chapter = keep; words that add no new content = cut.**

### Content quality — instructor standards
- **Every slide must have `notes`** — no exceptions (no notes = dead air).
- **Notes must be DESCRIPTIVE** — carry the chapter's real substance (what/why/how + a concrete
  example), enough that the audio alone teaches the concept. Match the note's depth to the chapter's.
- **The standard is information density, not word count** — every sentence adds new chapter content.
  Cut padding (repetition, filler, empty scenarios); keep detail. Under-writing a rich concept is a
  defect just as much as padding is.
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
