---
name: translate
description: >
  Translate a chapter or the whole book into another language while preserving the
  technical-term-in-English convention, code blocks, screenshot placeholders, and
  Markdown structure. Use when the user asks to "แปลบท", "translate chapter",
  "แปลหนังสือเป็นภาษาอังกฤษ", "ทำฉบับ EN", "localize the book", or names a target
  language. Localizes prose only — never touches code, commands, or file names.
---

## Paths (thai-book-production layout)

หนึ่ง working folder = หนังสือหนึ่งเล่ม Resolve ทุก path จาก `book.yaml → layout:` ที่ root
ของ folder — **ห้าม hardcode** ถ้าไม่มี `book.yaml` แปลว่าไม่ได้อยู่ใน book folder ให้ให้
`book-router` scaffold ก่อน ค่า default:

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


# Book Translation / Localization

Translate prose while keeping the book's technical conventions intact.

## Rules
- **Never translate**: code blocks, inline code, command names (/write-chapter),
  file extensions, tool names (Gmail, Chrome), API/SDK/MCP, image placeholders
  `{{screenshot:...}}` and `{{image:...}}` (ids stay identical), and terms the style guide keeps in English.
- **Do translate**: narrative prose, headings, callouts, captions, summaries.
- Preserve Markdown structure exactly — same headings, lists, tables, anchors.
- Keep character names and running examples consistent across chapters (share a
  translation memory / glossary so "คุณแพร" maps the same way every time).

## Process
1. Resolve paths from `book.yaml → layout:`. Load the source `{chapters}/chNN.md`,
   the apparatus glossary `{apparatus}/glossary.md` (for canonical term heads), and the
   per-language **translation memory** `{translations}/<lang>/glossary.md` (create if
   absent) — a `source → target` map for names, running examples, and recurring phrases.
2. Translate section by section; append every new mapping to the TM as you go so the
   next chapter stays consistent (e.g. `คุณแพร → Khun Prae`).
3. Preserve every non-prose element byte-for-byte (code, commands, `{{screenshot:...}}` and
   `{{image:...}}` — keep the id; you may translate only the caption after `|`, file names,
   English technical heads from the glossary).
4. Save to `{translations}/<lang>/chapters/chNN.md`.

Target languages come from `book.yaml → targets.translations` (e.g. `[en]`). Output
goes to `{translations}/<lang>/chapters/chNN.md`. Translate the FINAL Thai text (after
audit + proofread) so you don't localize content that still changes.

## Guardrails
- If the source chapter isn't finalized (open audit items), warn before translating.
- Do not "improve" content while translating — meaning-preserving only. Flag genuine
  errors you notice for the author instead of silently changing them.
