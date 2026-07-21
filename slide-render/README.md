# slide-render

Marp + Chromium slide-rendering microservice for **thai-book-production**. Renders a
Marp markdown deck (produced by `slides_yaml2marp.py`) into a **PDF + per-slide PNGs**
using the `thai-tech` CSS theme + bundled Thai fonts. Replaces the python-pptx deck
(low design ceiling) **and** the local LibreOffice/`soffice` step (missing/flaky on
macOS) with one image — design lives in CSS, rendered by Chromium.

## API

```
GET  /healthz                → { ok: true }
POST /slides   (multipart)
       markdown = <marp md>           (required)
       theme    = thai-tech           (optional; must exist in themes/)
       images   = <file> …            (0+ screenshots/figures referenced by <img src="name.png">)
   → 200 application/zip  { deck.pdf, slides/slide-01.png, slide-02.png, … }
   → 400 bad input · 401 unauthorized · 500 render failed
```

Auth: `Authorization: Bearer $SLIDE_RENDER_TOKEN` (check skipped if the env is unset —
dev only; in prod it sits behind the gateway which does auth).

## Run locally
```
npm install
npm install -g @marp-team/marp-cli@4        # or set MARP_BIN
export CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"   # macOS
node server.js                               # :8080
curl -sS -X POST localhost:8080/slides -F markdown=@deck.md -F theme=thai-tech -o deck.zip
```

## Build + deploy (cloud)
```
docker build -t registry.artech.cloud/slide-render:v0.1.0 .
# deploy as a k3s Deployment+Service in thclaws-cloud; expose via gateway /slide-render/*
```
**Chromium in Docker:** Chromium's sandbox needs either a non-root user or `--no-sandbox`
(the image sets `CHROMIUM_FLAGS`). Mirror marp-team/marp-cli's official image (runs as a
non-root user) for the hardened path, and render with **no network** (untrusted decks).

## ⚠️ Architecture constraint (hard)
The **desktop/GUI must NEVER call this API directly.** Flow is always:

```
Frontend (React/GUI) ─IPC→ thClaws Rust engine ─relay(token)→ slide-render API
```
The gateway/cloud token lives in Rust only; the GUI/gui-shell CSP blocks external hosts
anyway; auth/policy/metering stay on the same `resolve_access_key()` path as the media
tools (billed via the gateway ×1.25 markup). Preferred mechanism: a built-in Rust tool
`RenderSlides` (mirrors `TextToImage`) that the `build-slides-pptx` skill invokes —
backend-initiated by construction. GUI live-preview goes via an IPC command → the same
Rust relay, never a direct `fetch`.

## Contents
- `server.js` — Express service (multipart in → zip out, per-request temp dir, cleaned).
- `themes/thai-tech.css` — the 12-slide-type theme (navy/teal/gold, Prompt + Sarabun).
- `themes/fonts/*.ttf` — bundled Prompt + Sarabun (also installed system-wide by the image).
- `Dockerfile` — node + chromium + Thai fonts + marp-cli.

The Marp markdown ↔ slide-type mapping lives in the plugin:
`thai-book-production/skills/build-slides-pptx/scripts/slides_yaml2marp.py`.
