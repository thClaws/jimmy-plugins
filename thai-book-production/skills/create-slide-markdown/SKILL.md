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

### Speaker notes — the voice-over script (WRITE FOR THE EAR: descriptive but tight)

The `::: notes` block is the voice-over script fed to TTS — it becomes the actual **audio a person
sits and listens to.** Two things must both be true: it's **descriptive** (conveys the point with
its key detail, so the audio teaches) AND **tight** (a listener bores fast — say it once, clearly,
efficiently, then move on). This is not a book paragraph you can re-read; it's spoken, so **every
extra sentence costs the listener's attention.** Make the point, land the key detail, stop.

**The two defects to avoid — both make the VO too long AND boring:**
1. **Over-explaining one point** — restating it three ways, spelling out every nuance, a long setup
   scenario. Make the point once with its essential detail, then move on.
2. **REPEATING across slides (the big one)** — re-teaching a concept, analogy, example, or timeline
   an earlier slide already covered. This is the #1 source of tedium in a multi-slide deck.

**Anti-repetition — a slide's note must teach something NEW.** Before writing each note, recall what
earlier slides already said and do NOT say it again:
- **Section dividers PREVIEW, they don't teach.** Briefly frame what this section is about and why it
  matters (2-3 sentences) — do NOT tell the whole story; the content slides that follow carry the
  detail. A section note that narrates the entire topic makes the next 3 slides feel like reruns.
- **Screenshot notes DESCRIBE the image + add ONE new angle** — guide the eye through what's on screen
  and make one fresh connection. Do NOT re-explain the concept the previous content slide just taught.
- **Reuse an analogy at most once or twice, at its highest-impact spot** — not on every slide of a
  section. If you used ตึก/เฟอร์นิเจอร์ or ช่างแกะสลัก already, don't reach for it again.
- If two adjacent slides would say nearly the same thing, one of them adds nothing — make it add a
  new example, a caveat, or a different facet, or shorten it to a bridge.

#### Length guide — for the `::: notes` (voice-over) ONLY

**Keep VO tight enough to hold a listener. These are the target lengths for the SPOKEN audio — aim
for the LOW end when the point is simple, and only reach the high end for a genuinely dense concept.**
Descriptive means "carries the point + its key detail", NOT "exhausts every detail from the book."

| Slide Type | Target words | Keep it to |
|-----------|-------------|-----------|
| `cover` | 50-90 | one hook + the chapter's promise |
| `section` | 40-80 | a PREVIEW — what + why, not the whole story |
| `content` | 90-150 | the point + how/why + one concrete example |
| `two_column` | 90-150 | both sides briefly + the trade-off |
| `process` | 100-160 | one clear line per step |
| `table` | 70-120 | what it shows + the standout row |
| `callout` | 70-120 | the tip/warning + the one reason it matters |
| `screenshot` | 70-120 | describe the image + one fresh connection |
| `quote` | 40-70 | why it matters, briefly |
| `demo` | 50-90 | what it shows + what to watch |

Going OVER the target is almost always repetition or over-explaining — cut it. But don't drop below a
real explanation either: a bare one-liner for a concept the chapter details is too thin. The sweet
spot is **descriptive-but-tight**: the listener learns the point and stays engaged.

#### Tone and style
**Banned calques:** follow the shared Thai style rules in
`${CLAUDE_PLUGIN_ROOT}/skills/write-book-chapter/references/thai-style.md` for BOTH slide text
and notes — never use ❌ terms (e.g. "ใต้ฝากระโปรง" → "เจาะลึก"/"เบื้องหลังการทำงาน").

Conversational Thai, a friendly **male** instructor:
- **MALE speaker only**: use "ครับ" — NEVER "ค่ะ", "คะ", "นะคะ", "จ้า", "จ๊ะ" or any female particles.
- Use "ผม" (not "ฉัน/ดิฉัน"); use "ครับ" sparingly (once or twice per note); address the listener as "คุณ".
- Present tense, warm and clear. **NEVER start a note with "ครับคุณ"** (grammatically wrong).

#### Note structure — one clean pass, then stop
**State the point → explain how/why with the ONE key detail → a concrete example or number → a
one-phrase bridge.** That's it — for the ear, this is enough to teach the point without losing the
listener. Pick the *most important* detail; don't spell out every one the chapter mentions (the book
has them; the slide's job is to teach the core, tightly). Roughly 3-6 sentences for a content slide.

#### GOOD note example (content slide, ~110 words — descriptive but tight, no repetition)
```
LLM ทำงานด้วยการทำนายคำถัดไปทีละคำจากสถิติที่เรียนมาจากข้อความมหาศาลครับ มันถามตัวเองว่า "จากคำที่มีอยู่
คำไหนน่าจะตามมามากที่สุด" เลือกคำนั้น แล้วทำนายต่อไปเรื่อย ๆ จนจบ ตัวอย่างเช่นพิมพ์ "เมืองหลวงของไทยคือ"
โมเดลให้ "กรุงเทพ" ความน่าจะเป็นสูงสุดจึงตอบออกมา ข้อควรระวังคือมันทำนายจากสถิติ ไม่ได้ตรวจว่าจริงไหม จึงมั่นใจ
แม้ตอนผิดได้ครับ
```
Teaches the mechanism, gives one concrete example (เมืองหลวง→กรุงเทพ), lands one caveat — then stops.
Tight enough to listen to, descriptive enough to learn from. (Note it does NOT also cover parameters,
training, or history — those belong on their own slides, not repeated here.)

#### What NOT to do
- **Repeating an earlier slide** (the #1 defect) — re-teaching a concept/analogy/example/timeline
  already covered. Say it once, on its own slide; later slides reference it in a phrase, not re-explain it.
- **Over-explaining one point** — three sentences where one does it, long setup scenarios, spelling
  out every nuance. The listener bores. Land the core, move on.
- **Padding / filler** — "สิ่งสำคัญคือ...", "อย่างที่กล่าวไป...", reading the bullets aloud verbatim.
- **Section notes that tell the whole story** — they should PREVIEW; the content slides teach.
- **Too thin, though** — a bare one-liner for a concept the chapter details is under-written. The
  target is descriptive-but-tight, not empty.

### Content quality — instructor standards
- **Every slide must have `notes`** — no exceptions (no notes = dead air).
- **Descriptive but TIGHT** — the note teaches THIS slide's point with its one key detail + an
  example, then stops. Written for the ear: a listener bores, so no over-explaining, no padding.
- **No repetition across slides** — each note adds something NEW; never re-teach what an earlier slide
  covered. Section notes preview (short); screenshot notes describe the image + one fresh angle.
- **Reuse an analogy at most once or twice**, at its best spot — not on every slide of a section.
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
