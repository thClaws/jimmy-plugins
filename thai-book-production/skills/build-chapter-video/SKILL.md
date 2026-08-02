---
name: build-chapter-video
description: >
  Assemble the chapter training video DETERMINISTICALLY with the bundled ffmpeg script
  `scripts/slides2video.py` — pairs the rendered slide images (slides2preview) with the
  per-slide TTS WAVs (generate-tts) by index, builds one H.264/AAC segment per slide,
  and concats them into build/video/chNN.mp4. Use when the user asks to "สร้างวิดีโอ",
  "ทำวิดีโอบท", "ประกอบวิดีโอ", "build chapter video", "render video", "รวมสไลด์เป็นวิดีโอ",
  or when the router reaches the VIDEO stage (slide images + TTS ready).
---

## Paths (thai-book-production layout)

หนึ่ง working folder = หนังสือหนึ่งเล่ม Resolve ทุก path จาก `book.yaml → layout:` ที่ root
ของ folder — **ห้าม hardcode** ถ้าไม่มี `book.yaml` แปลว่าไม่ได้อยู่ใน book folder ให้ให้
`init-book` scaffold ก่อน ค่า default:

| what | path |
|------|------|
| slide images (input) | `build/slides/preview/chNN/slide-*.png` (จาก slides2preview.py) |
| audio (input, sparse ได้) | `build/audio/chNN/slide-NN.wav` (จาก generate-tts) |
| **video output** | `build/video/chNN.mp4` |


# Build Chapter Video — Deterministic (ffmpeg)

Two deterministic steps in one script: per-slide video segments (image + its WAV; slides
without audio get a silent hold), then concat into the chapter video. No LLM decisions —
pairing is strictly by index (`slide-01.png` ↔ `slide-01.wav`).

## Preconditions
- Slide images rendered (`slides2preview.py`) — count must equal the slide count.
- TTS generated (`generate-tts`) for the slides that have notes. Missing WAV = silent
  hold (`--hold`, default 4s); a WAV with no matching image = hard error.
- **Human gates passed**: outline approved, and screenshots `status: real` (or the human
  explicitly OK'd shipping with mockups) — check with `book-router` if unsure.

## Run
```bash
mkdir -p build/video
python3 {skill_dir}/scripts/slides2video.py \
  --images build/slides/preview/chNN \
  --audio  build/audio/chNN \
  -o build/video/chNN.mp4
```
Flags: `--hold N` (วินาทีของสไลด์ไม่มีเสียง, default 4), `--tail N` (ช่วงเงียบท้ายสไลด์มีเสียง,
default 0.5), `--fps N` (default 30), `--height N` (default 1080 → 16:9), `--keep-segments`
(เก็บ seg-NN.mp4 ไว้ debug).

Output: H.264 (yuv420p, CRF 20) + AAC 48k stereo, 1920×1080 @30fps — identical encode
params per segment so the concat is lossless-safe.

Requires `ffmpeg` + `ffprobe` (`apt-get install ffmpeg`); preflight via
`skills/build-slides-pptx/scripts/check_env.py`.

## After the build
- Report: slide count, voiced count, total duration; deliver `chNN.mp4` to the user.
- Stale-input check: if `chNN.yaml` / slide images / WAVs are newer than the mp4, the
  video is stale — recommend re-running the affected upstream stage first.

## Guardrails
- Deterministic only — this skill never edits notes, images, or audio. Fix upstream
  (`.slides.md` → recompile → re-render / regen TTS) and re-run.
- Writes only under `build/video/`.
- Fail loudly on count mismatches; never silently drop a slide.
