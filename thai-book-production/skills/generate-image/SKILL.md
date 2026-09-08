---
name: generate-image
description: >
  Generate content figures for the book with thClaws's built-in `TextToImage` tool (Gemini
  `pro` image by default, or `flash` — the nano-banana models, which render Thai + English text) — the LLM authors
  the prompt at generation time from the figure's caption and chapter context. Produces CONTENT-COMMUNICATING
  figures (`{{image:...}}`): infographics, diagrams, flowcharts, charts/graphs, comparison tables,
  and annotated illustrations with on-image labels — NOT abstract art, and NOT real UI screenshots
  (those are `{{screenshot:...}}`, handled by mockup-screenshot). Use when the user asks to
  "สร้างรูป", "generate image", "ทำภาพประกอบ", "ทำ infographic", "ทำไดอะแกรม/แผนภูมิ/กราฟ",
  "gen ภาพ AI", "make illustrations/diagrams", or when the router reaches the MEDIA stage and
  generated figures are still `needed`.
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
| slides | `media/slides/chNN.slides.md` → `chNN.yaml` |
| screenshots (จริง, จับจากโปรแกรม) | `media/screenshots/` (+ `inventory.json`) |
| generated (AI, built-in TextToImage) | `media/generated/` (+ `inventory.json`) |
| reports (QC ทุกชนิด) | `reports/chNN.audit.md`, `reports/chNN.proofread.md`, `reports/chNN.yaml-audit.md` |
| apparatus | `apparatus/glossary.md`, `apparatus/index.md` |
| translations | `translations/<lang>/chapters/chNN.md` |
| assets | `assets/` |
| build output | `build/` |


# Generate Image — Content Figures (built-in TextToImage)

**Prerequisite:** the built-in image tools must be on — `imageToolsEnabled: true` in
`.thclaws/settings.json`, plus a provider API key in env (`GEMINI_API_KEY`/`GOOGLE_API_KEY` for
Gemini, `OPENAI_API_KEY` for OpenAI) **or** the thClaws Gateway key. No MCP/Pinn.ai needed for images.

Two image kinds in this book, kept in **separate folders**:
- **screenshot** — real captures of the app UI → `{screenshots}/*.png`, referenced `{{screenshot:file|caption}}`.
  Precious, hand-captured (or UI mockups via `mockup-screenshot`). **This skill never touches these.**
- **generated** — AI figures → `{generated}/<id>.png`, referenced `{{image:id|caption}}`.
  Regenerable. **This skill owns these.**

## Make figures that TEACH, not decoration

The default model (Gemini `pro` image — nano-banana) **renders legible text in both Thai and
English** and is strong at **infographics, diagrams, flowcharts, charts/graphs, comparison tables, timelines, concept
maps, and annotated illustrations**. Use that. **Every generated figure should communicate the
chapter's content as concretely as possible — NOT abstract mood art.** A reader should learn
something from the picture alone.

Prefer, in order:
1. **Diagram / flowchart** — steps, pipelines, how something works (boxes + arrows + labels).
2. **Comparison** — before/after, A vs B, วิธีเดิม vs วิธีใหม่ (two labeled columns).
3. **Infographic** — a labeled scene or breakdown of a feature with callouts and short text.
4. **Chart / graph** — when the chapter has numbers or trends (bar, line, simple stats).
5. **Annotated illustration** — a concrete scene with labels pointing at the important parts.

Only fall back to a purely illustrative "hero" image when the concept truly has no structure to show.
**Put real, correctly-spelled text INTO the image** (Thai headings + English technical terms, step
numbers, labels) wherever it aids understanding — that is the point of using the nano-banana model.

## Config (from `book.yaml → style.image_gen`)
- `model` (default `pro`) — built-in `TextToImage` model. Gemini `pro` (nano-banana pro,
  `gemini-3-pro-image` — **default**, best at dense labeled diagrams and Thai text) or `flash`
  (cheaper/faster, fine for simple figures); or `gpt-image-2` (OpenAI); or `qwen-image-2.0` (Qwen,
  strong at text). Provider is inferred from the model — set `provider` explicitly only to
  disambiguate.
  > **Always pass `model=` explicitly.** `TextToImage`'s own built-in default is `flash`, so an
  > omitted argument silently downgrades the figure. If `book.yaml` has no `style.image_gen.model`,
  > pass `model="pro"`.
- `aspect_ratio` (default `16:9`) — one of `1:1`, `3:4`, `4:3`, `9:16`, `16:9`.
- `size` (default `2K` — print-quality figures) — `512` | `1K` | `2K`.
- `art_style` — house visual system prepended to **every** prompt so the whole book looks like one
  set: an **informative infographic** look (flat vector, house palette, clear labeled diagrams,
  legible Thai + English typography). Keep it consistent; don't drift per image.

## Registry — `{generated}/inventory.json`
```json
{
  "generated": [
    {
      "id": "ch01-old-way-vs-new-way",
      "chapter": 1,
      "caption": "ไดอะแกรมเปรียบเทียบวิธีทำงานแบบเดิม vs แบบใหม่",
      "prompt": "",                     // filled with the FINAL prompt actually used (incl. on-image text)
      "model": "pro",
      "aspect_ratio": "16:9",
      "size": "2K",
      "file": "ch01-old-way-vs-new-way.png",
      "status": "needed"                // needed | generated
    }
  ]
}
```

## Process
1. Resolve paths + `style.image_gen` from `book.yaml`. Read `{generated}/inventory.json` (create
   `{ "generated": [] }` if absent).
2. **Discover work.** Union of:
   - entries with `status: needed` in the registry, and
   - every `{{image:<id>|<caption>}}` placeholder found in `{chapters}/*.md` that has no registry
     entry yet → add one (`status: needed`, caption from the placeholder, `chapter` from the file).
   Report any placeholder whose id duplicates a `{{screenshot:...}}` (they must not collide).
3. **For each needed image, author the prompt (LLM, at generation time):**
   - Read the caption + the surrounding paragraph(s) in the chapter for the actual teaching point.
   - **Pick the figure type** that explains it best (diagram / comparison / infographic / chart /
     annotated illustration — see "Make figures that TEACH" above). Content clarity beats decoration.
   - Compose the prompt with `art_style` **first**, then describe the **layout** (boxes, arrows,
     columns, icons, data points) AND the **exact on-image text to render**. nano-banana renders
     Thai + English, so give the literal strings: Thai headings/labels, English technical terms
     (ศัพท์ใน `book.yaml → terminology.keep_english`), step numbers, short callouts. Keep
     on-image text short and legible.
   - **Spell every Thai (and English) string correctly** — it becomes part of the book. If a chart
     shows numbers, state the exact values and axis labels in the prompt.
   - The prompt body may be written in English (models parse it best) while the **text to be drawn
     inside the image is quoted verbatim** in whatever language it should appear.
   - Avoid: real public figures, brand logos, copyrighted characters, and tiny unreadable paragraphs
     of text (use a few clear labels, not walls of text).
4. **Generate** with the built-in tool (approval-gated — it costs money + writes a file):
   ```
   TextToImage(prompt=<authored>, model=<style.image_gen.model ?? "pro">,
               aspect_ratio=<style.image_gen.aspect_ratio>, size=<style.image_gen.size>)
   ```
   `model` is never omitted — the tool falls back to `flash` on its own if you leave it out.
   It writes the file to `output/img-<ts>-<sha8>.<ext>`, returns the image inline, and reports that
   path. (No URL — the file is already local.)
5. **Save.** Move the file the tool just wrote into the registry path:
   `mv "output/img-<ts>-<sha8>.<ext>" "{generated}/<id>.png"` (transcode to PNG if the provider
   returned a different ext). Read the exact `output/…` path from the tool result — don't guess it.
6. **Update the registry entry:** set `status: generated`, `file: <id>.png`, and store the **final
   prompt used** in `prompt` (so it's reproducible / editable next run).
7. **Insert a review preview into the chapter markdown — run the script, never edit by hand.** So the
   author can see the figure while reading `{chapters}/chNN.md` in a normal markdown preview, a
   standard markdown image tagged with an HTML-comment marker goes right after the placeholder:
   ```
   {{image:ch01-foo|caption}}
   <!-- gen-preview:ch01-foo -->
   ![caption](../media/generated/ch01-foo.png)
   ```
   **Always produce it with the script** — it is idempotent (strips old previews, re-emits one per
   placeholder), handles **multi-line captions**, and refuses to run on a damaged chapter:
   ```
   python3 {skill_dir}/scripts/manage-previews.py insert \
       {chapters}/ch{NN}.md [--rel ../media/generated] [--ext .png]
   ```
   - **NEVER insert/replace a preview by hand or with a line-based edit.** Placeholder captions
     routinely wrap across lines; "insert after the line starting with `{{image:`" splits the
     placeholder in half, swallows the preview into it, and has already destroyed chapter prose.
   - **Never remove or edit the `{{image:id|caption}}` placeholder** — it is the source of truth the
     pipeline (create-slide-markdown, build-epub-pdf) keys off. The preview is an *addition* beside it.
   - `--rel` defaults to `../media/generated` (path **relative to the chapter file**); pass it
     explicitly if `layout.generated` / `layout.chapters` are customized. Batch: pass several files.
   - This preview is review-only. `build-epub-pdf` strips every `gen-preview` block before resolving
     the placeholder, so the figure is embedded exactly once — no double image.
8. **Present** each result to the user (the image is returned inline), and offer variations/edits
   (regenerate, or `ImageToImage` for tweaks). Batch: process all needed images, then summarize id → status.

## Regeneration
- Re-run only regenerates `status: needed`. To redo one, set that entry back to `needed` (or the
  user says "regenerate ch01-hero") and run again — overwrites `<id>.png`.
- Because generated images are regenerable, they can be git-ignored; the registry `prompt` is the
  real source of truth for each figure.

## Guardrails
- Writes under `{generated}/` + its `inventory.json`, and may add/refresh **only** its own
  `<!-- gen-preview:<id> -->` block in `{chapters}/chNN.md` right after the matching `{{image:id}}`
  placeholder. **Never** edits the placeholder itself, the chapter prose, or `{screenshots}/`.
- **Preview blocks are written by `manage-previews.py` only** — no hand-editing, no Edit/sed on
  `gen-preview` lines.
- **Before reporting done, validate every chapter touched** — a broken placeholder makes
  build-epub-pdf and create-slide-markdown misread the chapter:
  ```
  python3 {skill_dir}/scripts/manage-previews.py validate \
      {chapters}/ch{NN}.md
  ```
  Exit 1 = fix it first (it reports unterminated placeholders, previews swallowed inside a
  placeholder, duplicates, and orphans). Placeholders whose image isn't generated yet are counted
  as pending, not as errors.
- Keep one consistent `art_style` across the book — visual coherence matters more than per-image flair.
- Show every generated image (returned inline) to the user; get sign-off before wide regeneration.
- If `TextToImage` is unavailable (`imageToolsEnabled` off, or no provider key / gateway), report
  which ids are still `needed` and stop — don't silently skip.
