# YAML Slide Format — Developer Manual

Reference for the YAML slide definition format — the compile target consumed by the in-plugin pipeline (build-slides-pptx → generate-tts → build-chapter-video).

## File Structure

```yaml
meta:
  book: <book-slug>        # e.g. "claude-cowork", "claude-code"
  chapter: <int>           # Chapter number (1-indexed)
  title: <string>          # Chapter title
  subtitle: <string>       # Chapter subtitle

slides:
  - type: <slide-type>
    # ... type-specific fields
    notes: |               # Speaker notes (used for TTS narration)
      Multi-line narration text
    broll:                 # Optional — b-roll metadata for video
      - type: <broll-type>
        desc: "Description of the visual"
        at: "0:15"
```

### `meta` Block

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `book` | string | Yes | Book slug matching directory name under `books/` |
| `chapter` | int | Yes | Chapter number. Used to derive output filenames (`Chapter01.pptx`, `ch01-slide-01.wav`) |
| `title` | string | No | Chapter title (informational) |
| `subtitle` | string | No | Chapter subtitle (informational) |

### Common Fields (All Slide Types)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Slide layout type (see below) |
| `notes` | string | No | Speaker notes. Used as TTS input by `generate-tts` (Pinn.ai). Multi-line with `\|` block scalar |
| `broll` | list | No | B-roll visual metadata for video production (see B-Roll section) |

---

## Slide Types

### `cover`

Chapter title slide. Dark navy background with teal accents.

```yaml
- type: cover
  chapter: "บทที่ 1"       # Chapter label (displayed in teal badge)
  title: "Chapter Title"   # Large white title
  subtitle: "Subtitle"     # Gold-colored subtitle
  notes: |
    ...
```

| Field | Type | Description |
|-------|------|-------------|
| `chapter` | string | Chapter badge text (e.g. "บทที่ 1", "Chapter 1") |
| `title` | string | Main title |
| `subtitle` | string | Subtitle (gold color) |

---

### `quote`

Full-slide quote with attribution. Dark navy background.

```yaml
- type: quote
  text: "Quote text here"
  attribution: "— Author Name"
  notes: |
    ...
```

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Quote body |
| `attribution` | string | Author/source (typically prefixed with "—") |

---

### `section`

Section divider with 2–5 info cards. Parchment background. The template variant is auto-selected based on card count.

```yaml
- type: section
  number: "1.1"
  title: "Section Title"
  subtitle: "Section subtitle"
  cards:
    - label: "Label 1"     # Teal badge text
      title: "Card Title"  # Card heading
      body: |              # Multi-line card body
        Line 1
        Line 2
    - label: "Label 2"
      title: "Card 2 Title"
      body: |
        ...
  notes: |
    ...
```

| Field | Type | Description |
|-------|------|-------------|
| `number` | string | Section number (e.g. "1.1", "2.3") — displayed in teal |
| `title` | string | Section title |
| `subtitle` | string | Section subtitle |
| `cards` | list | 2–5 card objects |
| `cards[].label` | string | Badge label (shown in teal pill) |
| `cards[].title` | string | Card heading |
| `cards[].body` | string | Card body text (supports multi-line with `\|`) |

**Template variants:** `section-2`, `section-3`, `section-4`, `section-5`. Card count is clamped to 2–5.

---

### `content`

General bullet-point slide. The workhorse layout. Parchment background.

```yaml
- type: content
  title: "Slide Title"
  subtitle: "Subtitle"
  bullets:
    - "First bullet point"
    - "Second bullet point"
    - "Third bullet point"
  numbered: false          # Optional — use 1. 2. 3. instead of bullets
  notes: |
    ...
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `title` | string | | Slide title |
| `subtitle` | string | | Subtitle (gray) |
| `bullets` | list[string] | | Bullet point items |
| `numbered` | bool | `false` | When `true`, renders as numbered list (1. 2. 3.) |

---

### `two_column`

Side-by-side comparison layout. Parchment background with navy left header and teal right header.

```yaml
- type: two_column
  title: "Comparison Title"
  subtitle: "Subtitle"
  left:
    header: "Left Column"
    bullets:
      - "Left bullet 1"
      - "Left bullet 2"
  right:
    header: "Right Column"
    bullets:
      - "Right bullet 1"
      - "Right bullet 2"
  notes: |
    ...
```

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Slide title |
| `subtitle` | string | Subtitle |
| `left.header` | string | Left column header (navy background) |
| `left.bullets` | list[string] | Left column bullet points |
| `right.header` | string | Right column header (teal background) |
| `right.bullets` | list[string] | Right column bullet points |

---

### `timeline`

Vertical timeline with 3–5 events. Parchment background with teal circles and connecting line.

```yaml
- type: timeline
  title: "Timeline Title"
  subtitle: "Subtitle"
  events:
    - year: "2021"
      title: "Event Title"
      body: "Event description"
    - year: "2023"
      title: "Another Event"
      body: "Description"
  callout:                  # Optional callout box
    title: "Note"
    bullets:
      - "Additional info"
  notes: |
    ...
```

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Slide title |
| `subtitle` | string | Subtitle |
| `events` | list | 3–5 event objects |
| `events[].year` | string | Year/label in teal circle |
| `events[].title` | string | Event heading |
| `events[].body` | string | Event description |
| `callout` | object | Optional callout box |
| `callout.title` | string | Callout heading |
| `callout.bullets` | list[string] | Callout bullet points |

**Template variants:** `timeline-3`, `timeline-4`, `timeline-5`. Event count is clamped to 3–5.

---

### `process`

Step-by-step process in a 2-column grid. Parchment background with numbered circles.

```yaml
- type: process
  title: "Process Title"
  subtitle: "Subtitle"
  steps:
    - number: 1
      title: "Step 1"
      body: |
        Step description
    - number: 2
      title: "Step 2"
      body: |
        Step description
  footer: "Footer note text"
  notes: |
    ...
```

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Slide title |
| `subtitle` | string | Subtitle |
| `steps` | list | 2–6 step objects |
| `steps[].number` | int | Step number (defaults to position index + 1) |
| `steps[].title` | string | Step heading |
| `steps[].body` | string | Step description (multi-line) |
| `footer` | string | Optional footer text (centered, gray) |

**Template variants:** `process-2` through `process-6`. Step count is clamped to 2–6. Steps are arranged in a 2-column grid (rows = ceil(n/2)).

---

### `table`

Data table with headers and rows. Table is generated programmatically on a template background.

```yaml
- type: table
  title: "Table Title"
  subtitle: "Subtitle"
  headers:
    - "Column 1"
    - "Column 2"
    - "Column 3"
  rows:
    - ["Cell 1", "Cell 2", "Cell 3"]
    - ["Cell 4", "Cell 5", "Cell 6"]
  notes: |
    ...
```

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Slide title |
| `subtitle` | string | Subtitle |
| `headers` | list[string] | Column header labels (navy background, white text) |
| `rows` | list[list[string]] | Row data (alternating white/teal-soft background) |

---

### `callout`

Highlighted callout box with accent bar and numbered body. Parchment background.

```yaml
- type: callout
  style: tip                # tip | warning | concept
  title: "Callout Title"
  body: |
    First numbered point
    Second numbered point
    Third numbered point
  notes: |
    ...
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `style` | string | `"tip"` | Visual style — sets accent color and icon |
| `title` | string | | Callout heading (icon is auto-prepended) |
| `body` | string | | Body text. Each `\n`-separated line becomes a numbered item (1. 2. 3.) |

**Styles:**

| Style | Accent Color | Icon |
|-------|-------------|------|
| `tip` | Gold | ✦ |
| `warning` | Red | ▲ |
| `concept` | Teal | ◆ |

---

### `demo`

Live demo interstitial slide. Dark navy background with large "DEMO" text.

```yaml
- type: demo
  title: "DEMO"              # Usually left as "DEMO" (hardcoded in template)
  subtitle: "Demo description"
  notes: |
    ...
```

| Field | Type | Description |
|-------|------|-------------|
| `subtitle` | string | Demo topic description (centered, secondary color) |

Note: The `title` field exists but the template renders fixed "DEMO" text. The `subtitle` is the meaningful field.

---

### `screenshot`

Screenshot display slide. Parchment background. If an image file exists, it's rendered full-bleed (16:9). Otherwise shows a placeholder with description text.

```yaml
# Option A: Reference screenshot in book's screenshots/ directory
- type: screenshot
  screenshot: "01-chat-tab-home-screen.png"
  notes: |
    ...

# Option B: Explicit image path
- type: screenshot
  image: "/absolute/path/to/image.png"
  title: "Screenshot Title"
  subtitle: "Subtitle"
  notes: |
    ...

# Option C: Placeholder (no image file)
- type: screenshot
  title: "Screenshot Title"
  subtitle: "Subtitle"
  description: "Description of what should appear here"
  notes: |
    ...
```

| Field | Type | Description |
|-------|------|-------------|
| `screenshot` | string | Filename in `books/<book>/screenshots/` directory |
| `image` | string | Explicit image path (takes priority over `screenshot`) |
| `title` | string | Slide title (hidden when image is full-bleed) |
| `subtitle` | string | Subtitle |
| `description` | string | Placeholder text shown when no image file exists |

**Image resolution:** When an image file exists, it's added at full-bleed 16:9 (10" × 5.625" = 1920×1080 at 192 DPI).

---

### `video_demo`

Video demo announcement slide. Dark navy background with play icon and optional duration badge.

```yaml
- type: video_demo
  title: "Video Demo Title"
  description: "What the demo shows"
  duration: "2:30"          # Optional — shows teal duration badge
  notes: |
    ...
```

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Demo title (white, centered) |
| `description` | string | Demo description (secondary color) |
| `duration` | string | Duration label (e.g. "2:30"). Shows as teal badge. Hidden if omitted |

---

## B-Roll Metadata

Optional metadata. Not consumed by the slide renderer — used for video production planning.

```yaml
broll:
  - type: screenshot
    desc: "Claude Desktop Settings > Usage page showing token breakdown"
    at: "0:15"
  - type: diagram
    desc: "Flowchart of the agentic loop: Observe → Plan → Act → Reflect"
    at: "0:25"
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | One of: `screenshot`, `screencast`, `picture`, `graph`, `diagram`, `animation` |
| `desc` | string | Specific, actionable description of the visual |
| `at` | string | Approximate timing within the slide's audio (e.g. "0:05", "0:15") |

**B-roll types:**

| Type | Use For |
|------|---------|
| `screenshot` | Static UI capture |
| `screencast` | Short screen recording with cursor movement |
| `picture` | Photo or illustration |
| `graph` | Chart or data visualization |
| `diagram` | Flowchart, architecture diagram |
| `animation` | Motion graphic or animated explanation |

---

## Pipeline Integration (in-plugin, standalone)

### YAML → PPTX + slide images (`build-slides-pptx`)
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/build-slides-pptx/scripts/slides2preview.py \
  media/slides/chNN.yaml --book book.yaml --out build/slides --strict-fonts
```
- Outputs: `build/slides/chNN.pptx`, `chNN-slides.pdf`, `preview/chNN/slide-*.png`,
  contact sheet, `chNN-image.pptx` (font-proof)

### YAML notes → TTS audio (`generate-tts` skill)
- Per-slide `notes:` → `mcp__pinn-ai__text2speech` → `build/audio/chNN/slide-NN.wav` + manifest
- Voice/model configured in `book.yaml → style.tts`

### Slide images + audio → chapter video (`build-chapter-video`)
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/build-chapter-video/scripts/slides2video.py \
  --images build/slides/preview/chNN --audio build/audio/chNN -o build/video/chNN.mp4
```
- Pairs by index; slides without audio get a silent hold. Output H.264/AAC 1920×1080.

## Renderer Design (in-code theme)

The renderer (`slides2pptx.py`) holds the full design in code — palette/fonts/sizes per the
Design System above, one layout function per slide type, Thai text on the complex-script
slot. Custom theme via `--theme theme.json` or `book.yaml → style.pptx_theme` (deep-merge).
No external template file is required.
