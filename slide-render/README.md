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
   → 200 application/zip  { deck.pdf, slides/slide.001.png, slide.002.png, … }
       + X-Slide-Count: <n>           (rendered pages — the gateway bills off this)
   → 400 bad input / malformed upload · 401 unauthorized · 500 render failed
```

The two routes do NOT name their PNGs the same way: Marp emits `slide.001.png`
(dot, 3-digit) and pdftoppm emits `slide-N.png` with the width set by the page
count (`slide-1` for a 2-page deck, `slide-01` for a 12-page one). Both sort
correctly within a document, and the engine's `RenderSlides` renumbers either
form to the `slide-NN.png` the rest of the toolchain pairs against
(`slide-01.png` ↔ `slide-01.wav`). Do not depend on the raw names.

Both render routes set **`X-Slide-Count`** before the zip starts streaming. It is
the billing unit: the gateway reads it off the 2xx and debits the caller's credit
per page. A 2xx without it (a pre-0.2.0 image mid-rollout) is billed the floor of
one page and logged as an error — so **deploy this service before the gateway
that meters it**, never the other way round.

Auth: `Authorization: Bearer $SLIDE_RENDER_TOKEN` (check skipped if the env is unset —
dev only; in prod it sits behind the gateway which does auth).

## Billing

Rendering is **not free**. The hosted service has no public Ingress, so the only
route to it is `{gateway}/slide-render/*`, and that route is metered: the caller's
gateway bearer is authenticated, their credit balance gates the request, and a
successful render is debited per page at `SLIDE_RENDER_MICROS_PER_PAGE`
(micro-cents, pre-markup; `200000` = $0.002/page ⇒ a 20-page chapter deck is 5¢ at
the default ×1.25). `/pptx` has its own rate, `SLIDE_RENDER_PPTX_MICROS_PER_PAGE`,
defaulting to `0` — that route backs the Files-tab preview of a deck the user
already owns, which has always been free.

Running your own copy and pointing `SLIDE_RENDER_API` at it costs nothing, because
it is your compute. That branch cannot reach the hosted service.

## Dependencies

`package-lock.json` is authoritative and the image builds from it (`npm ci`), so a rebuild of
a given commit ships the exact versions that were audited. Re-run `npm audit --package-lock-only`
after any dependency change.

`npm audit` is clean as of 2026-09-08, on Express 5 and multer 2. Both upgrades were verified
against a running container, not just a build: `/healthz`, every 400 path, a real Marp render of
a Thai deck, and a LibreOffice `/pptx` conversion, all as uid 10001.

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
docker build -t registry.artech.cloud/slide-render:v0.4.0 .
# deploy as a k3s Deployment+Service in thclaws-cloud; expose via gateway /slide-render/*
kubectl apply -f k8s.yaml      # Deployment + Service + HPA + PodDisruptionBudget
```

**The live deployment had drifted from this file.** As of 2026-09-08 the cluster was on
revision 6 running `v0.3.0`, while `k8s.yaml` still said `v0.1.0` — the image and the resource
limits had been changed with `kubectl` and never written back. The manifest is now the truth
again, so the next `kubectl apply -f k8s.yaml` will also reset the memory request (live 384Mi →
manifest 512Mi) and add the HPA, PodDisruptionBudget and securityContext. That is intended; it
is listed here so it is not a surprise. Patch by editing this file and applying it, not with
`kubectl set image`.

**Scaling.** Every request is self-contained — its own temp dir, removed in
`finally`, nothing shared — so the Service fans out over any number of pods with no
session affinity and no shared volume. `k8s.yaml` ships an HPA (1→6 pods on 60% CPU;
CPU is the signal because a render pins a core for roughly a second per page) and a
PodDisruptionBudget, since a render can run up to `TIMEOUT_MS` and dies with its pod.
Once the HPA is applied it owns `replicas` — stop editing that field by hand.
**Chromium in Docker:** the image runs as the unprivileged `render` user (uid 10001) and
still passes `--no-sandbox`, because Chromium's setuid sandbox needs `SYS_ADMIN` that the pod
does not get. The two are not alternatives: no-sandbox is forced by the container, and the
non-root user is what limits where an escaped renderer can write. Render with **no network**
(untrusted decks).

## ⚠️ Architecture constraint (hard)
The **desktop/GUI must NEVER call this API directly.** Flow is always:

```
Frontend (React/GUI) ─IPC→ thClaws Rust engine ─relay(token)→ slide-render API
```
The gateway/cloud token lives in Rust only; the GUI/gui-shell CSP blocks external hosts
anyway; auth/policy/metering stay on the same `resolve_access_key()` path as the media
tools (billed via the gateway ×1.25 markup). Mechanism: the built-in Rust tool
**`RenderSlides`** (thClaws engine `tools/slide_render.rs`, mirrors `TextToImage`) that the
`build-slides-pptx` skill invokes — backend-initiated by construction. It resolves the
endpoint `SLIDE_RENDER_API` (self-hosted) → thClaws Gateway `/slide-render/slides` (metered),
sends the marp-md + images as multipart, and unzips `deck.pdf` + `slide.*.png` into `out_dir`.
GUI live-preview goes via an IPC command → the same Rust relay, never a direct `fetch`.

## Contents
- `server.js` — Express service (multipart in → zip out, per-request temp dir, cleaned).
- `themes/thai-tech.css` — the 12-slide-type theme (navy/teal/gold, Prompt + Sarabun).
- `themes/fonts/*.ttf` — bundled Prompt + Sarabun (also installed system-wide by the image).
- `Dockerfile` — node + chromium + Thai fonts + marp-cli.

The Marp markdown ↔ slide-type mapping lives in the plugin:
`thai-book-production/skills/build-slides-pptx/scripts/slides_yaml2marp.py`.
