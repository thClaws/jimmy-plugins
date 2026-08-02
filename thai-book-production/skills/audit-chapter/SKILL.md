---
name: audit-chapter
description: >
  Audit the CONTENT of a written book chapter against its outline and learning
  objectives — not the language (that's proofread) and not the slides (that's
  audit-yaml). Use when the user asks to "audit chapter", "ตรวจเนื้อหาบท", "รีวิวบท",
  "บทนี้ครบไหม", "check chapter against outline", "does this chapter cover the
  objectives", or before running fix-chapter. Produces a structured audit report
  (CRITICAL / MAJOR / MINOR) that fix-chapter consumes.
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


# Chapter Content Audit

Judge whether a chapter delivers what it promised. Output a report that `fix-chapter`
can act on directly. Do NOT rewrite the chapter here — audit only.

## Inputs
- The chapter file: `{chapters}/chNN.md`
- Its slice of the outline + learning objectives: `{outline}/outline.md`, `{outline}/plan.md`
- `page_target` for this chapter from `book.yaml → chapters[id].page_target`
- The `write-book-chapter/references/chapter-source-map.md` + `{refs_docs}/` / `{refs_blogs}/`
  material for that chapter, if present

## Process
1. Resolve paths from `book.yaml → layout:`. Load `chNN.md`, `outline/outline.md`,
   `outline/plan.md`, and this chapter's `page_target`. If the outline/LO slice is
   missing, stop (audit needs a baseline).
2. Extract this chapter's learning objectives and planned subtopics (x.1–x.n) from the
   outline/plan.
3. Walk the chapter section by section, scoring each of the 7 dimensions below and
   collecting concrete evidence (line/section anchors) for every issue.
4. **Estimate actual pages** so page-plan fit is measurable: `est_pages ≈ ceil(word_count / 300)`
   for Thai prose (≈300 words/page at this trim), plus ~0.25 page per screenshot
   placeholder. Compare to `page_target` (±20% window).
5. Cross-check technical claims against the cited reference docs; a contradiction is CRITICAL.
6. Write the report to `{reports}/chNN.audit.md` in the exact format below and stop.
   Do NOT edit the chapter.

## Audit dimensions

1. **Objective coverage** — every learning objective for this chapter is actually
   taught, not just mentioned. Flag each uncovered LO as CRITICAL.
2. **Outline fidelity** — all planned subtopics (x.1–x.n) are present and in a sensible
   order. Missing subtopic = MAJOR; reordered-but-fine = note only.
3. **Depth & examples** — each concept has at least one concrete example / walkthrough
   where the outline calls for one. Thin section = MAJOR.
4. **Accuracy** — technical claims match the reference docs. Contradiction with a cited
   source = CRITICAL.
5. **Continuity** — terms, character names, and running examples are consistent with
   earlier chapters. Setup/payoff promises are honored.
6. **Page-plan fit** — length is within ~±20% of the page plan target. Way over/under
   = MAJOR (flag for split or expansion).
7. **Structural completeness** — opening story, body sections, callouts, summary,
   image placeholders (`{{screenshot:...}}` for UI captures, `{{image:...}}` for AI illustrations)
   all present per template.
8. **Thai style — banned calques** — scan against the shared list
   `{skill_dir}/../write-book-chapter/references/thai-style.md`; any ❌ term
   (e.g. "ใต้ฝากระโปรง") = MAJOR, report the ✅ replacement so fix-chapter can apply it.

## Severity rubric
- **CRITICAL** — reader cannot achieve a stated objective, or content is wrong.
- **MAJOR** — significant gap or imbalance; ships poorly but not incorrect.
- **MINOR** — polish; safe to defer.

## Report format (consumed by fix-chapter)

```
# Chapter NN Content Audit — <chapter title>
audited: <ISO date>  |  target pages: <n>  |  actual est: <n>

## CRITICAL
- [line/section] <issue> → <what's needed>
## MAJOR
- ...
## MINOR
- ...

## Objective coverage
| LO | covered? | where |
```

Save to `{reports}/chNN.audit.md` (per-chapter). `fix-chapter` reads exactly this path.

## Guardrails
- Audit, don't fix. The only output is the report.
- Compare against the ACTUAL outline/LO on disk, never an assumed structure.
- If the outline for this chapter is missing, say so and stop — audit needs a baseline.
