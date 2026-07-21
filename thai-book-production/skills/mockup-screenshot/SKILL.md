---
name: mockup-screenshot
description: >
  Generate placeholder mockup PNG screenshots for the Thai Cowork book using programmatic UI renderings.
  Use this skill whenever the user asks to "generate mockups", "create placeholder screenshots",
  "make mockup screenshots", "สร้าง mockup", "สร้าง screenshot จำลอง", or mentions needing
  screenshots for chapters but doesn't have real ones yet. Also trigger when the user runs
  /mockup-screenshot. This skill reads media/screenshots/inventory.json and renders realistic-looking
  Claude Desktop UI mockups for any missing screenshots, using the Sarabun Thai font.
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


# Mockup Screenshot Generator

This skill generates placeholder PNG mockups that simulate Claude Desktop UI screenshots, allowing
chapter writing to proceed before real screenshots are captured.

**Scope — real screenshots only (`{{screenshot:...}}`).** This skill covers the **screenshot** image
kind: UI captures of the app, living in `{screenshots}/` (`media/screenshots/`). It produces stand-in
mockups until the real capture exists. It does **NOT** handle AI illustrations — those are the
**generated** kind (`{{image:...}}`, `media/generated/`) and belong to the `generate-image` skill
(Pinn.ai). Never write into `{generated}/` from here.

## What It Does

Reads `media/screenshots/inventory.json` (specifically the `needed` array), then for each missing screenshot
renders a PNG using the bundled `mockup_screenshot.py` script with:
- Dark Claude Desktop window chrome (1440×900 px)
- Correct tab bar (Chat / Cowork), sidebar, and content area
- Thai text rendered with the bundled Sarabun font
- Template-specific content matching each screenshot's purpose

## Step 1: Find the Workspace

Use `Glob` with `**/media/screenshots/inventory.json` to find the workspace. The parent directory of
`media/screenshots/` is the workspace root.

## Step 2: Determine Font Path

The Sarabun fonts are bundled in this skill:

```bash
FONT_DIR="${CLAUDE_PLUGIN_ROOT}/skills/mockup-screenshot/assets/fonts/Sarabun"
```

Verify fonts exist:
```bash
ls "$FONT_DIR" | head -5
```

If empty or missing, check if the user has fonts elsewhere:
```bash
find /sessions -name "Sarabun-Regular.ttf" 2>/dev/null | head -3
```

## Step 3: Parse Arguments

`$ARGUMENTS` can be:

| Value | Behavior |
|-------|----------|
| (empty) | Generate all missing screenshots from inventory.json `needed` list |
| `all` | Same as empty — generate everything not yet present |
| `chN` | Only generate mockups for chapter N (e.g., `ch3`) |
| A filename | Generate just that one file (e.g., `05-typing-task-in-cowork.png`) |

## Step 4: Run the Generator

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/mockup-screenshot/scripts/mockup_screenshot.py" \
  <workspace> \
  ${ARGUMENTS:-all} \
  --font-dir "$FONT_DIR"
```

The script will:
1. Read `media/screenshots/inventory.json`
2. Match needed filenames to templates
3. Skip files that already exist (unless `--force` is passed)
4. Write PNGs to the paths specified in `suggested_filename`
5. Print a summary of what was generated

## Step 5: Report Results

After the script completes, report:

```
Generated N mockup screenshots:
  ✓ media/screenshots/01-chat-tab-home-screen.png
  ✓ media/screenshots/02-cowork-tab-home-screen.png
  ...

Already existed (skipped):
  - media/screenshots/05-typing-task-in-cowork.png

Use /list-screenshot to rescan the inventory.
```

## When to Regenerate with --force

If the user says "recreate" or "regenerate" or "overwrite", pass `--force`:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/mockup-screenshot/scripts/mockup_screenshot.py" \
  <workspace> \
  ${ARGUMENTS:-all} \
  --font-dir "$FONT_DIR" \
  --force
```

## Status tracking — mockup vs real (human gate)

Every entry in `{screenshots}/inventory.json` carries a **`status`** field:
- `"status": "mockup"` — set by this skill whenever it renders a placeholder
- `"status": "real"` — set when the human has captured the real screenshot

**Replacement flow (คนทำ):** the human captures the real UI, saves it over the **same
filename** in `{screenshots}/`, then tells Claude "เปลี่ยน <ไฟล์> เป็นภาพจริงแล้ว" (or "ภาพจริงครบแล้ว")
→ update those entries to `status: real`. `book-router` treats any remaining
`status: mockup` as an open **human gate** before slides/video are rendered — the deck may
ship with mockups only if the human explicitly allows it.

To list what's still pending: read inventory.json and report every `status: mockup` entry
with its chapter and description.

## Quality Notes

- Mockups are clearly labeled as "[MOCKUP]" in the image so they're distinguishable from real screenshots
- When real screenshots are captured and saved with the same filename, they automatically replace the mockups
  (remember to update inventory `status` → `real`)
- The generator skips files that already exist to avoid overwriting real screenshots
- All mockups are 1440×900 px at 96 DPI — same dimensions as the recommended real screenshots
