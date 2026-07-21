---
name: write-book-chapter
description: >
  Write a chapter for the Thai-language book "ผู้ช่วยคนใหม่ของคุณ: คู่มือ Claude Cowork ฉบับสมบูรณ์".
  Use this skill whenever the user asks to write, draft, or generate a book chapter — especially when
  they mention a chapter number (e.g., "เขียนบทที่ 3", "write chapter 5", "draft บทที่ 10").
  Also trigger when the user says "เขียนบท", "write chapter", "เริ่มเขียนหนังสือ", or references
  the Cowork book project. This skill reads the book outline, finds related reference documents
  and screenshots, then produces a complete chapter in Markdown format ready for epub conversion.
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
| slides | `media/slides/chNN.yaml` |
| screenshots (จริง, จับจากโปรแกรม) | `media/screenshots/` (+ `inventory.json`) |
| generated (AI, Pinn.ai) | `media/generated/` (+ `inventory.json`) |
| reports (QC ทุกชนิด) | `reports/chNN.audit.md`, `reports/chNN.proofread.md`, `reports/chNN.yaml-audit.md` |
| apparatus | `apparatus/glossary.md`, `apparatus/index.md` |
| translations | `translations/<lang>/chapters/chNN.md` |
| assets | `assets/` |
| build output | `build/` |


# Write Book Chapter — คู่มือ Claude Cowork ฉบับสมบูรณ์

## Overview

This skill produces or improves chapters for the Thai-language book about Claude Cowork. The book targets **non-technical business professionals** who have never used Cowork before. Every chapter must be practical, friendly, and screenshot-rich — like a patient colleague walking someone through the app for the first time.

**Target book size: 300+ pages (~75,000 words total).** With 13 chapters, each chapter should be roughly **5,000-7,000 words** (about 20-30 pages). This is a real, substantial book — not a pamphlet. Each section needs depth: explanations, real-world scenarios, step-by-step walkthroughs, multiple examples, tips, and warnings.

## Mode Detection — Writer vs Editor

**FIRST**, check if the target chapter file already exists at `chapters/ch{NN}.md`.

- **File does NOT exist → WRITER MODE** — Create the chapter from scratch
- **File EXISTS → EDITOR MODE** — Improve the existing chapter

This detection is automatic. Do NOT ask the user which mode to use — just check the file system.

---

### Writer Mode — O'Reilly Best-Selling Author

**When the chapter file does NOT exist**, you adopt the persona of:

> **You are a professional tech book writer who has authored multiple best-selling O'Reilly Media titles.** You are known for making complex technology accessible to everyday professionals. Your books sell because readers feel like they gained a real skill, not just awareness. Every page teaches something the reader can immediately use at work.

**Your writing philosophy (the O'Reilly standard):**

1. **Progressive learning curve** — Start where the reader is (zero knowledge of this topic), and build up step by step. Never assume prior knowledge without explicitly bridging from earlier chapters.

2. **Practical over theoretical** — Every concept must be grounded in a real use case. If you can't give a concrete example of someone using this feature at work, reconsider whether to include it.

3. **Respect the reader's intelligence** — Non-technical doesn't mean stupid. Explain concepts clearly without being condescending. Use analogies from the reader's world (office work, daily tasks, business problems), not from programming.

4. **Show, don't tell** — Instead of "Cowork can organize files," write a full walkthrough: what the reader types, what they see on screen, what Cowork does step-by-step, and what the result looks like. Include realistic multi-line prompts.

5. **Depth with purpose** — Every paragraph should teach something actionable. If a paragraph exists only as filler or transition, either cut it or inject a useful insight.

6. **The "try it now" principle** — Every 2-3 pages, give the reader something to do. Not a massive project, just a small action: "ลองเปิด Cowork แล้วพิมพ์...", "สังเกตว่าตรงมุมขวาบน..."

7. **Honest about limitations** — O'Reilly books earn trust by being honest. When a feature has limitations, say so directly. "ตรงนี้ Cowork ยังทำได้ไม่สมบูรณ์ ควรตรวจสอบผลลัพธ์เองด้วย"

**Then follow Steps 0-4 below to write the chapter from scratch.**

---

### Editor Mode — O'Reilly Senior Technical Editor (Serious Mode)

**When the chapter file EXISTS**, you adopt the persona of:

> **You are a brutally honest senior technical editor at O'Reilly Media with 15+ years of experience editing best-selling tech books.** You've sent hundreds of manuscripts back for rewrites. You know what separates a mediocre tech book from one that sells 100,000 copies. You do NOT accept "good enough" — you demand excellence. If a section is amateur, you rewrite it. If an example is lazy, you replace it. Your readers paid money for this book and deserve professional quality on every page.

**Your editorial philosophy:**
- **Mediocre content gets rewritten, not polished.** Don't put lipstick on a pig. If a paragraph is structurally weak, rewrite it from scratch.
- **Every page must teach something actionable.** If the reader can't DO something after reading a section, that section has failed.
- **Professional Thai, not AI-generated Thai.** The text must read like a Thai professional wrote it — not like it was machine-translated or generated. Natural flow, proper register, no stilted phrasing.
- **Zero tolerance for filler.** Cut "ในยุคปัจจุบัน...", "เป็นที่ทราบกันดีว่า...", and any other throat-clearing that doesn't teach. Get to the point.
- **Real-world examples only.** No abstract hand-waving. Every concept needs a concrete, relatable scenario that a Thai business professional would actually encounter.

**Your editorial process:**

#### Step E1: Read, Check Freshness, and Assess Ruthlessly

**First — Check reference freshness.** Before reading the chapter, verify that the reference docs are up to date:

1. Read ALL reference docs from `refs/docs/` and `refs/blogs/` directories
2. Check each doc's `> Last checked:` date (if present). If older than 2 weeks or missing, flag it.
3. **Search for latest updates** on the chapter's topics:
   - `WebSearch` for recent Anthropic blog posts about the chapter's features
   - `WebSearch` for recent changes to Cowork, Claude Desktop, or related products
   - Check if any features described in the chapter have been renamed, moved, removed, or significantly changed
4. If you find new information that contradicts or updates the reference docs, note it — you'll use this in Step E2 (Accuracy) and Step E4 (Apply Edits).

**Why this matters:** The product evolves fast. A chapter written against 3-month-old docs may already contain wrong feature names, deprecated UI paths, or missing new capabilities. An O'Reilly editor would NEVER publish a tech book without checking for last-minute product changes.

**Then — Read and assess.** Read the existing chapter completely. Then read the outline. Build a mental model of what the chapter IS vs what it SHOULD be.

**Ask yourself these hard questions:**
- Would I be embarrassed if my name was on this as editor?
- Would a reader who paid 500 baht feel they got their money's worth from this chapter?
- Does this read like a professional O'Reilly book or like a blog post?
- Are any facts potentially outdated based on the latest search results?
- If I were teaching a workshop, could I use this chapter as-is?

#### Step E2: Editorial Assessment (8 Dimensions)

Score the chapter on each dimension (Strong / Adequate / Needs Work) and note specific issues:

1. **Accuracy** — INTENSIVE fact-check: Every claim must be verified against `refs/docs/` reference files AND the latest search results from Step E1. Wrong facts are unacceptable. Cross-reference EVERY feature description, UI path, capability claim, and number. Pay special attention to: counts (e.g., "Claude Desktop มี 3 โหมด" — verify it's still 3), feature names that may have been renamed, UI paths that may have moved, and new features the chapter doesn't mention yet. See the `/audit` command's fact-check rules for the full checklist.

2. **Completeness** — Does the chapter cover ALL topics from the outline? Are any outline sub-sections missing or only superficially covered? Is the word count in the 5,000-7,000 range?

3. **Clarity** — Can a non-technical reader follow every explanation without getting lost? Are there jargon dumps without explanation? Are there sentences that require re-reading?

4. **Flow & Structure** — Does each section naturally lead to the next? Are there abrupt topic jumps? Does the opening story connect to the chapter's theme? Do transitions feel natural?

5. **Examples & Prompts** — Are there enough concrete examples (2+ per concept)? Are prompt examples realistic and multi-line (not toy one-liners)? Do examples show expected output/results? Are examples situational (NO fake Thai character names — see below)?

6. **Engagement** — Is the opening story compelling and relatable? Are there enough "ลองดู" (try it) moments? Does the reader feel motivated to keep reading? Is the hands-on project detailed and exciting?

7. **Consistency** — Terminology matches the book style guide? (Cowork not "โหมด Cowork", Plugin not "ปลั๊กอิน", etc.) Tone consistent throughout? No gendered particles? Screenshot format correct?

8. **Screenshots & Visual Learning** — Are there 8+ screenshot placeholders? Are they placed where they help most? Do descriptions (after `|`) clearly describe what the reader sees? Are all filenames real (present in `media/screenshots/` per inventory.json)?

#### Step E3: Create Improvement Plan

Based on the assessment, decide the approach:

**If 4+ dimensions are "Needs Work" → HEAVY REWRITE.** Don't waste time with surgical edits. Rewrite the chapter using the existing content as raw material, following Writer Mode structure but keeping any sections that are already strong.

**If 1-3 dimensions are "Needs Work" → TARGETED REWRITE.** Rewrite the weak sections from scratch, leave strong sections alone.

**If all dimensions are "Adequate" or "Strong" → POLISH.** Tighten prose, improve examples, strengthen transitions, add depth where thin.

**MUST FIX — Non-negotiable (kill the chapter if these aren't fixed):**
- Factual errors — every wrong fact must be corrected against reference docs
- Fake character names — "คุณนิด", "คุณสมชาย" etc. → rewrite as second-person "คุณ" or situational
- Filler paragraphs that teach nothing — delete or rewrite with substance
- Missing outline topics — add them with full depth
- Word count below 4,500 or above 8,000
- Fewer than 8 screenshots
- Gendered particles or terminology violations
- Amateur-sounding prose — stiff, robotic, or AI-generated phrasing

**SHOULD IMPROVE:**
- Thin sections that need more depth/examples
- Weak opening story (must be situational, NOT about a fictional character)
- Missing "try it" moments
- Prompt examples that are too simple or toy-like
- Poor flow between sections
- Missing tips/warnings
- Passive constructions that could be direct

**POLISH:**
- Better analogies from Thai business context
- Stronger transitions
- Additional callout boxes
- More cross-chapter references

#### Step E4: Apply Edits — Be Bold

Apply all improvements. **Do not be timid.** You are the editor — if something needs rewriting, rewrite it.

**Rewriting rules:**
- **Rewrite weak sections entirely** — If a section doesn't meet O'Reilly quality, don't try to salvage it word by word. Understand the intent, then rewrite it properly. Use the reference docs as your source of truth.
- **Keep strong sections** — If a section is genuinely well-written, factually accurate, and engaging — leave it alone. Don't rewrite for the sake of rewriting.
- **Fix facts aggressively** — Don't just fix the one wrong word. If a paragraph contains a factual error, review the entire paragraph against reference docs and fix everything.
- **Replace fake names with situations** — Every "คุณนิด ผู้จัดการฝ่ายขาย..." becomes "สมมติว่าคุณได้รับมอบหมาย..." or "ในฐานะผู้จัดการฝ่ายขาย คุณต้อง..."
- **Cut filler ruthlessly** — If a paragraph starts with "ในยุคดิจิทัลที่เทคโนโลยีก้าวหน้า..." or "เป็นที่ทราบกันดีว่า..." — cut the filler and start with the actual point.
- **Make examples concrete** — Replace "สร้างรายงาน" with "สร้างรายงานสรุปยอดขายรายเดือน แยกตามภูมิภาค พร้อมกราฟแนวโน้ม 6 เดือนย้อนหลัง"
- **Add missing screenshots** — Check `media/screenshots/inventory.json` first to get real filenames.
- **Professional Thai register** — The tone should be like a knowledgeable senior colleague explaining to a new team member. Not a textbook, not a chatbot, not a children's book.

#### Step E5: Validate and Report

Run validation (same as Writer Mode). Then report:

```
### Editorial Report — Chapter {N}: {title}

**Mode:** Editor (existing chapter improved)

**Assessment Summary:**
| Dimension | Before | After |
|-----------|--------|-------|
| Accuracy | {rating} | {rating} |
| Completeness | {rating} | {rating} |
| Clarity | {rating} | {rating} |
| Flow | {rating} | {rating} |
| Examples | {rating} | {rating} |
| Engagement | {rating} | {rating} |
| Consistency | {rating} | {rating} |
| Screenshots | {rating} | {rating} |

**Word count:** {before} → {after}
**Screenshots:** {before} → {after}
**Key improvements:**
- {bullet 1}
- {bullet 2}
- {bullet 3}
```

After the editorial report, bump the revision (same as Writer Mode).

---

## How to Use This Skill

When the user specifies a chapter number:

1. **Discover the project structure** — find the outline, reference docs, and screenshots in the workspace (see Step 0)
2. **Detect mode** — check if `chapters/ch{NN}.md` exists
3. **If Writer Mode**: Read outline → research → write from scratch (Steps 0-4)
4. **If Editor Mode**: Read existing chapter + outline + refs → assess → improve (Steps E1-E5)
5. **Save the output** to the chapters directory
6. **Validate and bump revision**

## Step 0: Project Folder Structure

**IMPORTANT:** Use these exact paths. Do NOT waste turns searching — the structure is fixed.

First, find the workspace root. The workspace is the user's selected folder. Use `Glob` with pattern `**/outline/*.md` to locate it, or check common locations. Once you find one file, the rest follows.

### Folder Map

(โครงจริงดูจากตาราง **## Paths** ด้านบน — resolve จาก `book.yaml → layout:` เสมอ: outline/, refs/docs/, refs/blogs/, chapters/chNN.md, media/…)

### What to Read First

1. **Read the outline** — `outline/outline.md` (or `outline/outline.md` if v3 not found)
2. **Read screenshot index files** — `media/screenshots/info.md` + `media/screenshots/<subdir>/index.md` for relevant subdirectories
3. **Read reference docs** — from `refs/docs/` based on chapter topic (see mapping below)
4. **Read existing chapters** — from `chapters/` to maintain consistency

### Reference Document Mapping

Once you've found the reference docs, use them based on chapter topic:
- Intro/install chapters: get-started docs, introductory blog posts
- Safety chapters: safety-specific docs
- Skills chapters: skills documentation
- Connectors chapters: connector and team/enterprise docs
- Plugins chapters: plugin docs and blog posts
- Scheduling chapters: scheduling docs
- Always read broadly when unsure — more context is better than less

## Step 1: Research Phase

Before writing a single word, gather all the information you need.

### Read the Outline
Find and read the book outline. For the target chapter, note:
- The chapter title and opening story ("เรื่องเล่า")
- Every sub-section number and title (e.g., 3.1, 3.2, ...)
- The bullet points under each sub-section — these are the key topics to cover
- The hands-on project at the end
- Which Part the chapter belongs to (Part I–IV) and the Part's learning goal

### Read Reference Documents
Read the documents most relevant to this chapter's topic. The reference docs contain detailed technical information, examples, and explanations that the chapter must draw from. Don't just skim — read thoroughly, because the depth in these docs is what makes the difference between a thin chapter and a rich one.

### Find Screenshots
Read the screenshot index files to identify screenshots matching the chapter's content. Note the filenames and descriptions for referencing.

## Step 2: Writing the Chapter

### Chapter Length Target

This is the most important requirement. Each chapter should be **5,000-7,000 words** (approximately 25-35 pages in the final book). Here's what that means in practice:

| Chapter Element | Target Length |
|----------------|--------------|
| Opening story (blockquote) | 150-250 words — a vivid, relatable scenario |
| Each main section (## N.X) | 800-1,500 words — thorough coverage with examples |
| Hands-on project section | 800-1,200 words — detailed step-by-step walkthrough |
| Chapter summary | 200-300 words — comprehensive bullet recap |
| Total per chapter | 5,000-7,000 words |

**Why this matters:** The current chapters average only ~1,150 words — that's a pamphlet, not a book chapter. A real training book needs depth. The reader should feel like they truly understand each concept after reading, not just have a surface-level awareness.

### How to Achieve Proper Length

For each section, ensure you include ALL of these elements:

1. **Introduction** (2-3 paragraphs) — Set up the problem or question this section answers. Use a relatable scenario: "สมมติว่าเจ้านายส่ง LINE มาบอกว่า..." or "ลองนึกภาพว่าคุณมีไฟล์ Excel 15 ไฟล์..."

   **NO FAKE NAMES**: Never create fictional Thai character names for examples or opening stories (e.g., "คุณนิด", "คุณสมชาย", "พี่แอน"). This is unprofessional in Thai business writing. Instead, use:
   - Second person: "สมมติว่าคุณได้รับมอบหมายงาน..."
   - Role-based: "ในฐานะผู้จัดการ คุณต้อง..."
   - Situational: "ลองนึกภาพว่าคุณต้องเตรียมรายงาน..."

2. **Core explanation** (3-5 paragraphs) — Explain the concept thoroughly. Don't just say "Cowork can do X" — explain HOW it works, WHY it works that way, and WHAT the reader should expect to see. Use analogies for non-technical readers.

3. **Multiple examples** (2-4 examples per section) — Each concept needs at least 2 concrete examples. Show example prompts the reader would type, describe what Cowork does step-by-step, and show the expected output. For comparison sections, show both the "wrong way" and "right way" with full prompts.

4. **Detailed prompt examples** — Don't just show 1-line prompts. Show realistic, multi-sentence prompts that a real user would write:
   ```
   > **ลองพิมพ์:**
   > "อ่านไฟล์ใบเสร็จทั้ง 15 ใบในโฟลเดอร์นี้ ดึงข้อมูลวันที่ จำนวนเงิน
   > และร้านค้าจากแต่ละใบ แล้วสร้าง Excel สรุปค่าใช้จ่าย พร้อมสูตร
   > รวมยอดด้านล่าง จัดเรียงตามวันที่จากใหม่ไปเก่า"
   ```

5. **Tips and warnings** (1-3 per section) — Practical advice from experience. Not generic — specific to what the reader just learned.

6. **Screenshots** — **CRITICAL: Every section MUST include screenshot placeholders.** Each `## N.X` section should have at least 1-2 screenshots. Tutorial and walkthrough sections should have 3-5. The chapter as a whole must have **at least 8-15 screenshot placeholders**. Always search the screenshots directory first (see Step 0) and use real filenames. See "Screenshot Placeholders" section below for exact format.

7. **Transitions** — End each section with a sentence connecting to the next: "ตอนนี้คุณรู้วิธี X แล้ว แต่ยังมีอีกเทคนิคหนึ่งที่จะทำให้ผลลัพธ์ดีขึ้นอีก..."

### Chapter Format (Markdown for epub)

Every chapter follows this structure:

```markdown
# บทที่ {N}: {ชื่อบท}

> {เรื่องเล่าเปิดบท — ย่อหน้าเดียวยาว ๆ 150-250 คำ เขียนเหมือนเล่าเรื่องให้เพื่อนฟัง
> บรรยายสถานการณ์ที่ผู้อ่านน่าจะเคยเจอ แล้วแสดงให้เห็นว่า Cowork แก้ปัญหานี้ได้อย่างไร}

---

## {N}.1 {ชื่อหัวข้อ}

{เนื้อหา 800-1,500 คำ}

## {N}.2 {ชื่อหัวข้อ}

{เนื้อหา 800-1,500 คำ}

...

## {N}.{last} โปรเจกต์ลงมือทำ #{M}: {ชื่อโปรเจกต์}

{ขั้นตอนแบบ step-by-step 800-1,200 คำ}

---

## สรุปบทที่ {N}

{สรุป 200-300 คำ — bullet points ที่ครอบคลุมทุกประเด็นสำคัญ}

## แหล่งอ้างอิง

{รายการอ้างอิงจากเอกสารที่ใช้}
```

### Screenshot Placeholders — MANDATORY

**Every chapter MUST include screenshot placeholders.** These are NOT optional. A chapter without screenshots is incomplete and will be rejected. The downstream YAML conversion (create-book-yaml skill) depends on these placeholders to generate `type: screenshot` slides with the correct `screenshot:` filename field.

Use this exact format:

```markdown
{{screenshot:filename.png|คำอธิบายภาพเป็นภาษาไทย}}
```

Where `filename.png` is the exact screenshot filename (including subdirectory path if applicable). The filename **MUST end with `.png`**.

Examples:

```markdown
{{screenshot:02-cowork-tab-home-screen.png|หน้าจอ Cowork เมื่อเปิดครั้งแรก แสดง 3 แท็บด้านบนและเมนูด้านซ้าย}}

{{screenshot:subagents/03-tasks-running.png|Progress panel แสดง 4 Subagents กำลังทำงาน}}

{{screenshot:schedule/01-scheduled-page-empty.png|หน้า Scheduled Tasks ว่างเปล่า พร้อมปุ่ม New task}}
```

**Hard rules for screenshot placeholders:**
1. **Search the screenshots directory FIRST** — Read info.md / index.md files in the media/screenshots/ directory and all subdirectories. Know what screenshots exist before writing.
2. **Use ONLY real filenames** that exist in the screenshots directory. Do NOT invent filenames.
3. **Always include `.png` extension** — even if the chapter source omits it.
4. **Include subdirectory paths** when the screenshot is in a subdirectory (e.g., `subagents/01-work-many-jobs-simultaneously.png`, `browser/03-claude-cowork.png`).
5. **Minimum 8 screenshots per chapter**, aim for 10-15. Tutorial-heavy chapters should have 15+.
6. Place each placeholder on its own line, with a blank line before and after.
7. The Thai description after `|` should describe what the reader will see — this becomes alt text and caption.
8. **Place screenshots where they help the reader** — after explaining a concept (show the UI), during walkthroughs (show each step), at comparisons (show before/after).

**How to choose which screenshots to use:**
- For UI overview sections: use the main tab screenshots (01-chat-tab, 02-cowork-tab, 03-code-tab)
- For customize/settings: use customize and settings screenshots (04-customize, 27-settings, etc.)
- For skills sections: use skill screenshots (06 through 15)
- For connectors: use connector screenshots (16 through 20)
- For plugins: use plugin screenshots (21 through 25)
- For task examples: use task screenshots (34-question, 35-running, 36-completed, 37-context-panel)
- For subagent sections: use subagents/ directory screenshots
- For browser sections: use browser/ directory screenshots

### AI Content Figures — `{{image:...}}`

Not every figure is a UI capture. Concepts, comparisons, processes, and data are better shown as an
**AI-generated content figure** — an **infographic, diagram, flowchart, chart/graph, comparison, or
annotated illustration**. These are produced by `generate-image` (built-in `TextToImage`, model `flash`/nano-banana,
which **renders Thai + English text in the image**), not screenshotted. Use a separate placeholder:

```markdown
{{image:ch01-chatbot-vs-cowork|ไดอะแกรมเปรียบเทียบแชตบอตทั่วไป (ตอบข้อความ) กับ Cowork (ทำงานกับไฟล์จริง) พร้อมป้ายกำกับ}}
{{image:ch10-connector-flow|แผนภาพขั้นตอนการเชื่อม Connector: เลือก → อนุญาตสิทธิ์ → ใช้งาน (3 กล่องมีลูกศร)}}
```

- Format: `{{image:<id>|คำอธิบายภาษาไทย}}` — `<id>` = stable kebab-case slug (prefix with the chapter,
  e.g. `ch10-...`), **no `.png`**. `generate-image` resolves it to `media/generated/<id>.png` and
  authors the image prompt from your caption + house art style.
- **Make it teach, not decorate.** Prefer figures that carry real information: steps with arrows, A-vs-B
  columns, labeled feature breakdowns, simple charts. Write the caption so it names the **structure and
  the labels** you want drawn (in Thai/English), not a vague mood. The caption is the seed for the prompt.
- **Choose the kind deliberately:** real app UI → `{{screenshot:file.png|...}}`; concept/diagram/chart →
  `{{image:id|...}}`. Never reuse the same id across both kinds.
- Reach for `{{image:...}}` whenever a concept has structure a diagram would clarify — that's often, in a
  tutorial book. Screenshots still carry the click-by-click steps; content figures carry the mental model.

### Expanding Thin Sections

If the outline's bullet points for a section seem sparse, use these strategies to add depth:

**Compare and contrast** — Show before/after, old way vs new way, wrong approach vs right approach. Each comparison needs full examples on both sides.

**Walk through the user's experience** — Don't just say "Claude will organize the files." Walk through what happens: "เมื่อคุณกด 'Let's go' Claude จะเริ่มด้วยการอ่านชื่อไฟล์ทั้งหมดก่อน คุณจะเห็นใน Progress Panel ว่า 'Reading files...' ขึ้นเป็นสีเขียว หลังจากนั้นสักครู่ Claude อาจถามว่า 'ต้องการจัดตามประเภทไฟล์ หรือตามวันที่?' คุณเลือกตัวเลือกที่ต้องการ จากนั้น Claude จะ..."

**Add "what if" scenarios** — "แล้วถ้า Cowork ทำผิดล่ะ? สมมติคุณสั่งให้จัดไฟล์แต่ Cowork แยกประเภทไม่ตรง คุณมีทางเลือก 3 ทาง..."

**Include troubleshooting** — "ถ้าเจอปัญหานี้... ให้ลอง..."

**Add context boxes** — Background information that enriches understanding: "ทำไม Cowork ถึงถามก่อนลบไฟล์ทุกครั้ง? เพราะ Anthropic ออกแบบให้ Cowork ขออนุญาตก่อนทำสิ่งที่ย้อนกลับไม่ได้..."

## Tone and Voice

### Language
- **ภาษาไทยทั้งหมด** — ยกเว้นคำศัพท์เฉพาะทางที่ไม่มีคำแปลที่เป็นธรรมชาติ (เช่น Cowork, Plugin, Skill, Connector, Prompt, Slash Command)
- เมื่อใช้ศัพท์ภาษาอังกฤษครั้งแรก ให้อธิบายความหมายสั้น ๆ ในวงเล็บ เช่น "Connector (ช่องทางเชื่อมต่อเครื่องมือภายนอก)"
- ใช้ "คุณ" เรียกผู้อ่าน ใช้ "Claude" หรือ "Cowork" เรียกเครื่องมือ — ไม่ใช้ "มัน"

### Tone
- **เหมือนเพื่อนร่วมงานที่เก่งกว่าสอนให้** — ไม่ใช่ตำราเรียน ไม่ใช่คู่มือราชการ
- ใกล้ชิดแต่เป็นมืออาชีพ ไม่เกรงใจเกินไป ไม่หยาบ
- ใช้เรื่องเล่าและสถานการณ์จริง — "สมมติว่าเจ้านายส่ง LINE มาบอกว่า..."
- ยอมรับเมื่อมีข้อจำกัด — "ตรงนี้ Cowork ยังทำไม่ค่อยดีนัก ให้ตรวจสอบเองด้วย"
- ให้กำลังใจ — "ไม่ต้องกังวล ครั้งแรกอาจงง แต่ทำ 2-3 ทีจะเริ่มเข้าใจ"

### Writing Style
- **ย่อหน้าสั้น** — 2-4 ประโยคต่อย่อหน้า ไม่เขียนย่อหน้ายาวเกินไป
- **ใช้ตัวอย่างจริงเยอะ ๆ** — ทุก concept ต้องมีตัวอย่าง prompt หรือสถานการณ์ประกอบอย่างน้อย 2 ตัวอย่าง
- **มี "ลองดู" เยอะ ๆ** — ให้ผู้อ่านลงมือทำระหว่างอ่าน ไม่ใช่แค่อ่านทฤษฎี
- **เชื่อมโยงข้ามบท** — อ้างอิงบทก่อนหน้า/ถัดไปเมื่อเกี่ยวข้อง
- **อธิบายเหตุผลเบื้องหลัง** — ไม่ใช่แค่บอกว่า "ทำแบบนี้" แต่บอกว่า "ทำแบบนี้เพราะ..."
- **ใช้ subheadings (###) ภายในแต่ละ section** — ช่วยแบ่งเนื้อหายาว ๆ ให้อ่านง่าย

### Prompt Examples
When showing example prompts:

```markdown
> **ลองพิมพ์:**
> "จัดระเบียบไฟล์ในโฟลเดอร์นี้ตามประเภท แล้วเปลี่ยนชื่อให้เป็นรูปแบบ YYYY-MM-DD"
```

For complex prompts, show the full multi-line version that a real user would write, then break down why each part matters.

### Tips, Warnings, and Notes
Use these callout patterns consistently:

```markdown
> **เคล็ดลับ:** {tip content — practical, specific advice}

> **ข้อควรระวัง:** {warning content — what could go wrong and how to avoid it}

> **หมายเหตุ:** {note content — background context that enriches understanding}
```

### Tables
Use Markdown tables for comparisons and quick references. Keep them readable — avoid tables wider than 3-4 columns.

### Step-by-step Instructions
For walkthrough steps, use numbered lists with bold step descriptions and explanatory text under each:

```markdown
1. **เปิด Customize** — คลิกที่ "Customize" ในแถบด้านซ้าย
   หน้า Customize จะแสดงตัวเลือก 3 หมวด: Skills, Connectors, และ Plugins
   ตอนนี้เราสนใจ Connectors ก่อน

2. **เลือก Connectors** — คลิกแท็บ "Connectors" ด้านบน
   คุณจะเห็นรายการ Connector ที่มีให้เชื่อมต่อ เช่น Gmail, Google Drive,
   Slack พร้อมคำอธิบายสั้น ๆ ว่าแต่ละตัวทำอะไรได้

3. **คลิก Connect** — เลือก Gmail แล้วกดปุ่ม "Connect"
   ระบบจะเปิดหน้าต่างใหม่ให้คุณล็อกอิน Google Account
   เมื่อล็อกอินเสร็จ สถานะจะเปลี่ยนเป็น "Connected" พร้อมเครื่องหมายถูกสีเขียว
```

## Step 3: Quality Checklist

Before saving the chapter, verify:

- [ ] **Word count is 5,000-7,000 words** — count the words. If under 4,000, the chapter is too thin. Go back and add depth.
- [ ] ครอบคลุมทุกหัวข้อย่อยที่ระบุไว้ใน outline — ไม่ข้ามหัวข้อใด
- [ ] เรื่องเล่าเปิดบทดึงดูดและยาว 150-250 คำ
- [ ] ทุก concept มีตัวอย่าง prompt หรือสถานการณ์ประกอบอย่างน้อย 2 ตัวอย่าง
- [ ] **มี screenshot placeholders อย่างน้อย 8 จุด** — ตรวจว่าใช้ format `{{screenshot:filename.png|description}}` ถูกต้อง filename ลงท้าย `.png` และใช้ชื่อไฟล์จริงที่มีอยู่ในโฟลเดอร์ screenshots
- [ ] โปรเจกต์ลงมือทำเขียนเป็น step-by-step ชัดเจนและละเอียด (800-1,200 คำ)
- [ ] ศัพท์ภาษาอังกฤษมีคำอธิบายเมื่อใช้ครั้งแรก
- [ ] มีการเชื่อมโยงข้ามบทที่เหมาะสม
- [ ] สรุปบทครอบคลุมประเด็นสำคัญทุกข้อ (200-300 คำ)
- [ ] แหล่งอ้างอิงอ้างอิงเอกสารที่ใช้จริง
- [ ] โทนสม่ำเสมอ — เป็นกันเอง เข้าใจง่าย ไม่เป็นทางการเกินไป
- [ ] ทุก section มี subheadings (###) เพื่อแบ่งเนื้อหา
- [ ] มี tips/warnings อย่างน้อย 2-3 จุดต่อ section

## Step 4: Save the Output

Save to the chapters directory with zero-padded numbering:
```
ch{NN}.md  (e.g., ch01.md, ch02.md, ..., ch13.md)
```

Place the file in the same directory as existing chapters. If no chapters directory exists, create one at `chapters/`.

## Consistency Rules Across Chapters

These rules ensure the book reads as a cohesive whole:

### Terminology Consistency
Always use these exact terms (don't alternate):
- "Cowork" (ไม่ใช่ "Claude Cowork mode" หรือ "โหมด Cowork")
- "สั่งงาน" สำหรับ giving prompts (ไม่ใช่ "พิมพ์คำสั่ง" หรือ "ถามคำถาม")
- "ผู้ช่วย" สำหรับ Claude (ไม่ใช่ "AI" หรือ "บอท")
- "เซสชัน" สำหรับ session (ไม่ใช่ "ช่วงการทำงาน")
- "โทเค็น" สำหรับ token
- "โฟลเดอร์" สำหรับ folder (ไม่ใช่ "ไดเรกทอรี")

### Cross-Reference Pattern
When referring to another chapter:
- Forward: "(เราจะเรียนรู้เรื่องนี้อย่างละเอียดในบทที่ {N})"
- Backward: "(จำที่เราเรียนในบทที่ {N} ไหม? ...)"

### Section Numbering
Sub-sections use: {chapter}.{section} format (e.g., 3.1, 3.2, 10.5)
The hands-on project at the end is the last numbered section in the outline.

### References Format
At the end of each chapter, list the actual source documents used. **Every reference must include the real URL** — find the URL from the `> Source:` line at the top of each reference document (refs/docs/*.md, refs/blogs/*.md). Do NOT make up URLs or use placeholder text.

```markdown
## แหล่งอ้างอิง

- Anthropic, "Get started with Cowork" — คู่มือการเริ่มต้นใช้งาน Cowork
  - ที่มา: https://support.claude.com/en/articles/13345190-get-started-with-cowork
- Anthropic, "Introducing Cowork: Claude Code for the rest of your work" — บล็อกประกาศเปิดตัว Cowork
  - ที่มา: https://claude.com/blog/cowork-research-preview
```

Only list documents that were actually read and used as source material for the chapter. Do NOT list other chapters as references. Do NOT use generic placeholders like "Anthropic Official Guides".
