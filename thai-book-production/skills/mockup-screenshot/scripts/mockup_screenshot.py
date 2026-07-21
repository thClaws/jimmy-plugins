#!/usr/bin/env python3
"""mockup_screenshot.py — render placeholder Claude Desktop UI mockups (bundled).

Reads {workspace}/media/screenshots/inventory.json and renders a 1440x900 mockup PNG
for each entry that has no image file yet (or all requested), using the bundled
Sarabun fonts. Every rendered entry is marked "status": "mockup" in the inventory so
book-router can track the human replace-with-real gate.

Inventory formats accepted (tolerant):
  {"needed": [ {"file": "01-home.png", "title": "...", "description": "...",
                "chapter": 1}, ... ]}
  {"screenshots": [ ...same shape... ]}   or a bare list [ ... ].
Entries may use keys file/filename, title/name, description/desc.

Usage:
  python3 mockup_screenshot.py <workspace> [all|chapter-N|<filename>]
                               --font-dir DIR [--force]

Exit codes: 0 ok, 1 input error, 2 missing dependency.
"""
import argparse, json, os, sys, glob

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.stderr.write("Pillow required: pip install Pillow --break-system-packages\n")
    sys.exit(2)

W, H = 1440, 900
NAVY = (13, 27, 42); DARK = (8, 19, 31); PANEL = (22, 50, 79)
PARCH = (248, 246, 240); TEAL = (0, 122, 110); TEAL_SOFT = (220, 234, 232)
GRAY = (90, 106, 126); WHITE = (255, 255, 255); LINE = (227, 223, 213)

def log(m): sys.stderr.write(f"[mockup] {m}\n")

def load_font(font_dir, weight, size):
    cand = {"bold": ["Sarabun-Bold.ttf", "Sarabun-SemiBold.ttf"],
            "medium": ["Sarabun-Medium.ttf", "Sarabun-Regular.ttf"],
            "regular": ["Sarabun-Regular.ttf"]}[weight]
    for name in cand:
        for p in glob.glob(os.path.join(font_dir, "**", name), recursive=True):
            return ImageFont.truetype(p, size)
    log(f"WARNING: Sarabun not found in {font_dir}; using default font")
    return ImageFont.load_default()

def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for word in str(text).split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur: lines.append(cur)
            cur = word
    if cur: lines.append(cur)
    return lines or [""]

def render(entry, out_path, font_dir):
    title = entry.get("title") or entry.get("name") or os.path.basename(out_path)
    desc = entry.get("description") or entry.get("desc") or ""
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    f_big = load_font(font_dir, "bold", 30)
    f_md = load_font(font_dir, "medium", 20)
    f_sm = load_font(font_dir, "regular", 16)

    # window chrome
    d.rectangle([0, 0, W, 44], fill=DARK)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([16 + i * 24, 15, 30 + i * 24, 29], fill=c)
    # tab bar
    for i, (tab, active) in enumerate([("Chat", False), ("Cowork", True), ("Code", False)]):
        x = W // 2 - 150 + i * 100
        col = WHITE if active else GRAY
        d.text((x, 12), tab, font=f_sm, fill=col)
        if active:
            d.rectangle([x - 6, 38, x + 66, 41], fill=TEAL)
    # sidebar
    d.rectangle([0, 44, 240, H], fill=DARK)
    d.text((20, 64), "Claude", font=f_md, fill=WHITE)
    for i, item in enumerate(["+ New task", "Recents", "Projects", "Customize", "Settings"]):
        d.text((20, 120 + i * 40), item, font=f_sm, fill=GRAY)
    # content area
    d.rectangle([240, 44, W, H], fill=PARCH)
    cx, cw = 280, W - 320
    d.text((cx, 90), title, font=f_big, fill=NAVY)
    d.rectangle([cx, 136, cx + 70, 140], fill=TEAL)
    y = 165
    for ln in wrap(d, desc, f_md, cw)[:6]:
        d.text((cx, y), ln, font=f_md, fill=(42, 56, 72)); y += 30
    # placeholder card
    d.rounded_rectangle([cx, y + 20, cx + cw, H - 120], 14, fill=WHITE, outline=LINE, width=2)
    d.rounded_rectangle([cx, y + 20, cx + cw, y + 26], 3, fill=TEAL)
    hint = wrap(d, desc or title, f_sm, cw - 80)[:3]
    hy = (y + 20 + H - 120) // 2 - len(hint) * 11
    for ln in hint:
        tw = d.textlength(ln, font=f_sm)
        d.text((cx + (cw - tw) // 2, hy), ln, font=f_sm, fill=TEAL); hy += 24
    # watermark
    d.text((W - 190, H - 40), "[ MOCKUP ]", font=f_md, fill=(204, 51, 51))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG", dpi=(96, 96))

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace")
    ap.add_argument("scope", nargs="?", default="all",
                    help="all | chN / chapter-N | a specific filename")
    ap.add_argument("--font-dir", required=True)
    ap.add_argument("--force", action="store_true",
                    help="re-render even if the PNG exists (never overwrites status:real)")
    args = ap.parse_args(argv)

    shots_dir = os.path.join(args.workspace, "media", "screenshots")
    inv_path = os.path.join(shots_dir, "inventory.json")
    if not os.path.exists(inv_path):
        log(f"no inventory.json at {inv_path}"); return 1
    inv = json.load(open(inv_path, encoding="utf-8"))
    entries = inv.get("needed") or inv.get("screenshots") or \
        (inv if isinstance(inv, list) else [])
    if not entries:
        log("inventory has no entries"); return 0

    done = skipped = 0
    for e in entries:
        fname = e.get("file") or e.get("filename")
        if not fname:
            continue
        if args.scope != "all":
            import re as _re
            m = _re.fullmatch(r"(?:chapter-|ch)(\d+)", args.scope)
            if m:
                if str(e.get("chapter", "")) != m.group(1):
                    continue
            elif os.path.basename(fname) != os.path.basename(args.scope):
                continue
        out = os.path.join(shots_dir, fname)
        if e.get("status") == "real":
            skipped += 1; continue                     # never touch real captures
        if os.path.exists(out) and not args.force:
            skipped += 1; continue
        render(e, out, args.font_dir)
        e["status"] = "mockup"
        done += 1
        log(f"rendered {fname}")

    if not isinstance(inv, list):
        json.dump(inv, open(inv_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
    log(f"done: {done} rendered, {skipped} skipped")
    return 0

if __name__ == "__main__":
    sys.exit(main())
