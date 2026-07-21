#!/usr/bin/env python3
"""slides_yaml2marp.py — compile chNN.yaml → Marp markdown (thai-tech theme).

Maps the 12 slide types to Marp-md + HTML that the `thai-tech` CSS theme styles.
Output is fed to the slide-render service (Marp + Chromium) → pdf + per-slide png.
This replaces the python-pptx deck (low design ceiling) — design lives in CSS.

  python3 slides_yaml2marp.py chNN.yaml [-o chNN.marp.md] [--theme thai-tech]

Image refs ({{screenshot:file}} / a screenshot filename) are emitted as <img src=...>;
the render service resolves them against the media dirs passed alongside.
Requires: pyyaml.
"""
import argparse, html, os, sys

try:
    import yaml
except ImportError:
    sys.stderr.write("pyyaml required: pip install pyyaml --break-system-packages\n")
    sys.exit(2)

SEP = "\n\n---\n\n"


def esc(s):
    return html.escape(str(s or "")).replace("\n", "<br>")


def txt(s):
    # plain markdown text (keep as-is, collapse newlines to spaces for inline)
    return " ".join(str(s or "").split())


def bullets_md(items, ordered=False):
    mark = (lambda i: f"{i+1}.") if ordered else (lambda i: "-")
    return "\n".join(f"{mark(i)} {txt(b)}" for i, b in enumerate(items or []))


def bullets_html(items):
    return "".join(f"<li>{esc(txt(b))}</li>" for b in (items or []))


def img_src(name):
    """A screenshot/image filename → relative src the render service resolves."""
    if not name:
        return ""
    n = str(name)
    # allow {{screenshot:foo}} / {{image:id}} forms
    if n.startswith("{{"):
        n = n.strip("{} ").split(":", 1)[-1].split("|", 1)[0].strip()
    if not n.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        n += ".png"
    return n


def cover(s):
    kick = s.get("chapter") or ""
    out = ['<!-- _class: cover -->', '<!-- _paginate: false -->']
    if kick:
        out.append(f'<div class="kicker">{esc(kick)}</div>')
    out.append(f"\n# {txt(s.get('title'))}")
    if s.get("subtitle"):
        out.append(f'\n<div class="sub">{esc(s["subtitle"])}</div>')
    return "\n".join(out)


def quote(s):
    q = txt(s.get("text") or s.get("quote") or s.get("title"))
    attr = txt(s.get("attribution") or s.get("attr") or "")
    out = ['<!-- _class: quote -->', f"\n> {q}"]
    if attr:
        out.append(f'\n<div class="attr">— {esc(attr)}</div>')
    return "\n".join(out)


def section(s):
    cards = s.get("cards") or []
    grid = "cards two" if len(cards) <= 2 else "cards"
    head = "## " + " · ".join(x for x in [txt(s.get("number")), txt(s.get("title"))] if x)
    out = ['<!-- _class: section -->', head]
    if s.get("subtitle"):
        out.append(f"### {txt(s['subtitle'])}")
    cs = "".join(
        f'<div class="card"><div class="lbl">{esc(c.get("label"))}</div>'
        f'<div class="ct">{esc(c.get("title"))}</div><p>{esc(c.get("body"))}</p></div>'
        for c in cards
    )
    out.append(f'\n<div class="{grid}">{cs}</div>')
    return "\n".join(out)


def content(s):
    out = ['<!-- _class: content -->', f"## {txt(s.get('title'))}"]
    if s.get("subtitle"):
        out.append(f"### {txt(s['subtitle'])}")
    out.append("\n" + bullets_md(s.get("bullets"), ordered=bool(s.get("numbered"))))
    return "\n".join(out)


def two_column(s):
    left, right = s.get("left") or {}, s.get("right") or {}
    body = (
        f'<div class="twocol">'
        f'<div class="col"><div class="hd">{esc(left.get("header"))}</div>'
        f'<ul>{bullets_html(left.get("bullets"))}</ul></div>'
        f'<div class="col alt"><div class="hd">{esc(right.get("header"))}</div>'
        f'<ul>{bullets_html(right.get("bullets"))}</ul></div></div>'
    )
    return f"<!-- _class: content -->\n## {txt(s.get('title'))}\n\n{body}"


def timeline(s):
    evs = "".join(
        f'<div class="ev"><span class="dot"></span><div class="yr">{esc(e.get("year"))}</div>'
        f'<div class="et">{esc(e.get("title"))}</div><p>{esc(e.get("body"))}</p></div>'
        for e in (s.get("events") or [])
    )
    out = [f"## {txt(s.get('title'))}", f'\n<div class="tl">{evs}</div>']
    c = s.get("callout")
    if isinstance(c, dict):
        items = "".join(f"<li>{esc(txt(b))}</li>" for b in (c.get("bullets") or []))
        out.append(
            f'\n<div class="callout"><div class="tag">{esc(c.get("title") or "หมายเหตุ")}</div>'
            f"<ol>{items}</ol></div>"
        )
    return "\n".join(out)


def process(s):
    sts = "".join(
        f'<div class="st"><div class="n">{esc(st.get("number") or i+1)}</div>'
        f'<div class="pt">{esc(st.get("title"))}</div><p>{esc(st.get("body"))}</p></div>'
        for i, st in enumerate(s.get("steps") or [])
    )
    out = [f"## {txt(s.get('title'))}"]
    if s.get("subtitle"):
        out.append(f"### {txt(s['subtitle'])}")
    out.append(f'\n<div class="proc">{sts}</div>')
    return "\n".join(out)


def table(s):
    hs = s.get("headers") or []
    rows = s.get("rows") or []
    md = ["<!-- _class: tabl -->", f"## {txt(s.get('title'))}", ""]
    md.append("| " + " | ".join(txt(h) for h in hs) + " |")
    md.append("|" + "|".join("---" for _ in hs) + "|")
    for r in rows:
        md.append("| " + " | ".join(txt(c) for c in r) + " |")
    return "\n".join(md)


def callout(s):
    style = (s.get("style") or "tip").strip()
    body = s.get("body")
    if isinstance(body, list):
        inner = "<ol>" + "".join(f"<li>{esc(txt(b))}</li>" for b in body) + "</ol>"
    else:
        inner = f"<p>{esc(body)}</p>"
    tag = {"tip": "Tip", "warning": "Warning", "concept": "Concept"}.get(style, style.title())
    box = f'<div class="callout {style}"><div class="tag">{esc(tag)}</div>{inner}</div>'
    return f"## {txt(s.get('title'))}\n\n{box}"


def demo(s):
    out = ['<!-- _class: demo -->', '<div class="badge">DEMO</div>',
           f"\n## {txt(s.get('subtitle') or s.get('title') or 'DEMO')}"]
    code = s.get("code") or s.get("body")
    if code:
        out.append(f'\n<div class="term">{esc(code)}</div>')
    return "\n".join(out)


def screenshot(s):
    src = img_src(s.get("screenshot") or s.get("image"))
    frame = (f'<img src="{esc(src)}">' if src else
             '<div class="ph">🖼️ (screenshot pending)</div>')
    out = ['<!-- _class: shot -->']
    if s.get("title"):
        out.append(f"## {txt(s['title'])}")
    if s.get("subtitle"):
        out.append(f"### {txt(s['subtitle'])}")
    out.append(f'\n<div class="frame">{frame}</div>')
    if s.get("description"):
        out.append(f'<div class="cap">{esc(s["description"])}</div>')
    return "\n".join(out)


def video_demo(s):
    out = ['<!-- _class: video -->', '<div class="play"></div>',
           f"\n## {txt(s.get('title'))}"]
    if s.get("description"):
        out.append(f'\n<div class="desc">{esc(s["description"])}</div>')
    if s.get("duration"):
        out.append(f'<div class="dur">▶ {esc(s["duration"])}</div>')
    return "\n".join(out)


RENDERERS = {
    "cover": cover, "quote": quote, "section": section, "content": content,
    "two_column": two_column, "timeline": timeline, "process": process,
    "table": table, "callout": callout, "demo": demo, "screenshot": screenshot,
    "video_demo": video_demo,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("yaml")
    ap.add_argument("-o", "--out")
    ap.add_argument("--theme", default="thai-tech")
    a = ap.parse_args()

    d = yaml.safe_load(open(a.yaml, encoding="utf-8")) or {}
    slides = d.get("slides") or []
    if not slides:
        sys.stderr.write(f"no slides in {a.yaml}\n"); sys.exit(1)

    front = f"---\nmarp: true\ntheme: {a.theme}\npaginate: true\n---\n\n"
    blocks, unknown = [], []
    for i, s in enumerate(slides):
        t = s.get("type", "content")
        fn = RENDERERS.get(t)
        if fn is None:
            unknown.append(t)
            fn = content  # graceful fallback
        blocks.append(fn(s))

    md = front + SEP.join(blocks) + "\n"
    out = a.out or os.path.splitext(a.yaml)[0] + ".marp.md"
    open(out, "w", encoding="utf-8").write(md)
    sys.stderr.write(f"✓ {len(slides)} slides → {out}\n")
    if unknown:
        sys.stderr.write(f"⚠ unknown types (rendered as content): {sorted(set(unknown))}\n")


if __name__ == "__main__":
    main()
