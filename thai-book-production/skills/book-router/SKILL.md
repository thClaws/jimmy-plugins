---
name: book-router
description: >
  The front door and orchestrator for an EXISTING book project (has a `book.yaml`), built
  where one working folder holds one book. Use this skill whenever the
  user asks an open-ended question about a book already underway — "อยู่เฟสไหนแล้ว", "ทำอะไร
  ต่อดี", "book status", "what's next on the book", "ช่วยทำหนังสือต่อ" — or any request that
  spans more than one stage. It reads project state, reports which stage each chapter is
  in, recommends the next action, and hands off to the right stage skill. Starting a NEW
  book (no `book.yaml` yet) is **init-book**'s job — route there. When a request clearly
  names one stage, let that stage skill trigger directly instead.
---

# Book Router — Pipeline Orchestrator

You are the project manager for a book project. One working folder =
one book. Your job is NOT to write content — it is to (1) know the layout, (2) report
state, (3) route to the correct stage skill.

**Read `references/folder-structure.md` first** — it defines the canonical layout. All
paths come from `book.yaml → layout:`, never hardcoded.

## Paths (thai-book-production layout)
หนึ่ง working folder = หนังสือหนึ่งเล่ม Resolve ทุก path จาก `book.yaml → layout:` ที่ root —
**ห้าม hardcode** สเปกโครงเต็มอยู่ที่ `references/folder-structure.md`; template ของ manifest
อยู่ที่ `../init-book/references/book.yaml.template` ถ้าไม่มี `book.yaml` = ยังไม่ใช่ book folder →
ส่งต่อ **init-book** ให้ scaffold ก่อน (router ไม่ scaffold เอง)

## Step 0 — Are we in a book folder?

A book folder has `book.yaml` at its root.

- **book.yaml present** → load it. `layout:` gives every path; `chapters:` gives scope.
- **book.yaml absent** → this is not a book yet. Route to **init-book** (the intake +
  scaffold wizard) — it interviews for metadata/targets/style, writes `book.yaml`, makes
  the skeleton, and hands back to the pipeline. Router does **not** scaffold inline.

Never guess paths. If unsure which folder is the book, ask once.

## The Pipeline (canonical order)

```
INIT        init-book (no book.yaml → intake wizard: metadata + targets + style → scaffold)
PLAN        get-book-ref (seed) → outline-planner → get-book-ref (targeted)   ↺ loop
            → ✋ HUMAN: adjust & approve outline ({outline}/APPROVED.md)   [book only; article skips]
WRITE       write-book-chapter (+ generate-image AI figures + mockup-screenshot placeholders)
QC          audit-chapter → proofread → fix-chapter        (loops per chapter)
            → ✋ HUMAN: adjust content · capture real screenshots to replace mockups
MEDIA       create-slide-markdown (author .slides.md) → create-slide-yaml (compile) → audit-yaml
            → build-slides-pptx → RenderSlides tool (Marp deck → PDF + slide-NN.png)
            → generate-tts (built-in TextToSpeech — per-slide WAV)
            → build-chapter-video (ffmpeg: slide video → chapter video — deterministic)
APPARATUS   index-glossary
LOCALIZE    translate
BUILD       cover-design → build-epub-pdf
```

PLAN is a small loop: pull the core reference docs first so the outline is grounded on
real source material, draft the outline, then fetch targeted refs for any gaps the
outline exposes. WRITE→QC repeat per chapter; APPARATUS onward are book-level, run once
near the end.

**Read `book.kind` (default `book`) and adapt.** Three kinds on a spectrum:

| behavior | `article` | `mini-book` | `book` (default) |
|---|---|---|---|
| chapters | exactly 1 | **3–5 (hard cap 5)** | many |
| "บทที่ N" heading | no (article title) | yes | yes |
| TOC in build | no | yes | yes |
| outline-approval gate | **skip** | keep | keep |
| back-matter (glossary/index) | none | **optional (default skip)** | yes |
| MEDIA (slides/TTS/video) | **yes** | **yes** | **yes** |

- **article** route: (PLAN light/optional — no `APPROVED.md`) → WRITE → QC → (MEDIA) → (LOCALIZE) → BUILD.
- **mini-book** route: same as book but **cap chapters at 5** — if the `chapters:` registry has >5,
  warn the user (trim, or switch to `kind: book`). Apparatus (`index-glossary`) is **optional**:
  run it only if the user asks; otherwise skip straight to translate/cover/build.
- **book** route: the full canonical pipeline above, unchanged.

**MEDIA runs the same for every kind.** Each chapter (`chNN.md` — for an article that's the single
`ch01`) goes through **create-slide-markdown** → **create-slide-yaml** → **build-slides-pptx** (RenderSlides) → **generate-tts**
→ **build-chapter-video**. So slides/video are fully supported for article and mini-book too —
never treat them as text-only.

## Step 1 — Build the state table

Resolve paths from `layout:`. For each chapter in the `chapters:` registry, find the
furthest stage reached using cheap on-disk signals (prefer existence + mtime over
reading contents):

| Stage | Evidence |
|---|---|
| outline | listed in `chapters:` but no `{chapters}/chNN.md` |
| written | `{chapters}/chNN.md` exists |
| content-audited | `{reports}/chNN.audit.md` exists |
| fixed | chNN.md mtime newer than its audit report |
| proofread | `{reports}/chNN.proofread.md` exists |
| slides-md | `{slides}/chNN.slides.md` exists (authored source — create-slide-markdown) |
| slides-yaml | `{slides}/chNN.yaml` exists and is newer than `chNN.slides.md` (compiled — create-slide-yaml) |
| slides-audited | `{reports}/chNN.yaml-audit.md` exists |
| slides-rendered | `{build}/slides/chNN.marp.md` exists and is newer than `chNN.yaml` |
| slide-images | `{build}/slides/preview/chNN/slide-*.png` count == slide count (RenderSlides) |
| images-ready | no `{{screenshot:...}}`/`{{image:...}}` in `chNN.md` is still unresolved — real file in `{screenshots}`/mockup present, and every `{{image:id}}` has `{generated}/<id>.png` (registry `status: generated`) |
| screenshots-real | no entry in `{screenshots}/inventory.json` used by this chapter still has `status: mockup` (**human gate** — คนจับภาพจริงมาแทน) |
| tts | `{build}/audio/chNN/slide-*.wav` count == slide count + `manifest.json` (generate-tts) |
| video | `{build}/video/chNN.mp4` exists and newer than slide images + audio (build-chapter-video) |

**Human gates (สถานะที่ "คน" ต้องปลดเอง — router แจ้งและรอ ไม่ข้ามเอง):**
| Gate | Evidence | ปลดโดย |
|---|---|---|
| outline-approved (book only) | `{outline}/APPROVED.md` exists | คนรีวิว outline แล้วบอก "อนุมัติ outline" → router เขียน `APPROVED.md` (วันที่+หมายเหตุ) ให้ · **article: ข้าม gate นี้** |
| screenshots-real | ไม่มี `status: mockup` ค้าง | คนวางไฟล์จริงทับชื่อเดิมแล้วบอก "เปลี่ยนเป็นภาพจริงแล้ว" → mark `status: real` |

Render: `บท | ชื่อ | สถานะล่าสุด | ค้างอะไร`.

Also check **book-level artifacts** (run once, near the end) with the same cheap signals:

| Book-level stage | Evidence |
|---|---|
| apparatus | `{apparatus}/glossary.md` and `{apparatus}/index.md` exist |
| translated | `{translations}/<lang>/chapters/` populated for each lang in `targets.translations` |
| cover | `{assets}/cover-front.png` exists (+ `cover-wrap.pdf` if print) |
| built | `{build}/<slug>.epub` (and `.pdf` if `targets.pdf`) exist |

Report book-level status only once all in-scope chapters are through the per-chapter loop.

## Step 2 — Recommend the next action

Priority (ตรงกับ workflow: init → seed refs → manifest → outline → **คนอนุมัติ** → เขียนบท+ภาพ →
**คนแทนภาพจริง** → สไลด์+VO → render → TTS → วิดีโอ):
0. no `book.yaml` → **init-book** (scaffold the project first; nothing else can run)
1. `{refs_docs}`/`{refs_blogs}` empty → **get-book-ref** (seed the core docs for the
   book's subject before outlining)
2. Seed refs present but no outline files → **outline-planner** (ground it on `refs/`)
3. Outline done but it exposes gaps / a chapter lacks source material → **get-book-ref**
   (targeted pass), then continue
4. **HUMAN GATE — outline approval (book only):** outline exists but no `{outline}/APPROVED.md`
   → stop and ask the human to review/adjust the outline; on "อนุมัติ outline" write
   `APPROVED.md` (date + reviewer note). **Do not start writing chapters before this.**
   - **`book.kind: article` → SKIP this gate.** No `APPROVED.md` needed; go straight to
     **write-book-chapter** once the article title/scope is set (outline is optional).
5. Chapter in scope has no `chNN.md` → **write-book-chapter** (lowest unwritten) —
   the chapter comes with `{{image:}}` figures (**generate-image**) and `{{screenshot:}}`
   mockups (**mockup-screenshot**) generated alongside
6. Written chapter never content-audited → **audit-chapter**
7. Audit report has open CRITICAL/MAJOR → **fix-chapter**, then **proofread**
   (คนปรับเนื้อหาเองได้ตลอดช่วงนี้ — router แค่ตรวจ state ใหม่)
8. Unresolved images: `{{screenshot:...}}` without a file → **mockup-screenshot**;
   `{{image:id}}` with registry `status: needed` → **generate-image** (built-in TextToImage)
9. **HUMAN GATE — real screenshots:** chapter clean but inventory still has
   `status: mockup` entries → remind the human to capture real screenshots and replace
   the mockup files (same filename), then mark `status: real`. Slides/video may proceed
   with mockups **only if the human explicitly says so.**
10. All in-scope chapters clean, `.slides.md` missing → **create-slide-markdown** (author the
   slide Markdown + voice-over script ใน `::: notes`); then `.slides.md` exists but no `.yaml`
   (or `.yaml` older than the `.slides.md`) → **create-slide-yaml** (compile + validate)
11. Slides YAML clean but no rendered slides (or older than the YAML) →
   **build-slides-pptx** (compile Marp-md, then the **RenderSlides** tool → PDF + per-slide `slide-NN.png`)
12. Slide images ready but `{build}/audio/chNN/` incomplete → **generate-tts**
   (built-in TextToSpeech ต่อสไลด์จาก notes, deterministic naming)
13. Slide images + TTS ready but no `{build}/video/chNN.mp4` → **build-chapter-video**
   (`slides2video.py` — ffmpeg: ภาพ+เสียงต่อสไลด์ → ต่อเป็นวิดีโอทั้งบท, deterministic)
14. Chapters + media done → book-level: **index-glossary** → **translate** (if
   `targets.translations` non-empty) → **cover-design** → **build-epub-pdf**
   - **`kind: article` → SKIP index-glossary** (no back-matter); go straight to translate → cover → build.
   - **`kind: mini-book` → index-glossary is OPTIONAL** (default skip); run only if the user asks,
     else go straight to translate → cover → build.

State the recommendation in one line, then offer handoff: "จะให้เริ่ม <stage> เลยไหม".

## Step 3 — Hand off

Don't re-implement a stage — defer to its skill and pass the concrete target (chapter
id, resolved file path). If the user picks a different stage, respect it.

## Guardrails

- Never mark a stage done you haven't verified on disk.
- audit-chapter must run before fix-chapter (fix-chapter reads `{reports}/chNN.audit.md`).
- Book-level stages run once the per-chapter loop is complete for all in-scope chapters.
- Keep status reports factual and short. Router orients; stage skills do the work.
