---
name: generate-tts
description: >
  Generate the per-slide voice-over audio for a chapter with Pinn.ai TTS
  (mcp__pinn-ai__text2speech) — reads each slide's speaker notes from the compiled
  chNN.yaml and produces deterministic WAV files (build/audio/chNN/slide-NN.wav) plus a
  manifest, ready for build-chapter-video. Use when the user asks to "สร้างเสียง",
  "gen เสียงพากย์", "ทำ TTS", "generate voice over", "อัดเสียงสไลด์", "tts บทที่ N",
  or when the router reaches the TTS stage (slide images ready, audio missing).
---

## Paths (thai-book-production layout)

หนึ่ง working folder = หนังสือหนึ่งเล่ม Resolve ทุก path จาก `book.yaml → layout:` ที่ root
ของ folder — **ห้าม hardcode** ถ้าไม่มี `book.yaml` แปลว่าไม่ได้อยู่ใน book folder ให้ให้
`book-router` scaffold ก่อน ค่า default:

| what | path |
|------|------|
| slides (build artifact, แหล่ง notes) | `media/slides/chNN.yaml` |
| slide images (จาก slides2preview) | `build/slides/preview/chNN/slide-*.png` |
| **audio output** | `build/audio/chNN/slide-NN.wav` + `manifest.json` |
| video output (ขั้นถัดไป) | `build/video/chNN.mp4` |


# Generate TTS — Per-slide Voice-over (Pinn.ai)

Turns each slide's `notes:` (the voice-over script written by `create-book-yaml`) into a
WAV file via **`mcp__pinn-ai__text2speech`**. Output naming is deterministic so
`build-chapter-video` (ffmpeg) can pair audio to slide images by index.

## Config (from `book.yaml → style.tts`)
```yaml
style:
  tts:
    voice: Charon                    # ชายโทน informative (default) — ดูรายชื่อใน tool description
    model: google/gemini-3.1-flash-tts
    style_hint: ""                   # optional เช่น "Say warmly, like a friendly trainer:"
```
All optional — defaults shown. `style_hint`, when set, is prepended to every slide's text.

## Process (per chapter NN)
1. Resolve paths; read `{slides}/chNN.yaml`; abort loudly if missing or has no `slides`.
2. Ensure `build/audio/chNN/` exists. Read existing `manifest.json` if present.
3. For each slide `i` (1-based, zero-padded `slide-01` … order = document order):
   - `text` = the slide's `notes` (verbatim — it was written TTS-ready; prepend
     `style_hint` if configured). Slides with no notes → **skip** and record
     `"audio": null` in the manifest (video stage will hold the slide silently).
   - **Idempotent:** if `slide-NN.wav` already exists and the manifest's stored text
     matches the current notes, skip it. Regenerate only missing/changed slides
     (or everything, if the user says "regen เสียงทั้งบท").
   - Call `mcp__pinn-ai__text2speech(text=<text>, voice=<voice>, model=<model>)` →
     download the returned WAV: `curl -L -o build/audio/chNN/slide-NN.wav "<url>"`.
   - Text over 8000 chars: split at sentence boundaries into parts, generate each, and
     concat with ffmpeg (`concat` demuxer) into the single slide WAV.
4. Write/update `build/audio/chNN/manifest.json`:
   ```json
   { "chapter": 1, "voice": "Charon", "model": "google/gemini-3.1-flash-tts",
     "slides": [ {"index": 1, "file": "slide-01.wav", "chars": 512,
                  "text_sha1": "…", "duration_s": 38.2} , … ] }
   ```
   (duration via `ffprobe -show_entries format=duration`.)
5. Report: ตาราง slide → ไฟล์/ข้าม/ความยาว, รวมความยาวทั้งบท และสไลด์ที่ notes ว่าง.

## Guardrails
- Notes are the **final script** — do not rewrite/summarize them here. Fix wording in
  `.slides.md` → recompile → regenerate the affected slide only.
- Writes only under `build/audio/`. Deterministic names; never rename slide images.
- If Pinn.ai is unavailable or a call fails, keep what succeeded, list which slides are
  missing, and stop — never leave a silently incomplete manifest.
- Credits: ~1 credit per 2000-character block per slide — with long chapters, tell the
  user the slide count before a full run.
