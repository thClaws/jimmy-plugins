#!/usr/bin/env python3
"""mockup_screenshot.py — render placeholder app-UI mockups (bundled).

Reads the screenshot inventory.json and renders a 1440x900 mockup PNG for each entry
that has no image file yet (or all requested), using the bundled Sarabun fonts. Every
rendered entry is marked "status": "mockup" in the inventory so book-router can track
the human replace-with-real gate.

The window chrome (app name, tabs, sidebar) is NOT hardcoded — it comes from
{workspace}/book.yaml -> mockup: {app_name, tabs, sidebar}. Left empty (or with no
book.yaml / no PyYAML), the mockup draws a neutral empty window, which is honest;
drawing some other product's UI would not be.

Inventory formats accepted (tolerant):
  {"needed": [ {"file": "01-home.png", "title": "...", "description": "...",
                "chapter": 1}, ... ]}
  {"screenshots": [ ...same shape... ]}   or a bare list [ ... ].
Entries may use keys file/filename, title/name, description/desc.

Usage:
  python3 mockup_screenshot.py <workspace> [all|chapter-N|<filename>]
                               --font-dir DIR [--force] [--shots-dir DIR]

Exit codes: 0 ok, 1 input error, 2 missing dependency.
"""
import argparse, json, os, sys, glob

try:
    import yaml
except ImportError:
    yaml = None

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

def load_book(workspace):
    path = os.path.join(workspace, "book.yaml")
    if yaml is None or not os.path.exists(path):
        if yaml is None:
            log("PyYAML not installed — drawing a neutral window (no app chrome)")
        return {}
    try:
        return yaml.safe_load(open(path, encoding="utf-8")) or {}
    except Exception as e:
        log(f"WARNING: could not read book.yaml ({e}) — drawing a neutral window")
        return {}

def chrome_from(book):
    """book.yaml -> mockup: {app_name, tabs, sidebar}. Empty = neutral window."""
    m = (book.get("mockup") or {}) if isinstance(book, dict) else {}
    as_list = lambda v: [str(x) for x in v if str(x).strip()] if isinstance(v, list) else []
    return {"app_name": str(m.get("app_name") or "").strip(),
            "tabs": as_list(m.get("tabs")),
            "sidebar": as_list(m.get("sidebar"))}

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

def render(entry, out_path, font_dir, chrome):
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
    # tab bar — first tab is the active one; no tabs configured = no tab bar
    tabs = chrome["tabs"]
    if tabs:
        span = 100
        x0 = W // 2 - (len(tabs) * span) // 2
        for i, tab in enumerate(tabs):
            x = x0 + i * span
            active = i == 0
            d.text((x, 12), tab, font=f_sm, fill=WHITE if active else GRAY)
            if active:
                d.rectangle([x - 6, 38, x + 66, 41], fill=TEAL)
    # sidebar — only when the book declares one
    side_w = 240 if (chrome["app_name"] or chrome["sidebar"]) else 0
    if side_w:
        d.rectangle([0, 44, side_w, H], fill=DARK)
        if chrome["app_name"]:
            d.text((20, 64), chrome["app_name"], font=f_md, fill=WHITE)
        for i, item in enumerate(chrome["sidebar"][:8]):
            d.text((20, 120 + i * 40), item, font=f_sm, fill=GRAY)
    # content area
    d.rectangle([side_w, 44, W, H], fill=PARCH)
    cx, cw = side_w + 40, W - side_w - 80
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
    ap.add_argument("--shots-dir",
                    help="override the screenshot dir (default: book.yaml layout.screenshots)")
    args = ap.parse_args(argv)

    book = load_book(args.workspace)
    chrome = chrome_from(book)
    if not (chrome["tabs"] or chrome["sidebar"] or chrome["app_name"]):
        log("book.yaml has no mockup: chrome — rendering neutral windows")
    rel = args.shots_dir or ((book.get("layout") or {}).get("screenshots")
                             if isinstance(book, dict) else None) or "media/screenshots"
    shots_dir = rel if os.path.isabs(rel) else os.path.join(args.workspace, rel)
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
        render(e, out, args.font_dir, chrome)
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
