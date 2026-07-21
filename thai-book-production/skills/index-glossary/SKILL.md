---
name: index-glossary
description: >
  Build the back-matter apparatus for the book: a term glossary and a page/section
  index compiled from finished chapters. Use when the user asks to "สร้าง index",
  "ทำ glossary", "อภิธานศัพท์", "ดัชนีท้ายเล่ม", "build the index", "collect glossary
  terms", or when the router reaches the APPARATUS stage. Runs book-level, once
  chapters are largely final.
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
| generated (AI, built-in TextToImage) | `media/generated/` (+ `inventory.json`) |
| reports (QC ทุกชนิด) | `reports/chNN.audit.md`, `reports/chNN.proofread.md`, `reports/chNN.yaml-audit.md` |
| apparatus | `apparatus/glossary.md`, `apparatus/index.md` |
| translations | `translations/<lang>/chapters/chNN.md` |
| assets | `assets/` |
| build output | `build/` |


# Index & Glossary Builder

Compile the glossary and index from all finished chapters. Book-level, run late.

**Guard — kind.** Read `book.yaml → book.kind`:
- **`article`** → **STOP**: an article has no back-matter. Report "kind: article — ไม่มี apparatus, ข้าม"
  and hand back to book-router (next: translate/cover/build).
- **`mini-book`** → back-matter is **optional**; only proceed if the user explicitly asked for a
  glossary/index. Otherwise report "mini-book — apparatus เป็น optional, ข้าม (ถ้าต้องการค่อยสั่ง)" and hand back.
- **`book`** (or unset) → proceed normally.

Resolve paths from `book.yaml → layout:`. Read chapters from `{chapters}/`, write to
`{apparatus}/glossary.md` and `{apparatus}/index.md`. Run once in-scope chapters are final.

## Glossary
1. Scan every `{chapters}/chNN.md` for first-mention English terms explained in
   parentheses (the "Plugin (ชุดเครื่องมือเสริม)" pattern) and for bold/defined terms.
2. Deduplicate; keep ONE canonical definition per term (English head + Thai explanation).
   Record which chapter first defines it.
3. **Sort (decided): two sections in one file** — `## English A–Z` first, then
   `## ภาษาไทย ก–ฮ` — because heads are English but explanations are Thai; a single
   merged collation across two scripts reads worse. Each entry: **`Head`** — คำอธิบาย
   *(ครั้งแรก: บท N)*.
4. Output `{apparatus}/glossary.md`.

## Index
1. Collect index-worthy terms (product names, features, commands, concepts). Reuse the
   glossary heads plus proper nouns; skip stopwords and one-off mentions.
2. Map each to the chapters/sections where it *meaningfully* appears (defined, taught,
   or demonstrated — not every incidental mention).
3. Output `{apparatus}/index.md` with `term → locations`, grouped like the glossary
   (English A–Z, then Thai ก–ฮ).

Locator granularity comes from `book.yaml → style.index_locator`:
- `section` (default) → link to section anchors (`chNN#slug`); can run before build.
- `page` → real page numbers exist only after `build-epub-pdf` paginates, so run this
  step AFTER build when `page` is selected. Warn and fall back to `section` if build
  output isn't present yet.

## Guardrails
- Definitions come from the chapters, not invented. If a term is used but never
  defined, flag it rather than writing a definition from scratch.
- Respect the terminology table in proofread's style guide (keep English terms English).
