---
name: fix-chapter
description: >
  Fix chapter issues identified in the audit report. Reads the latest audit report,
  extracts all CRITICAL and MAJOR issues for the target chapter, then rewrites the
  chapter to address every flagged issue while preserving good content. Use when the
  user runs /fix-chapter or asks to "fix chapter", "แก้บท", "fix audit issues",
  "apply audit fixes", or "rewrite chapter based on audit".
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


# Fix Chapter — Audit-Driven Chapter Revision

## Overview

This skill rewrites a book chapter to fix all issues identified by `/audit`. It reads the audit report, extracts the issue list for the target chapter, loads the original chapter + reference material, then produces a corrected version that addresses every CRITICAL and MAJOR issue while preserving content that was not flagged.

**Philosophy:** Fix, don't rewrite from scratch. The goal is surgical improvement — keep what works, fix what's broken, expand what's thin.

## Project Folder Structure

Same as write-book-chapter. Find the workspace root with `Glob` pattern `**/outline/*.md`.

```
<book-folder>/
├── book.yaml
├── outline/outline.md + plan.md (+ APPROVED.md)
├── refs/docs/ + refs/blogs/
├── chapters/chNN.md            ← chapters to fix
├── media/slides/chNN.slides.md → chNN.yaml   (re-generate after fix)
├── media/screenshots/ + media/generated/
└── reports/chNN.audit.md       ← ★ THE AUDIT REPORT (your guide)
```

## Step 1: Read and Validate the Audit Report

Read `reports/chNN.audit.md`. Check for the YAML front-matter block:

```yaml
---
audit_rev: N
generated: "YYYY-MM-DD"
chapters_audited: [1, 2, 3, ...]
book_version: "X.Y.Z"
issues:
  critical: N
  major: N
  minor: N
  total: N
---
```

**Validation checks:**
1. The front-matter MUST exist. If it doesn't, warn the user: "Audit report has no revision metadata. Please re-run /audit to generate a versioned report."
2. The target chapter number MUST be in `chapters_audited`. If not: "Chapter N was not included in the last audit. Run /audit N first."
3. Check that `audit_rev` exists — this is what `/fix-chapter` uses to confirm it's working from the right version.

If the front-matter is missing but the report content exists (old-format report), proceed with a warning but recommend re-running `/audit`.

## Step 2: Extract Issues for Target Chapter

From the audit report, find the section `### Chapter N: {title}` and extract:

1. **All numbered issues** with their severity tags: `[CRITICAL]`, `[MAJOR]`, `[MINOR]`
2. **Recommended fixes** — the bulleted list under each chapter's issues
3. **Cross-chapter issues** that mention this chapter (from the "Cross-Chapter Issues" section)
4. **Redundancy map entries** that involve this chapter

Create a working checklist of ALL issues to address. Group them:

```
MUST FIX (block publication):
- [CRITICAL-1] ...
- [CRITICAL-2] ...

SHOULD FIX (significantly improves quality):
- [MAJOR-1] ...
- [MAJOR-2] ...

NICE TO FIX (polish):
- [MINOR-1] ...
- [MINOR-2] ...
```

## Step 3: Read Source Material

Load these in parallel:

1. **The original chapter** — `chapters/ch{NN}.md`
2. **The outline** — `outline/outline.md` (or `outline/outline.md`)
3. **Reference docs** — read the relevant `refs/docs/` and `refs/blogs/` files for this chapter's topic
4. **Screenshot inventory** — read `media/screenshots/inventory.json` (+ `info.md`/`index.md` in subdirs) and list the real filenames available for this chapter
5. **Adjacent chapters** — read chapter N-1 and N+1 (if they exist) to maintain cross-chapter flow

## Step 4: Plan the Fix

Before writing, plan your approach for each issue:

### For CRITICAL issues (factually wrong):
- Find the exact line(s) in the original chapter
- Cross-reference with the reference docs to get the correct information
- Plan the corrected text

### For MAJOR flow/redundancy issues:
- Map which sections need restructuring
- Identify content to remove (duplicates) vs content to add (gaps)
- Plan new transitions between sections

### For MAJOR content gaps (thin chapters):
- Identify which sections need expansion
- Pull enrichment material from reference docs
- Plan new subsections, examples, or callout boxes

### For consistency issues:
- Build a find-replace list (e.g., "โหมด {Term}" → "{Term}", mixed terminology → standardized)

### For screenshot issues:
- List missing screenshots that need `{{screenshot:...}}` placeholders
- List duplicate screenshot references to consolidate
- List screenshots that need repositioning

## Step 5: Rewrite the Chapter

Now rewrite the chapter applying ALL planned fixes. Follow these rules:

### Preservation Rules
- **Keep the chapter structure** (h1, h2, h3 hierarchy) unless the audit specifically flags restructuring
- **Keep good content** — don't rewrite paragraphs that weren't flagged
- **Keep the opening story** unless flagged for relevance issues — but fix factual errors in it
- **Keep all screenshot placeholders** — only add/remove/reposition as the audit directs
- **Keep the summary section** — update it to reflect any content changes
- **Keep the reference section** at the bottom

### Fix Rules
- **CRITICAL fixes take absolute priority** — these are factual errors that mislead readers
- **Remove ALL duplicated content** — if the audit flags repeated sections, keep only the best version and delete the rest
- **Expand thin sections** by pulling from reference docs — don't just add filler words, add real substance (examples, explanations, step-by-step guidance)
- **Add callout boxes** where the audit flags missing tips/warnings — use the format:
  ```
  > **เคล็ดลับ:** {tip text}
  > **ข้อควรระวัง:** {warning text}
  ```
- **Fix terminology** consistently across the entire chapter
- **Add cross-references** where the audit flags forward references: "ดูรายละเอียดในบทที่ N"
- **Fix screenshot placement** — move screenshots near the text they illustrate

### Writing Quality Rules (same as write-book-chapter)
- **5,000-7,000 Thai words** per chapter (expand if below, trim if above)
- **No gendered particles** (ครับ, ค่ะ)
- **Friendly, professional tone** — like a knowledgeable colleague
- **Concrete examples** — every concept should have a practical example
- **Screenshot format** (real UI): `{{screenshot:filename.png|คำอธิบายภาษาไทย}}`
- **AI illustration format** (concept art): `{{image:ch-id|คำอธิบายภาษาไทย}}` — resolved by
  `generate-image` (built-in TextToImage); id is kebab-case, no `.png`. Don't reuse an id across both kinds.
- **ONLY use screenshot filenames that exist in `media/screenshots/` (per inventory.json)** — never invent filenames

### For Thin Chapters (under 5,000 words)

When the audit flags a chapter as too thin, expand it by:

1. **Adding more examples** — concrete use cases, sample prompts, expected outputs
2. **Adding step-by-step walkthroughs** — break high-level instructions into detailed steps
3. **Adding comparison tables** — before/after, do/don't, feature comparisons
4. **Adding callout boxes** — tips, warnings, notes (aim for 4-8 per chapter)
5. **Expanding the project exercise** — add intermediate checkpoints and success criteria
6. **Pulling depth from reference docs** — the chapter may summarize what the docs explain in detail

Do NOT pad with:
- Repetitive restating of the same point
- Generic filler ("AI is changing the world...")
- Excessive disclaimers or caveats

## Step 6: Validate

After writing, run validation:

Validate inline (no external script):

Check that:
1. Word count is in the 5,000-7,000 range (or closer than before)
2. Screenshot count meets minimum (8+)
3. All screenshot files exist
4. Callouts are present
5. All structural elements exist (opening story, summary, references, project)

## Step 7: Save and Verify

Save the fixed chapter to the same path: `chapters/ch{NN}.md`

Then do a **diff summary** — describe what changed:
- Sections added
- Sections removed (duplicates)
- Sections restructured
- Facts corrected
- Word count: before → after
- Issues addressed: N of M

## Step 8: Bump Revision

## Step 9: Report to User

Present a summary for each fixed chapter:

```
### Chapter N: {title}
- Words: {before} → {after}
- Score: {before}/11 → {after}/11
- Issues fixed: {count} of {total} ({critical} critical, {major} major, {minor} minor)
- Key changes:
  - {bullet 1}
  - {bullet 2}
  - {bullet 3}
- Remaining issues (if any): {list}
```

**Important:** After fixing chapters, their YAML files (if they exist) become stale and will need re-generation with `/create-yaml`. Mention this to the user.

## Issue Fix Patterns

Quick reference for common audit issue types:

| Issue Type | Fix Pattern |
|-----------|-------------|
| Factual error | Cross-reference with refs/docs/, correct the claim, add source citation |
| Content duplication | Keep best version, delete others, smooth transitions |
| Thin chapter | Expand with examples, steps, callouts from reference docs |
| Missing screenshot | Add `{{screenshot:...}}` at relevant position (check inventory first) |
| Terminology inconsistency | Find-replace across entire chapter |
| Bad flow/ordering | Restructure sections, add transition paragraphs |
| Missing safety warning | Add callout box with warning from refs/docs/02-use-cowork-safely |
| Forward reference | Add "ดูบทที่ N" or rephrase to not assume future knowledge |
| Unsupported claim | Remove claim or find supporting evidence in reference docs |
| Pricing/version info | Add caveat "ราคาอาจเปลี่ยนแปลง ดูข้อมูลล่าสุดที่ claude.com/pricing" |
