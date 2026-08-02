---
name: init-book
description: >
  Start a brand-new book OR article project — the intake wizard that scaffolds a fresh
  working folder for the thai-book-production pipeline. Use this skill when the user wants to
  BEGIN a new piece and there is no `book.yaml` yet: "เริ่มหนังสือใหม่", "สร้างหนังสือใหม่",
  "สร้างโปรเจกต์หนังสือ", "ตั้งโปรเจกต์หนังสือใหม่", "init a book", "start a new book",
  "create a book project", "scaffold a book", **"สร้างบทความ", "เขียนบทความ", "write an article",
  "new article"** (→ `kind: article`), **"มินิบุ๊ก", "mini-book", "เล่มเล็ก 3-5 บท", "หนังสือสั้นๆ"**
  (→ `kind: mini-book`, ≤5 บท). It interviews for the whole-project decisions that drive the
  pipeline (kind book|mini-book|article, metadata, chapter
  scope, output targets epub/pdf/translations, image & voice style, cover approach), writes `book.yaml` from the template,
  creates the directory skeleton, then hands off to get-book-ref to seed references. If a
  `book.yaml` already exists in the folder, do NOT re-init — route to book-router instead.
---

# Init Book — New-Project Intake & Scaffold

You set up a **new** book so the rest of the pipeline runs on solid, whole-book
decisions instead of silent template defaults. One working folder = one book. Your job
ends the moment `book.yaml` + the skeleton exist and the first stage (get-book-ref) is
ready to run — you do NOT gather references, outline, or write content.

**Read `references/book.yaml.template` first** — it is the manifest SSOT you fill in.
Layout spec: `../book-router/references/folder-structure.md`.

## Step 0 — Guard: are we already in a book folder?

A book folder has `book.yaml` at its root.

- **book.yaml present** → STOP. Do not overwrite. Say so and hand to **book-router**
  ("มี book.yaml อยู่แล้ว — จะดูสถานะ/ทำต่อ ใช้ book-router"). Only re-init if the user
  explicitly asks to start over (then confirm the existing file will be replaced).
- **book.yaml absent** → proceed with the interview below.

## Step 1 — Interview (essentials first, defaults for the rest)

Ask compactly, in Thai. Insist only on the essentials; offer sensible defaults for
everything else and let the user accept them in one go.

**Essential (must ask):**
- `book.kind` — **`book` (default) | `mini-book` | `article`**. Pick from intent:
  - **`article`** — "บทความ" / "article" / "เอกสารสั้น": single doc, **no "บทที่ N"/TOC/back-matter**,
    skips outline-approval.
  - **`mini-book`** — "มินิบุ๊ก" / "mini-book" / "เล่มเล็ก" / "เล่มบาง" / "หนังสือสั้นๆ 3-5 บท": a small
    book of **3–5 chapters (hard cap 5)** — keeps "บทที่ N" + TOC + outline-approval, but back-matter
    (glossary/index/appendix) is **optional (default: skip)**.
  - **`book`** — full book, many chapters, everything.
  All three still support MEDIA (slides/TTS/video). Set kind right up front — it drives
  init/router/write/build.
- `book.title` — ชื่อเต็มบนปก (article: หัวเรื่องบทความ). Derive `book.slug` from it (kebab-case
  ASCII, for build filenames เช่น `my-book.epub`); confirm the slug.
- `book.author`
- `book.language` — default `th`. Keep `keep_english_terms: true` (คงศัพท์เทคนิคอังกฤษ)
  unless the user says otherwise.
- **Chapter scope** → initial `chapters:` registry.
  - **`kind: article`** → exactly **one** entry (`id: 1`, `title` = the article title). Don't
    interview for multiple chapters; an article is one document.
  - **`kind: mini-book`** → ask for **3–5 chapters (hard cap 5)**. If the user proposes more than 5,
    say a mini-book is capped at 5 and offer to either trim or switch to `kind: book`.
  - **`kind: book`** → ask for the chapter list (id + title) or, if unknown, start with one
    placeholder `id: 1` and note it can grow later.
  - Set a `page_target` per chapter (default 15; article often ~5–10) — audit-chapter checks
    thickness ±20% against it.
- **Output targets** (`targets:`) — these steer the whole pipeline, so decide now:
  - `epub` (default `true`)
  - `pdf` (default `false`) — needs `xelatex`; note the extra toolchain
  - `translations` (default `[]`) — เช่น `[en]` เพื่อทำฉบับอังกฤษ

**Offer-with-defaults (ask "รับค่า default หรือปรับ?"):**
- `style.image_gen.art_style` — the AI-figure look applied to the **whole book** (must be
  consistent). Default in the template (clean modern infographic, teal & navy). Also
  `aspect_ratio` (default `16:9`), `size` (default `2K`), and `model` (default `pro` — Gemini
  nano-banana pro via the built-in `TextToImage` tool; `flash` is the cheaper option. No Pinn.ai
  needed for images).
- `style.tts` — `voice` (default `Charon`), `model`, optional `style_hint` for narration.
- `cover.tool` — `nano-banana` (AI, default) | `canva` | `programmatic`; plus `art_style`
  and `frame` (`flat` | `bleed`). Only prompt further if they'll do print (`print_trim_mm`,
  `paper_thickness_mm`).

Don't over-interrogate: read the defaults from the template, restate them, and let the
user override selectively.

## Step 2 — Write `book.yaml` + scaffold

1. Copy `references/book.yaml.template` to `<folder>/book.yaml` and fill in every value
   gathered above — **including `book.kind`** (`book` default, or `article`). Leave unset
   optional fields at their template defaults. Do not hardcode paths — the `layout:` block
   stays as the template defines it. For `kind: article`, `chapters:` holds exactly one entry.
2. Create the directory skeleton (from folder-structure.md). For `kind: article` you may skip
   `apparatus/` (no back-matter) but it's harmless to leave it empty:
   ```
   outline/  refs/docs/  refs/blogs/  chapters/  media/slides/
   media/screenshots/  media/generated/  apparatus/  translations/  assets/  reports/  build/
   ```
3. Seed empty registries where the pipeline expects them: `media/screenshots/inventory.json`
   and `media/generated/inventory.json` as `[]` (list skills read these).

## Step 3 — Confirm & hand off

Show a one-screen summary: **kind (book/article)**, title/slug, author, language, chapter
count, targets, and the image/voice/cover choices. Then route to the first pipeline stage:

> โครงเริ่ม (book/บทความ) พร้อมแล้ว — เริ่ม **get-book-ref** เพื่อดึงเอกสารอ้างอิงหลักก่อนวาง outline ไหม

Hand off; do not start fetching refs yourself. From here on, **book-router** owns state
and routing.

## Guardrails

- Never overwrite an existing `book.yaml` without explicit confirmation.
- `book.yaml` is the single source of truth — every later skill resolves paths from
  `layout:`. Get it right here so nothing downstream has to guess.
- Whole-book style (`image_gen.art_style`, `tts.voice`) is expensive to change mid-book —
  settle it now, not at the MEDIA stage.
- Your output is a scaffold, not content. Stop at "ready for get-book-ref".
