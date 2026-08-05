---
name: write-book-chapter
description: >
  Write or edit a chapter for any book in the thai-book-production pipeline. Uses
  conventions from `book.yaml`, the outline, and reference docs — works for any
  subject (software, AI, business, howto, vision/trends). Use when the user asks to
  write, draft, edit, or improve a chapter — specify the chapter number or title.
  Automatically detects whether the chapter file exists (Editor mode) or not
  (Writer mode).
---

## Paths (thai-book-production layout)

Resolve every path from `book.yaml → layout:` at the project root. Defaults:

| what | path |
|------|------|
| chapters | `chapters/chNN.md` |
| outline | `outline/outline.md`, `outline/plan.md` |
| references | `refs/docs/`, `refs/blogs/` |
| generated images (AI) | `media/generated/` (+ `inventory.json`) |
| screenshots (real captures) | `media/screenshots/` (+ `inventory.json`) |
| reports | `reports/chNN.audit.md` etc. |

## Before writing — ALWAYS read these

1. **Outlines** — `outline/outline.md` + `outline/plan.md` for the chapter's subtopics,
   learning objectives, and page_target from `book.yaml → chapters[id].page_target`
2. **Reference docs** — ALL `refs/docs/` and `refs/blogs/` files mapped to this chapter
   (check outline's inventory table or chapter-source-map). Skip none.
3. **Existing chapters** — at least the immediately preceding chapter, for tone and
   cross-reference consistency
4. **Thai style** — `{skill_dir}/references/thai-style.md` (banned calques, preferred wording)

**Hard rule: never write without reading refs first.** Facts, numbers, quotes, and examples
must be grounded in reference docs. If a ref is missing, say so and stop.

## Conventions (all books)

Every chapter follows this structure. The conventions are book-agnostic — they work
for tutorials, vision/trends books, technical howtos, and business books alike.

### Chapter format

```markdown
# บทที่ {N}: {title}

> {Opening story — one long blockquote paragraph (~150-250 words). Paint a vivid
> scenario the reader can relate to, then show how this chapter's topic addresses it.
> Write like telling a story to a colleague — concrete, personal, engaging.}

---

## {N}.1 {section title}

{content — aim for roughly page_target ÷ section_count per section}

### {subsection title}

{use H3 subsections to break up long sections into digestible chunks}

## {N}.2 {section title}

...

---

## สรุปบทที่ {N}

{Bullet-point recap covering every key takeaway — 200-300 words}

## แหล่งอ้างอิง

- {Author/Publisher}, "{title}" — {one-line description}
  - ที่มา: {real URL from the reference doc's Source line}
```

### Page length

Target is set per chapter in `book.yaml → chapters[id].page_target`. The standard
word-per-page count is project-specific — check `outline/plan.md` for the agreed
number (default 400 words/page for Thai prose). Aim for page_target ±20%.

### Opening story (blockquote)

- One paragraph, 150-250 words, in a markdown blockquote (`> `)
- Set a relatable scene — not abstract, not about a fictional character
- Use second person ("คุณ") or role-based scenarios
- Connect the scene to what the chapter teaches

### Section structure

- Every `###` subsection = one digestible idea
- Introduce with a relatable scenario or question
- Explain the concept thoroughly
- Ground claims in reference docs (facts, numbers, quotes)
- End with a transition to the next section

### Images — two kinds

**AI-generated figures** (`{{image:...}}`) — infographics, diagrams, flowcharts, comparisons:
```markdown
{{image:chNN-concept|คำอธิบายภาษาไทยว่าภาพนี้แสดงอะไร — จะถูกใช้เป็น prompt สำหรับสร้างภาพ}}
```

**Screenshots / real captures** (`{{screenshot:...}}`):
```markdown
{{screenshot:filename.png|คำอธิบายสิ่งที่เห็นในภาพ}}
```
Use real filenames from `media/screenshots/inventory.json`. Placeholders go on their own
lines with a blank line before and after.

The `generate-image` skill inserts review previews with `manage-previews.py insert` —
never add `<!-- gen-preview: -->` blocks by hand.

### Callouts

Use these patterns consistently:

```markdown
> **หมายเหตุ:** {background context}

> **ข้อควรระวัง:** {what could go wrong}

> **เคล็ดลับ:** {practical, specific advice}

> **ลองคิดตาม:** {a question for the reader to reflect on}

> **ลองสังเกต:** {something to notice in daily life}
```

### Tables

Use markdown tables for comparisons and quick references. Keep to 3-4 columns max.

### Examples

- At least one concrete example per concept
- Prefer real-world scenarios over abstract descriptions
- Connect examples to the reader's likely experience
- Use second person: "สมมติว่าคุณ..."
- **No fake Thai character names** ("คุณนิด", "คุณสมชาย") — use situations, not characters

### Cross-references

```markdown
(เราจะพูดถึงเรื่องนี้อย่างละเอียดในบทที่ {N})
(จำจากบทที่ {N} ได้ไหม? ...)
```

Always reference by chapter number — never "บทก่อนหน้า" or "บทถัดไป".

### Summary

- Bullet-point list covering every major section
- Each bullet = one key takeaway (bold the core concept with `**...**`)
- Actionable — reader finishes knowing what they learned

### References

Format:
```markdown
- {Author}, "{Title}" — {short description}
  - ที่มา: {real URL from the reference document}
```

**Every reference must have a real URL.** Read the `> Source:` line from each
reference doc. Never invent URLs or use placeholder text.

### Thai language

- Keep technical terms in English where natural (no forced Thai coinage)
- No banned calques from `thai-style.md` (e.g., never "ใต้ฝากระโปรง")
- Professional but friendly tone — like a knowledgeable senior colleague
- Natural Thai, not machine-translated or stiff

## Writer Mode (chapter file does NOT exist)

1. Read everything in "Before writing" above
2. Plan the chapter structure against the outline subtopics + page_target
3. Write the full chapter following the conventions above
4. Run `manage-previews.py insert` to add review previews for any `{{image:...}}`
5. Run `manage-previews.py validate` — must exit 0 before declaring done
6. Report: word count, page estimate, section count, image count, and refs used

## Editor Mode (chapter file EXISTS)

1. Read the existing chapter + outline + ALL reference docs
2. Verify factual accuracy against refs — every claim, number, and quote
3. Check outline coverage — every subtopic present with depth
4. Check cross-references — correct chapter numbers, not stale
5. Rewrite or polish as needed — be bold with weak sections, leave strong ones
6. Run `manage-previews.py validate` — must pass
7. Report: what was changed, why, and the before/after page estimates
