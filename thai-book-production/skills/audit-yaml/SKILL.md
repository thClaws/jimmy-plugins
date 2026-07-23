---
name: audit-yaml
description: "Audit YAML slides against chapter .md, yaml spec, and Thai style guide — then auto-fix all issues in one pass."
triggers:
  - audit yaml
  - audit-yaml
  - ตรวจ yaml
  - check yaml
  - fix yaml
  - yaml audit
  - yaml quality
  - ตรวจสไลด์
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
| slides (source, ตรวจ+แก้ที่นี่) | `media/slides/chNN.slides.md` |
| slides (build artifact) | `media/slides/chNN.yaml` (regenerate เท่านั้น ห้ามแก้มือ) |
| screenshots (จริง, จับจากโปรแกรม) | `media/screenshots/` (+ `inventory.json`) |
| generated (AI, built-in TextToImage) | `media/generated/` (+ `inventory.json`) |
| reports (QC ทุกชนิด) | `reports/chNN.audit.md`, `reports/chNN.proofread.md`, `reports/chNN.yaml-audit.md` |
| apparatus | `apparatus/glossary.md`, `apparatus/index.md` |
| translations | `translations/<lang>/chapters/chNN.md` |
| assets | `assets/` |
| build output | `build/` |


# Audit YAML Skill — Audit & Auto-Fix in One Pass

You are a YAML slide quality auditor and fixer for the book "ผู้ช่วยคนใหม่ของคุณ: คู่มือ Claude Cowork ฉบับสมบูรณ์". Your job is to audit each YAML slide file against 5 dimensions, then **immediately fix every issue** — no separate fix step.

## Core Principle

**Audit AND fix in one pass — on the `.slides.md` surface.** For each issue you find, fix it
immediately **in `chNN.slides.md`** (the human-editable Markdown), then recompile with the
bundled compiler:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/create-slide-yaml/scripts/slides_md2yaml.py \
  media/slides/chNN.slides.md
```

**Never patch the YAML directly** — it's a build artifact regenerated from the MD. Only flag issues
for human review when the fix is genuinely ambiguous (e.g., factual uncertainty about a feature).
Everything else — flow, redundancy, notes quality, format, Thai proofreading — gets auto-fixed in the MD.

## Before You Start

Read these files:

1. **Markdown slide format spec** — the authoring surface you audit/fix:
```
Read ${CLAUDE_PLUGIN_ROOT}/skills/create-slide-markdown/references/slide-md-format.md
```
2. **YAML format spec** — the compile target (so you know what the MD must produce):
```
Read ${CLAUDE_PLUGIN_ROOT}/skills/create-slide-yaml/references/yaml-format.md
```

3. **The source chapter** — `chapters/ch{NN}.md` — this is the ground truth for content
4. **The slides source** — `media/slides/ch{NN}.slides.md` — **this is what you audit and fix**
   (`ch{NN}.yaml` is the build artifact; regenerate it after fixing, never edit it by hand)
5. **The book outline** — `outline/outline.md` — for section structure reference

## The 5 Audit Dimensions

### Dimension 1: Flow Sync (ลำดับสไลด์ vs บท)

Check that slides follow the same logical order as the chapter `.md`.

**What to check:**
- The cover slide matches the chapter title
- Section slides (`type: section`) appear in the same order as `## N.X` headings in the `.md`
- Content slides within each section cover the same topics in the same order
- Screenshot slides appear near the content they illustrate (same position as in `.md`)
- No orphaned slides (slides about content not in the chapter)
- No missing sections (sections in the `.md` that have no slides)
- The summary/closing section appears at the end

**How to fix:**
- Reorder slides to match chapter flow
- Add missing section slides or content slides for uncovered sections
- Remove slides that reference content not in the chapter
- Move screenshot slides to the correct position

**Issue severity:**
- CRITICAL: Section completely missing from YAML
- MAJOR: Slides significantly out of order, or screenshot in wrong position
- MINOR: Slight ordering preference differences

### Dimension 2: Redundancy (ความซ้ำซ้อน)

Check for redundant or bloated slide content.

**What to check:**
- Multiple slides covering the exact same concept (consolidate)
- Bullets that repeat the same idea in different words
- Speaker notes that repeat content from the previous slide's notes
- Section cards that overlap significantly with subsequent content slides
- Multiple slides teaching the SAME idea (genuine redundancy)

**Slide count is NOT audited against a target.** There is no minimum or maximum — the deck should be
exactly as long as the chapter's content needs (create-slide-markdown lets content decide). Judge
each slide on whether it teaches something new, NOT on the total. Flag a slide only when it is
genuinely redundant with another, not because the deck is "long" or "short".

**How to fix (slide count is fine — fix the NOTES, don't merge slides):**
- **Repetition is mainly a VO problem, not a count problem.** A content slide + a screenshot slide on
  the same concept is OK — but their NOTES must differ: the content slide teaches it, the screenshot
  slide describes the image + one new angle. Differentiate the notes; keep the slides.
- A `section` note that told the whole story → cut it to a short PREVIEW, let the content slides teach.
- A reused analogy on 3+ slides → keep it on the one slide it lands best; drop it elsewhere.
- Trim over-explained notes to the core point + one key detail (the audio must stay listenable).
- Remove duplicate bullets / overlapping section cards.
- Do NOT merge distinct ideas or pad — count is not the target; distinct, tight notes are.

**Issue severity:**
- MAJOR: 3+ slides covering the same concept (true redundancy)
- MINOR: Slight bullet overlap, minor note repetition

### Dimension 3: Speaker Notes Quality (คุณภาพ Speaker Notes)

Speaker notes are the MOST IMPORTANT output — they become TTS voice-over for training videos.

**What to check:**

#### A. Length + repetition — VO must be descriptive but TIGHT (it's audio a person listens to)

Notes are spoken audio — a listener bores when they run long or repeat. Audit for **descriptive-but-
tight** and, above all, **no repetition across slides**. Three failure modes:
- **Repeats an earlier slide (the #1 defect — MAJOR):** re-teaches a concept, analogy, example, or
  timeline already covered on a previous slide. Scan the deck as a whole:
  - a `section` note that narrates the whole topic, then the next content slides re-tell it;
  - a `screenshot` note that re-explains the concept the previous content slide just taught, instead
    of describing the image + one new angle;
  - the same analogy (e.g. ตึก/เฟอร์นิเจอร์, ช่างแกะสลัก) reused on 3+ slides of a section.
  Fix: keep the teaching on ONE slide; make the others add a new facet or shorten to a reference.
- **Over-explains one point (MAJOR/MINOR):** three sentences where one does it, long setup scenarios,
  every nuance spelled out. Fix: land the core point + one key detail, cut the rest.
- **Too thin (MAJOR):** a bare one-liner for a concept the chapter details. Fix: add the core detail.

Target lengths for the SPOKEN note (over the top end usually = repetition or over-explaining):

| Slide Type | Target words |
|-----------|-------------|
| `cover` | 50-90 |
| `section` | 40-80 (a PREVIEW, not the whole story) |
| `content` / `two_column` | 90-150 |
| `process` | 100-160 |
| `table` / `callout` / `screenshot` | 70-120 |
| `quote` / `demo` | 40-90 |

**Flag both directions AND repetition.** A note well over target is over-explaining/repeating — trim.
A note far under for a detailed concept is too thin. And any note that re-teaches an earlier slide is
MAJOR regardless of its length.

#### B. TTS Naturalness — MALE SPEAKER ONLY
- Notes should sound like a **friendly male Thai trainer speaking in a workshop**
- **MALE particles only**: Use "ครับ" — NEVER "ค่ะ", "คะ", "นะคะ", "จ้า", "จ๊ะ" or any female particles
- Replace ALL female particles found: "ค่ะ" → "ครับ", "คะ" → "ครับ", "นะคะ" → "นะครับ", "จ้า" → "ครับ", "จ๊ะ" → "นะครับ"
- **NEVER start notes with "ครับคุณ"** — this is grammatically wrong Thai. "ครับ" goes at END of clauses
- Address listener as "คุณ" — direct second person
- Present tense, as if walking through together
- No robotic patterns like "ข้อแรก... ข้อสอง... ข้อสาม..."
- Male speech patterns: "ผม" (not "ฉัน/ดิฉัน"), "นะครับ" (not "นะคะ"), "ใช่ครับ" (not "ใช่ค่ะ")

#### C. Content — descriptive but TIGHT, and non-repetitive
Each note teaches THIS slide's point with its one key detail + an example, then stops — written for a
listener, so no over-explaining and (critically) **no re-teaching what another slide already covered.**
State the point → how/why with the key detail → a concrete example → a short bridge. ~3-6 sentences
for a content slide. Section notes PREVIEW (short); screenshot notes describe the image + one new
angle. Flag: repeats-an-earlier-slide, over-explained, or too-thin (see §A for the split).

#### D. Variety
- Don't start every note with the same phrase (check for repetitive "มาดูกัน", "ทีนี้", etc.)
- Good openers: vary them; but keep the opener short — don't spend two sentences setting up.

**How to fix:**
- **Under-written note** (thin vs. a concept the chapter details) → expand with the chapter's real
  substance: the how, the why, a concrete example/number.
- **Padded note** (repetition, filler, empty scenarios, bullets read verbatim) → cut the padding,
  keep the detail.
- Fix unnatural openings and vary opening phrases.

**Issue severity:**
- CRITICAL: Notes missing entirely, or a bare label with no explanation at all
- MAJOR: Under-written (chapter detail dropped), OR padded/repetitive/restates bullets verbatim
- MINOR: A repetitive opener, or slightly thin/padded in one spot

### Dimension 4: Slide Format Compliance (MD → YAML)

Check the `.slides.md` against `slide-md-format.md`, and confirm it **compiles** to YAML valid
per `yaml-format.md`. Fix problems in the MD, then recompile.

**What to check:**

#### A0. Markdown surface well-formed (`slide-md-format.md`)
- Deck front-matter present (`book`, `chapter`, `title`); each slide starts with a
  `<!-- slide: TYPE ... -->` directive; every `:::` block is closed; directives are single-line
- The MD compiles with no malformed-block errors

#### A. Structural (compile target — `yaml-format.md`)
- `meta` block has `book`, `chapter`, `title` (required)
- `slides` is a list of objects
- Every slide has `type` field
- Every slide has `notes` field (required — no exceptions) → from a `::: notes` block in the MD

#### B. Type-Specific Fields
| Slide Type | Required Fields |
|-----------|----------------|
| `cover` | chapter, title, subtitle |
| `quote` | text, attribution |
| `section` | number, title, cards (2-5 items) |
| `content` | title, bullets |
| `two_column` | title, left{header, bullets}, right{header, bullets} |
| `timeline` | title, events (3-5 items) |
| `process` | title, steps (2-6 items), each step has number/title/body |
| `table` | title, headers, rows |
| `callout` | style (tip/warning/concept), title, body |
| `demo` | subtitle |
| `screenshot` | screenshot OR image |
| `video_demo` | title, description |

#### C. Constraints
- Section cards: 2-5 (clamped)
- Process steps: 2-6 (clamped)
- Timeline events: 3-5 (clamped)
- Callout style: must be "tip", "warning", or "concept"

#### D. No Emoji
**CRITICAL**: No emoji anywhere in slide text fields or notes. Scan ALL text for:
- Unicode emoji: ✅ ❌ 🔄 ⏳ ⚡ 💡 📝 ⚠️ ✦ ⏹️ ▶ 🎯 📊 🔑 ➡️
- Replace with plain Thai text: "เคล็ดลับ:" instead of 💡, etc.
- Exception: ✦ ▲ ◆ are OK only in callout `style` rendering (handled by template), not in text

#### E. Image Coverage & Visual Accuracy (BOTH kinds)
- Extract ALL image placeholders from the source chapter `.md`: `{{screenshot:filename}}` (real UI)
  **and** `{{image:id}}` (AI figure).
- Extract ALL `screenshot:` values from the YAML.
- Every chapter image MUST appear on a slide: `{{screenshot:X.png}}` → `screenshot: X.png`;
  `{{image:id}}` → `screenshot: id.png` (file in `media/generated/`). **Never drop an image.**
- Filenames must match exactly (including subdirectory paths like `subagents/03.png`).

**Visual Verification of Screenshot Notes:**
For every `type: screenshot` slide, **`Read` the actual PNG file** from `media/screenshots/` to visually verify that the speaker notes match what's in the image:

```
Read: <workspace>/media/screenshots/<filename>.png
```

Check that:
- Notes reference UI elements that actually appear in the screenshot (buttons, labels, panels, text)
- Notes don't describe elements that aren't visible in the image
- Notes guide the learner's eyes to specific locations ("ตรงกลาง...", "ด้านซ้าย...", "สังเกตปุ่ม...")
- If the image is a mockup/placeholder, notes still describe the labeled elements accurately

**If notes don't match the image**, rewrite them based on what you actually see. This is a CRITICAL fix — inaccurate voice-over destroys learner trust.

#### F. YAML Syntax
- Block scalar `|` for multi-line text
- Strings with colons/brackets are quoted
- Consistent 2-space indentation
- No trailing spaces
- Valid YAML (parseable)

**How to fix:**
- Add missing required fields
- Fix constraint violations (e.g., section with 6 cards → merge to 5)
- Remove all emoji, replace with text
- Add missing screenshot slides
- Fix YAML syntax issues
- Quote unquoted strings with special characters

**Issue severity:**
- CRITICAL: Missing required fields, emoji in text, missing screenshots, invalid YAML
- MAJOR: Constraint violations, missing notes
- MINOR: Style inconsistencies, unquoted safe strings

### Dimension 5: Thai Proofreading (ตรวจภาษาไทย)

Proofread all Thai text in the YAML — titles, bullets, card bodies, and especially speaker notes.

**What to check:**

#### A. Spelling — MANDATORY GREP PRE-SCAN

**Before reading the YAML manually, run this grep scan to mechanically catch known misspellings.** This is non-negotiable — the LLM eye often misses Thai typos that grep catches reliably.

```bash
# Run this for EVERY chapter YAML file:
YAML_FILE="media/slides/ch{NN}.yaml"
echo "=== Scanning $YAML_FILE for known Thai misspellings ==="
grep -n 'สรุม' "$YAML_FILE"          # → สรุป (summarize)
grep -n 'เครื่อมือ' "$YAML_FILE"      # → เครื่องมือ (tool)
grep -n 'เคื่อง' "$YAML_FILE"        # → เครื่อง
grep -n 'ส้าง' "$YAML_FILE"          # → สร้าง (create)
grep -n 'ปลั๊กอิน' "$YAML_FILE"      # → Plugin (keep English)
grep -n 'พลักอิน' "$YAML_FILE"       # → Plugin
grep -n 'สกิล' "$YAML_FILE"          # → Skill (keep English)
grep -n 'คอนเนกเตอร์' "$YAML_FILE"   # → Connector (keep English)
grep -n 'ตัวเชื่อม' "$YAML_FILE"     # → Connector (keep English)
grep -n 'โคเวิร์ก' "$YAML_FILE"      # → Cowork (keep English)
grep -n 'อัพเดต' "$YAML_FILE"        # → อัปเดต (update, Royal Institute spelling)
grep -n 'อัพเดท' "$YAML_FILE"        # → อัปเดต
grep -n 'อัพโหลด' "$YAML_FILE"       # → อัปโหลด (upload)
grep -n 'ดาว์นโหลด' "$YAML_FILE"     # → ดาวน์โหลด (download)
grep -n 'ดาวโหลด' "$YAML_FILE"       # → ดาวน์โหลด
grep -n 'เซิร์ฟเวอร์' "$YAML_FILE"   # → เซิร์ฟเวอร์ is OK, but prefer "server" in tech context
grep -n 'แอพ ' "$YAML_FILE"          # → แอป (app, Royal Institute)
grep -n 'แอ็พ' "$YAML_FILE"          # → แอป
grep -n 'ประมาน' "$YAML_FILE"        # → ประมาณ (approximate)
grep -n 'โปรแกม' "$YAML_FILE"        # → โปรแกรม (program)
grep -n 'สะดวด' "$YAML_FILE"         # → สะดวก (convenient)
grep -n 'เหมาสม' "$YAML_FILE"        # → เหมาะสม (appropriate)
grep -n 'ข้อมุล' "$YAML_FILE"        # → ข้อมูล (data)
grep -n 'บันทุก' "$YAML_FILE"        # → บันทึก (save/record)
grep -n 'เบื้องตน' "$YAML_FILE"      # → เบื้องต้น (basic)
grep -n 'เพื่มเติม' "$YAML_FILE"     # → เพิ่มเติม (additional)
grep -n 'ประสิทะิภาพ' "$YAML_FILE"   # → ประสิทธิภาพ (efficiency)
grep -n 'ประสิธิภาพ' "$YAML_FILE"    # → ประสิทธิภาพ
grep -n 'ลักณะ' "$YAML_FILE"         # → ลักษณะ (characteristic)
grep -n 'แอปพลิเคชั่น' "$YAML_FILE"  # → แอปพลิเคชัน (no ่ on ชัน)
grep -n 'เเ' "$YAML_FILE"            # → แ (double Sara Ae is invalid Thai)
```

**Fix every match.** Every grep hit is a confirmed spelling error — no judgment needed, just fix it.

Also check manually for:
- Garbled text or corrupted characters (random consonant clusters that aren't Thai words)
- Wrong vowels/tone marks that grep can't catch
- Words that look Thai but are nonsense (read every speaker note aloud mentally)

#### B. Grammar
- Wrong classifiers, incomplete sentences
- Wrong prepositions, doubled words

#### C. Product Terminology
Keep in English: Claude, Cowork, Plugin, Skill, Connector, MCP, API, SDK, Gmail, Chrome, OAuth, SSO, URL, UI

Use Thai: ติดตั้ง, ตั้งค่า, เครื่องมือ, คำสั่ง, ไฟล์, โฟลเดอร์, หน้าจอ, หน้าต่าง

Correct terms:
| Term | Correct | Wrong |
|------|---------|-------|
| Cowork | "Cowork" | "โหมด Cowork", "Cowork mode" |
| Plugin | "Plugin" | "พลักอิน", "ปลั๊กอิน" |
| Skill | "Skill" | "สกิล", "ทักษะ" (when meaning Claude skill) |
| Connector | "Connector" | "คอนเนกเตอร์", "ตัวเชื่อม" |

#### D. Thai/English Mixing
- Space before AND after English words in Thai sentences
- No mid-word switches: "install แล้ว" not "installแล้ว"

#### E. Typography
- "ๆ" with space before: "ต่าง ๆ" not "ต่างๆ"
- Consistent punctuation

**How to fix:**
- **First**: Fix every grep hit from the pre-scan (these are guaranteed errors)
- **Then**: Apply manual spelling/grammar corrections
- Fix terminology to match style guide
- Fix spacing around English words
- Fix typography

**Issue severity:**
- CRITICAL: Known misspellings from grep scan (สรุม, ปลั๊กอิน, etc.)
- MAJOR: Wrong product terminology, garbled text
- MINOR: Spacing issues, minor grammar

## Audit & Fix Process

### For Each Chapter:

1. **Read the source chapter** `.md` — extract section order, screenshot list, key content
2. **Read the YAML file** — parse all slides
3. **Build a section map**: Map each `.md` section heading to its corresponding YAML slides
4. **Run all 5 dimensions** — collect issues with severity
5. **Fix all issues** — edit the YAML file directly:
   - For speaker notes rewrites: rewrite the entire notes block
   - For structural fixes: add/remove/reorder slides
   - For format fixes: correct fields, remove emoji
   - For Thai fixes: correct text in-place
6. **Validate YAML syntax** after all fixes:
```bash
python3 -c "import yaml; yaml.safe_load(open('media/slides/ch{NN}.yaml')); print('YAML OK')"
```
7. **Image cross-check (both kinds)**:
```bash
# Chapter images → expected screenshot filenames ({{screenshot:X.png}} + {{image:id}}→id.png):
{ grep -oP '(?<={{screenshot:)[^|}]+' chapters/ch{NN}.md;
  grep -oP '(?<={{image:)[^|}]+' chapters/ch{NN}.md | sed 's/$/.png/'; } | sort -u

# Slide screenshot fields:
grep 'screenshot:' media/slides/ch{NN}.yaml | sed 's/.*screenshot: *"\?\([^"]*\)"\?.*/\1/' | sort -u
# first set ⊆ second set
```
## Report Format

After fixing, report per chapter:

```
Chapter {N}: {title}
  Flow Sync:    {issues found} → {issues fixed}
  Redundancy:   {issues found} → {slides removed/merged}
  Notes Quality:{issues found} → {notes rewritten}
  YAML Format:  {issues found} → {issues fixed}
  Thai Proofread:{issues found} → {issues fixed}
  ─────────────────────────────────
  Total:        {total issues} found, {total fixed}, {unfixed} flagged for review
  Slides:       {before} → {after}
  Screenshots:  {count} (all matched: ✓/✗)
```

## Summary Table (for multiple chapters)

```
| Chapter | Flow | Redundancy | Notes | Format | Thai | Total Fixed | Slides | Screenshots |
|---------|------|------------|-------|--------|------|-------------|--------|-------------|
| Ch 2    | 3    | 2          | 5     | 1      | 4    | 15          | 22→20  | 8 ✓         |
| ...     |      |            |       |        |      |             |        |             |
```

## Key Constraints

- **No slide-count target** — never merge distinct ideas or pad to hit a number; let the content
  decide the length (see create-slide-markdown). Only merge slides that are genuinely redundant.
- **Never drop an image** — every `{{screenshot:}}` AND every `{{image:}}` from the `.md` must appear as a slide
- **Always keep `notes`** — every slide MUST have notes, no exceptions
- **Preserve slide `type`** — don't change a section slide to content unless structurally wrong
