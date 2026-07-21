---
name: build-epub-pdf
description: >
  Assemble finished chapters, front/back matter, glossary, index, and cover into a
  complete epub and/or print-ready PDF. Use when the user asks to "build epub",
  "สร้าง epub", "ทำ PDF เล่ม", "ประกอบเล่ม", "compile the book", "export the book", or
  when the router reaches the final BUILD stage. Runs book-level, last.
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


# Book Build — epub / PDF

Compile the whole book into shippable files. Last stage in the pipeline.

## Preconditions (verify first)
- All in-scope chapters written, content-audited clean, proofread
- Glossary + index generated (index-glossary)
- Cover ready (cover-design) — at least front cover for epub
- Front matter (title page, copyright, TOC) and back matter assembled

## Config (from `book.yaml`)
- `book.slug` → output filename; `book.title/subtitle/author/publisher/language` → metadata.
- `targets.epub` / `targets.pdf` → which artifacts to build.
- `build.epub_engine` (default `pandoc`), `build.pdf_engine` (`xelatex` | `weasyprint` | `none`),
  `build.validate` (default `[epubcheck]`).
- `style.fonts` (Sarabun) → embedded font. Chapter order from the `chapters:` registry.

## Assembly order
1. Collect chapters in registry order from `{chapters}/chNN.md` + front matter (title
   page, copyright, auto-TOC) + back matter (`{apparatus}/glossary.md`, `index.md`).
2. Resolve **both** image placeholders and inline the real files:
   - `{{screenshot:file.png|cap}}` → `{screenshots}/file.png` (real capture, or a mockup from
     mockup-screenshot)
   - `{{image:id|cap}}` → `{generated}/<id>.png` (AI illustration from generate-image)
   Use the caption after `|` as the figure alt text/caption. **Fail loudly** and stop on any
   unresolved placeholder of either kind (missing file, or `status: needed` in a registry).
3. Apply the stylesheet (Sarabun for Thai body/headings; monospace for code).

## Toolchain — Pandoc (default)
Install if missing: `pandoc`, and for PDF `texlive-xetex` (xelatex) or `weasyprint`.

**epub** (reflowable):
```
pandoc {chapters}/ch*.md \
  --metadata title="<title>" --metadata author="<author>" --metadata lang=<language> \
  --toc --toc-depth=2 \
  --epub-cover-image={assets}/cover-front.png \
  --epub-embed-font='<Sarabun *.ttf>' \
  --css=style.css -o {build}/<slug>.epub
```
**PDF** (paginated) — xelatex is Thai-safe:
```
pandoc {chapters}/ch*.md --toc --pdf-engine=xelatex \
  -V mainfont="Sarabun" -V geometry:paperwidth=6in,paperheight=9in,margin=0.75in \
  -o {build}/<slug>.pdf
```
(If `pdf_engine: weasyprint`, render Markdown→HTML+CSS→PDF instead. `none` = skip PDF.)

4. **Validate**: run `epubcheck {build}/<slug>.epub`; for print PDF, sanity-check page
   count and trim/bleed. Record results in the build report.

## Outputs (to `{build}/`)
- `<slug>.epub` (validated with epubcheck)
- `<slug>.pdf` (if `targets.pdf`)
- `build-report.md`: chapter count, est. page count, unresolved-placeholder list (must be 0),
  validation results, and — if `index_locator: page` — the trigger to regenerate the
  index against final pagination.

## Guardrails
- Do not build with unresolved image placeholders (`{{screenshot:...}}` or `{{image:...}}`) or
  open CRITICAL audit items — report and stop.
- Publishing/uploading to a store is a separate permissioned action; build only
  produces local files.
