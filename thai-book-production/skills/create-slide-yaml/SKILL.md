---
name: create-slide-yaml
description: >
  Compile a chapter's slide Markdown (`media/slides/chNN.slides.md`) into the slide YAML build
  artifact (`media/slides/chNN.yaml`) with the bundled deterministic compiler, then validate it.
  This is STEP 2 of two: **create-slide-markdown** authors the `.slides.md`; this skill turns it into
  `.yaml` for the render/TTS/video pipeline. Use when the user asks to "compile slides", "convert
  slides to yaml", "make the slide yaml", "แปลงสไลด์เป็น yaml", "compile chNN.slides.md", "สร้าง yaml
  สไลด์", or when the router reaches the compile step. If no `.slides.md` exists yet, author it first
  with create-slide-markdown — do NOT hand-write the YAML.
---

## Paths (thai-book-production layout)

Resolve every path from `book.yaml → layout:` at the folder root — **ห้าม hardcode**. Defaults:

| what | path |
|------|------|
| slides (source, แก้มือ — create-slide-markdown writes) | `media/slides/chNN.slides.md` |
| **slides (build artifact — THIS skill writes)** | `media/slides/chNN.yaml` |
| chapters (for the image audit) | `chapters/chNN.md` |
| screenshots / generated | `media/screenshots/` · `media/generated/` |
| reports | `reports/chNN.yaml-audit.md` |

---

# Compile Slide Markdown → YAML

## Where this fits (2-step workflow)

```
create-slide-markdown  →  chNN.slides.md   (authoring — human-editable)
create-slide-yaml      →  chNN.yaml        (THIS skill — deterministic compile + validate)
```
The `.yaml` is a **build artifact**: never hand-write or hand-edit it. If you need to change a slide,
edit the `.slides.md` (via create-slide-markdown or directly) and **recompile**. The compiled YAML
then feeds `build-slides-pptx` (RenderSlides) → `generate-tts` → `build-chapter-video`.

The compile target — every slide type, its fields, and the design system — is specified in:
```
Read: {skill_dir}/references/yaml-format.md
```
You only need this to understand or debug what a `<!-- slide: TYPE -->` block compiles into.

## Step 1 — Preflight

The compiler needs `pyyaml`. If missing, install it inline (`pip install pyyaml` or
`.venv/bin/python -m pip install pyyaml`) — that's the only dependency. (The shared
`build-slides-pptx/scripts/check_env.py` also covers it, but don't get pulled into the full
python-pptx preflight; `pyyaml` alone is enough here.)

## Step 2 — Compile (deterministic script — never hand-transcribe)

```bash
python3 {skill_dir}/scripts/slides_md2yaml.py \
  media/slides/chNN.slides.md            # writes media/slides/chNN.yaml
# validate only, no write:
python3 {skill_dir}/scripts/slides_md2yaml.py \
  media/slides/chNN.slides.md --check
```

The script maps every `<!-- slide: TYPE -->` block to the `yaml-format.md` schema, turns `::: notes`
into a literal-block `notes:`, and preserves document order (so insert/delete never renumbers).

- **Never hand-edit `chNN.yaml`** — it is regenerated from the MD every time.
- The script exits non-zero and names the offending slide on malformed input (missing directive,
  unclosed `:::`, missing `::: notes`, unknown type). **Fix the `.slides.md` and recompile — never
  patch the YAML.** If the fix is substantive authoring (notes, structure), hand back to
  create-slide-markdown.
- `id=` on a slide directive is reserved for stable output naming (the pipeline pairs by document
  order today — see generate-tts).

## Step 3 — Validate the compiled YAML

1. **Compiles cleanly** — Step 2 (or `--check`) produces parseable YAML with no errors.
2. **Every slide has `notes`** — no exceptions (no notes = dead air in the video).
3. **No emoji** in any text field (renderer + TTS choke on them).
4. **Section coverage** — every `## N.X` section from the chapter is represented.
5. **Image audit (BOTH kinds — mandatory)** — no chapter image may be dropped:
   - Chapter images (both kinds) → expected screenshot filenames:
     ```bash
     { grep -oP '(?<={{screenshot:)[^|}]+' chapters/chNN.md;
       grep -oP '(?<={{image:)[^|}]+' chapters/chNN.md | sed 's/$/.png/'; } | sort -u
     ```
   - Slide `screenshot:` fields:
     ```bash
     grep '  screenshot:' media/slides/chNN.yaml | sed 's/.*screenshot: *//; s/"//g' | sort -u
     ```
   - The first set must be a **subset** of the second. If any image is missing, fix the `.slides.md`
     (add the screenshot slide) and recompile — never patch the YAML.
6. **Card counts valid** — section cards 2-5, process steps 2-6, timeline events 3-5.

**Slide count is NOT a validation criterion.** create-slide-markdown deliberately lets the chapter's
content decide how many slides there are — do not flag a deck for being "too short" or "too long"
here. The only count rule is coverage (sections + every image present, above). Deeper editorial QC —
redundancy, pacing, note quality — is the separate **audit-yaml** skill.

## Output
`media/slides/ch{NN}.yaml` (zero-padded, e.g. `ch01.yaml`) — the build artifact. Multiple chapters
are independent (parallelizable). After compiling, the deck is ready for `build-slides-pptx`.
