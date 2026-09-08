---
name: get-book-ref
description: >
  Search for and download official documentation and blog posts about a given topic from any source,
  saving them as Markdown reference files for the current book project (`book.yaml`). Use this skill whenever
  the user asks to "find docs", "get reference", "download documentation", "หาเอกสาร", "ดาวน์โหลด doc",
  "เพิ่ม reference", "add reference", "get book ref", or mentions needing official source material
  for the book. Also trigger when the user says "search for official docs about {topic}" or
  "find blog about {topic}". This skill identifies who owns the topic first, then searches their
  official documentation sites and blogs, downloading complete articles to refs/docs/ and refs/blogs/ directories.
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


# Get Book Reference — Download Official Docs & Blogs

## Overview

This skill searches the official documentation and blog domains for the book's subject (from `book.yaml → sources:`), downloads the complete content, and saves it as properly formatted Markdown in the book project's `refs/docs/` and `refs/blogs/` directories.

The topic may be owned by any company or project. The first step is always to identify WHO owns the topic and WHERE their official docs live, then fetch from those sources.

Every book in this pipeline is grounded in official reference material — the outline and every chapter are written from what lands in `refs/docs/` and `refs/blogs/`. Which sources count as "official" depends on the book, so they come from `book.yaml`, never from this file.

## Project Folder Structure

(โครงจริงดูจากตาราง **## Paths** ด้านบน — resolve จาก `book.yaml → layout:` เสมอ: outline/, refs/docs/, refs/blogs/, chapters/chNN.md, media/…)

Find the workspace root the same way every other skill in this plugin does: `Glob` for
`**/book.yaml`. Its parent directory is the book folder; resolve `refs_docs` / `refs_blogs`
from `book.yaml → layout:`. No `book.yaml` ⇒ not a book folder ⇒ hand to `init-book`.

## Step 0: Understand the Request

This skill runs in **two passes** within the PLAN loop:

- **Seed pass** (before the outline exists) — the topic is the book's overall subject
  (from `book.yaml → book.title` / user). Pull the *core* authoritative docs so
  `outline-planner` can ground the structure on real material. Keep it bounded to the
  subject; don't drag in the whole ecosystem.
- **Targeted pass** (after a draft outline) — the topic is a specific gap the outline
  exposed (a chapter/subtopic lacking source material). Fetch narrowly to fill it.

The user (or `book-router`) will specify a **topic**, always inside the book's subject
(`book.yaml → book.subject`) — a feature of it, an area around it, or a specific concept it
involves. Parse the topic and prepare search queries for both documentation and blog posts.

## Step 1: Check What Already Exists

Before searching, read the existing files to avoid duplicates:

```bash
# List existing docs
ls <workspace>/refs/docs/
# List existing blogs
ls <workspace>/refs/blogs/
```

Read the first few lines (especially the `> Source:` line) of existing files to know which URLs are already downloaded. Skip any URLs that are already present.

## Step 2: Search for Official Documentation

### Step 2a — Who owns this topic?

Read `book.yaml → sources:`.

- **Populated** → use those domains directly. They were confirmed for this book already.
- **Empty** → find the owner *first*, then search. A topic belongs to whoever builds it:
  a product has a vendor, a language has a foundation, a standard has a body. Search
  `"{subject} official documentation"` / `"{subject} docs"`, confirm the domains actually
  belong to that owner (not an aggregator, tutorial farm, or SEO clone), then **write them
  back to `book.yaml → sources`** so every later pass reuses the same answer instead of
  re-deriving it. Tell the user which domains you settled on.

### Step 2b — Search those domains

For each domain in `sources.official_docs` and `sources.official_blogs`:

```
WebSearch: "site:{domain} {topic}"
WebSearch: "{subject} {topic} documentation"
WebSearch: "{subject} {topic} 2025 OR 2026"        # recency, when the topic moves fast
```

Keep URLs whose host matches a `sources:` domain. Anything off-domain is a candidate, not a
source: only add it after checking it really is published by the owner (a vendor's docs
sometimes live on a second domain — add that domain to `sources` too).

**Only official material.** Tutorials, Medium posts, Stack Overflow answers and AI-generated
summaries are not sources for this book; they belong in the author's head, not in `refs/`.

## Step 3: Download and Save Documents

For each relevant URL found, download the complete content and save it as Markdown.

### Downloading Content

Use `WebFetch` or `mcp__e1a77f26-ab93-4b01-a818-338deeebc6f8__scrape_url` to fetch the full page content. The scrape_url tool often gets better results for complete article extraction.

**Important:** Try to get the COMPLETE document. Don't settle for truncated content. If the first fetch is incomplete:
- Try `scrape_url` with `scroll_to_bottom: true` for lazy-loaded content
- Try fetching with different tools to get the fullest version
- If content is still partial, note this in the file header

### File Naming Convention

**For docs:**
```
NN-{slug}.md
```
Where NN is the next number after the highest existing doc number (zero-padded to 2 digits), and {slug} is a kebab-case summary of the article title.

Example: If the last doc is `08-deployment-guide.md`, the next one is `09-{slug}.md`.

**For blogs:**
```
NN-{slug}.md
```
Same numbering convention, continuing from the highest existing blog number.

### File Format

Every saved file MUST follow this exact format to be compatible with the book writing skill:

**For support docs:**
```markdown
# {Article Title}

> Source: {full URL}
> Owner: {Company or Project Name}

{Complete article content in Markdown}
```

**For blog posts:**
```markdown
# {Blog Post Title}

> Source: {full URL}
> Owner: {Company or Project Name}
> Date: {publication date if available}
> Category: {categories if available}

{Complete blog post content in Markdown}
```

### Content Formatting Rules

When converting to Markdown:
- Preserve all headings (##, ###, etc.)
- Preserve all lists (bulleted and numbered)
- Preserve code blocks with appropriate language tags
- Preserve tables
- Preserve bold/italic emphasis
- Remove navigation elements, sidebars, footers, and cookie notices
- Remove "Related articles" sections at the bottom
- Keep image alt text references but note that images won't be downloaded
- Clean up any HTML artifacts

## Step 4: Update the Folder Map

After adding new files, check if the `write-book-chapter/SKILL.md` folder map needs updating. If new doc or blog files were added, update the folder map section to include them so chapter-writing agents know they exist.

Read `write-book-chapter/SKILL.md` and update the Folder Map section's refs/docs/ and refs/blogs/ file listings if needed.

## Step 5: Report Results

After downloading, provide a summary:

```
Downloaded {N} new documents:

Docs:
- refs/docs/09-{slug}.md — "{Title}" (from {domain})
  {word count} words, complete/partial

Blogs:
- refs/blogs/05-{slug}.md — "{Title}" (from {domain})
  {word count} words, complete/partial

Already existed (skipped):
- {URL} → already saved as refs/docs/01-{slug}.md

Not found:
- No official {topic} documentation found on the domains in `sources:`
```

## Tips for Better Results

- **Be thorough with search queries** — Try multiple phrasings. A doc might not mention `book.subject` in its title and still be exactly the source you need.
- **Check for recently published content** — official docs move fast. Include the year in searches (2025, 2026).
- **Prefer complete over partial** — It's better to have one complete doc than three truncated ones.
- **Watch for redirects** — Some URLs redirect. Follow the redirect and save the final content.
- **Cross-reference the book outline** — Read `outline/outline.md` to understand which topics need references. This helps prioritize which docs to download.

## Quality Checklist

Before finishing, verify:
- [ ] All new files have the correct `> Source:` header with real URL
- [ ] File numbering is sequential (no gaps, no duplicates)
- [ ] Content is complete (not truncated mid-sentence)
- [ ] Markdown formatting is clean (no HTML artifacts)
- [ ] No duplicate downloads (same URL saved twice)
- [ ] The write-book-chapter skill's folder map is updated if needed
