#!/usr/bin/env python3
"""check_env.py — preflight dependency check for thai-book-production scripts.

Runs on any machine BEFORE the pipeline scripts, using ONLY the standard library
(so it works even when the deps are missing) and warns about what's not installed.

Checks:
  REQUIRED    Python packages the scripts import (pyyaml, python-pptx)
  RECOMMENDED optional packages that improve output (Pillow)
  EXTERNAL    optional CLI tools used by some stages (curl, soffice, pandoc, ...)

Exit code: 0 = all REQUIRED present; 1 = a REQUIRED package is missing
           (with --strict, RECOMMENDED misses also cause exit 1).

Usage:
  python3 check_env.py                # human-readable report
  python3 check_env.py --strict       # fail if RECOMMENDED missing too
  python3 check_env.py --json         # machine-readable
  python3 check_env.py --quiet        # print only on problems / final line
"""
import sys
import argparse
import importlib.util
import shutil
import json

# (import_name, pip_name, why)
REQUIRED = [
    ("yaml", "pyyaml", "อ่าน book.yaml / chNN.yaml (slides_md2yaml.py, slides2pptx.py)"),
    ("pptx", "python-pptx", "render สไลด์เป็น .pptx (build-slides-pptx)"),
]
RECOMMENDED = [
    ("PIL", "Pillow", "คำนวณสัดส่วนภาพ screenshot ให้พอดี (slides2pptx.py)"),
]
# (cmd, stage, required_for_stage?)
EXTERNAL = [
    ("curl", "optional — media downloads (built-in tools write files directly)"),
    ("soffice", "slides2preview.py (แปลง .pptx เป็น PDF เพื่อพรีวิว/font-proof)"),
    ("pdftoppm", "slides2preview.py (แตก PDF เป็น PNG รายสไลด์ — poppler-utils)"),
    ("fc-match", "slides2preview.py (ด่านตรวจฟอนต์ก่อนเรนเดอร์ — fontconfig)"),
    ("ffmpeg", "build-chapter-video (ประกอบวิดีโอจากสไลด์+เสียง)"),
    ("ffprobe", "generate-tts/build-chapter-video (วัดความยาวเสียง)"),
    ("pandoc", "build-epub-pdf (สร้าง epub/pdf)"),
    ("xelatex", "build-epub-pdf (PDF ภาษาไทย)"),
    ("epubcheck", "build-epub-pdf (ตรวจ epub)"),
]

PY_MIN = (3, 8)


def has_module(name):
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def collect():
    py_ok = sys.version_info >= PY_MIN
    req = [(imp, pip, why, has_module(imp)) for imp, pip, why in REQUIRED]
    rec = [(imp, pip, why, has_module(imp)) for imp, pip, why in RECOMMENDED]
    ext = [(cmd, why, shutil.which(cmd) is not None) for cmd, why in EXTERNAL]
    return py_ok, req, rec, ext


def main(argv=None):
    ap = argparse.ArgumentParser(description="Preflight dependency check")
    ap.add_argument("--strict", action="store_true", help="fail if RECOMMENDED missing too")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--quiet", action="store_true", help="print only problems + verdict")
    args = ap.parse_args(argv)

    py_ok, req, rec, ext = collect()
    missing_req = [pip for _, pip, _, ok in req if not ok]
    missing_rec = [pip for _, pip, _, ok in rec if not ok]
    pip_to_install = missing_req + (missing_rec if args.strict else [])
    ok_overall = py_ok and not missing_req and not (args.strict and missing_rec)

    if args.json:
        print(json.dumps({
            "python": ".".join(map(str, sys.version_info[:3])),
            "python_ok": py_ok,
            "required": {pip: ok for _, pip, _, ok in req},
            "recommended": {pip: ok for _, pip, _, ok in rec},
            "external": {cmd: ok for cmd, _, ok in ext},
            "missing_required": missing_req,
            "missing_recommended": missing_rec,
            "ok": ok_overall,
        }, ensure_ascii=False, indent=2))
        return 0 if ok_overall else 1

    def line(mark, label, note):
        print(f"  {mark}  {label:<16} {note}")

    if not args.quiet:
        print("thai-book-production — ตรวจสภาพแวดล้อม (preflight)\n")
        print(f"Python {'.'.join(map(str, sys.version_info[:3]))}"
              f"  {'✓ ok' if py_ok else f'✗ ต้อง >= {PY_MIN[0]}.{PY_MIN[1]}'}\n")
        print("REQUIRED (จำเป็น):")
        for _, pip, why, ok in req:
            line("✓" if ok else "✗", pip, why if ok else f"ขาด — {why}")
        print("\nRECOMMENDED (ควรมี):")
        for _, pip, why, ok in rec:
            line("✓" if ok else "•", pip, why)
        print("\nEXTERNAL CLI (เฉพาะบางเฟส, ไม่บังคับ):")
        for cmd, why, ok in ext:
            line("✓" if ok else "•", cmd, why)
        print()

    # warnings
    if missing_req:
        sys.stderr.write("⚠️  ขาดแพ็กเกจที่จำเป็น: " + ", ".join(missing_req) + "\n")
    if missing_rec:
        sys.stderr.write("ℹ️  ยังไม่มีแพ็กเกจที่แนะนำ: " + ", ".join(missing_rec) + "\n")
    if pip_to_install:
        sys.stderr.write("👉  ติดตั้งด้วย:\n     pip install "
                         + " ".join(pip_to_install) + " --break-system-packages\n")

    print(("✅ พร้อมใช้งาน — dependency ครบ" if ok_overall
           else "❌ ยังไม่พร้อม — ติดตั้งแพ็กเกจที่ขาดก่อน (ดูด้านบน)"))
    return 0 if ok_overall else 1


if __name__ == "__main__":
    sys.exit(main())
