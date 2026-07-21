#!/usr/bin/env python3
"""slides2video.py — deterministic: slide PNGs + per-slide WAV -> chapter video (ffmpeg).

slide-01.png + slide-01.wav ──▶ seg-01.mp4 ─┐
slide-02.png + slide-02.wav ──▶ seg-02.mp4 ─┤──concat──▶ chNN.mp4
slide-03.png   (no audio)   ──▶ seg-03.mp4 ─┘   (silent hold)

Inputs come from the earlier deterministic stages:
  images : build/slides/preview/chNN/slide-*.png   (slides2preview.py)
  audio  : build/audio/chNN/slide-NN.wav           (generate-tts skill; may be sparse)

Usage:
  python3 slides2video.py --images build/slides/preview/ch01 \
                          --audio  build/audio/ch01 \
                          -o build/video/ch01.mp4 \
                          [--hold 4] [--tail 0.5] [--fps 30] [--height 1080]
                          [--keep-segments]

Rules:
- Slides are paired to audio BY INDEX (slide-01.png <-> slide-01.wav). Missing wav ->
  silent segment of --hold seconds. Extra wavs without a matching image -> hard error.
- Every segment is encoded with identical parameters (H.264 yuv420p + AAC 48k stereo),
  so the concat demuxer can join without re-encoding surprises.
- Output duration per voiced slide = audio duration + --tail padding.

Requires: ffmpeg + ffprobe on PATH. Exit codes: 0 ok, 1 input error, 2 tool missing.
"""
import argparse, glob, os, re, shutil, subprocess, sys, tempfile

def log(m): sys.stderr.write(f"[slides2video] {m}\n")

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        log("cmd failed: " + " ".join(cmd))
        log(r.stderr.strip()[-800:])
        sys.exit(1)
    return r

def audio_duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path])
    return float(r.stdout.strip())

def main(argv=None):
    ap = argparse.ArgumentParser(description="slide PNGs + WAVs -> chapter mp4")
    ap.add_argument("--images", required=True, help="dir with slide-*.png (ordered)")
    ap.add_argument("--audio", help="dir with slide-NN.wav (optional / sparse)")
    ap.add_argument("-o", "--output", required=True, help="output .mp4")
    ap.add_argument("--hold", type=float, default=4.0,
                    help="seconds to show a slide that has no audio (default 4)")
    ap.add_argument("--tail", type=float, default=0.5,
                    help="silence padding after each voiced slide (default 0.5)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--height", type=int, default=1080, help="output height (16:9)")
    ap.add_argument("--keep-segments", action="store_true",
                    help="keep per-slide segment mp4s next to the output")
    args = ap.parse_args(argv)

    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            log(f"ERROR: `{tool}` not found — apt-get install ffmpeg"); sys.exit(2)

    pngs = sorted(glob.glob(os.path.join(args.images, "slide-*.png")))
    if not pngs:
        log(f"no slide-*.png in {args.images}"); sys.exit(1)

    wavs = {}
    if args.audio and os.path.isdir(args.audio):
        for w in glob.glob(os.path.join(args.audio, "slide-*.wav")):
            m = re.search(r"slide-(\d+)\.wav$", w)
            if m:
                wavs[int(m.group(1))] = w
    orphan = [i for i in wavs if i > len(pngs)]
    if orphan:
        log(f"ERROR: audio for slide(s) {orphan} but only {len(pngs)} images"); sys.exit(1)

    w = args.height * 16 // 9
    scale = (f"scale={w}:{args.height}:force_original_aspect_ratio=decrease,"
             f"pad={w}:{args.height}:(ow-iw)/2:(oh-ih)/2:color=black,"
             f"format=yuv420p,fps={args.fps}")

    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    seg_dir = (os.path.splitext(args.output)[0] + "-segments") if args.keep_segments \
        else tempfile.mkdtemp(prefix="s2v_")
    os.makedirs(seg_dir, exist_ok=True)

    segs, total = [], 0.0
    for i, png in enumerate(pngs, 1):
        seg = os.path.join(seg_dir, f"seg-{i:02d}.mp4")
        wav = wavs.get(i)
        if wav:
            dur = audio_duration(wav) + args.tail
            cmd = ["ffmpeg", "-y", "-v", "error",
                   "-loop", "1", "-i", png, "-i", wav,
                   "-t", f"{dur:.3f}", "-vf", scale,
                   "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                   "-c:a", "aac", "-ar", "48000", "-ac", "2",
                   "-af", f"apad=pad_dur={args.tail}", "-shortest", seg]
            kind = f"voiced {dur:5.1f}s"
        else:
            dur = args.hold
            cmd = ["ffmpeg", "-y", "-v", "error",
                   "-loop", "1", "-i", png,
                   "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                   "-t", f"{dur:.3f}", "-vf", scale,
                   "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                   "-c:a", "aac", "-ar", "48000", "-ac", "2", seg]
            kind = f"silent {dur:5.1f}s"
        run(cmd)
        segs.append(seg); total += dur
        log(f"seg {i:02d}/{len(pngs)}  {kind}  <- {os.path.basename(png)}")

    lst = os.path.join(seg_dir, "concat.txt")
    with open(lst, "w") as f:
        for s in segs:
            f.write(f"file '{os.path.abspath(s)}'\n")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", lst, "-c", "copy", args.output])

    voiced = sum(1 for i in range(1, len(pngs) + 1) if i in wavs)
    log(f"wrote {args.output}  ({len(pngs)} slides, {voiced} voiced, "
        f"~{total/60:.1f} min)")
    if not args.keep_segments:
        shutil.rmtree(seg_dir, ignore_errors=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
