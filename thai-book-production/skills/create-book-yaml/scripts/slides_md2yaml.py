#!/usr/bin/env python3
"""slides_md2yaml.py — deterministic compiler: .slides.md -> chNN.yaml

Authoring surface spec : skills/create-book-yaml/references/slide-md-format.md
Compile target spec    : skills/create-book-yaml/references/yaml-format.md

The .slides.md file is the human-editable surface. This script turns it into the
YAML build artifact that the in-plugin pipeline consumes (slides2pptx/preview, generate-tts, slides2video).
Never hand-edit the YAML — edit the .slides.md and recompile.

Usage:
    python3 slides_md2yaml.py CH.slides.md [-o CH.yaml] [--check]

Exit codes: 0 ok · 1 malformed input · 2 missing dependency
"""
import sys
import re
import argparse

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML required: pip install pyyaml --break-system-packages\n")
    sys.exit(2)


# ---- YAML emit: multi-line strings as literal block scalars (notes readability) ----
class Literal(str):
    pass


def _literal_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style="|")


yaml.add_representer(Literal, _literal_representer)


class CompileError(Exception):
    pass


# ---- tokenizers ------------------------------------------------------------
# matches:  key   |   key=value   |   key="quoted value"
_TOKEN_RE = re.compile(r'([\w-]+)(?:=(?:"([^"]*)"|(\S+)))?')
_DIRECTIVE_RE = re.compile(r"<!--\s*slide:\s*(?P<rest>.*?)\s*-->")


def _parse_attrs(text):
    """Return (first_bareword, attrs_dict). Bare flags -> True."""
    toks = []
    for m in _TOKEN_RE.finditer(text):
        key = m.group(1)
        val = m.group(2) if m.group(2) is not None else m.group(3)
        toks.append((key, val))
    if not toks:
        return None, {}
    head = toks[0][0]
    attrs = {}
    for k, v in toks[1:]:
        attrs[k] = True if v is None else v
    return head, attrs


def parse_directive(line):
    m = _DIRECTIVE_RE.search(line)
    if not m:
        return None
    stype, attrs = _parse_attrs(m.group("rest").strip())
    if not stype:
        raise CompileError("empty slide directive")
    return stype, attrs


# ---- structure splitters ---------------------------------------------------
def split_frontmatter(text):
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                fm = yaml.safe_load("\n".join(lines[1:j])) or {}
                return fm, "\n".join(lines[j + 1:])
        raise CompileError("front-matter opened with '---' but never closed")
    return {}, text


def split_slides(body):
    chunks, cur = [], []
    for l in body.splitlines():
        if l.strip() == "---":
            chunks.append(cur)
            cur = []
        else:
            cur.append(l)
    chunks.append(cur)
    return [c for c in chunks if any(x.strip() for x in c)]


def split_blocks(lines):
    """Separate ::: name ... ::: fenced blocks from loose markdown lines."""
    loose, blocks, i = [], [], 0
    while i < len(lines):
        m = re.match(r"^:::\s+([\w-]+)\s*(.*)$", lines[i].strip())
        if m:
            name, attr_str = m.group(1), m.group(2).strip()
            _, attrs = _parse_attrs(name + " " + attr_str)
            inner, i, closed = [], i + 1, False
            while i < len(lines):
                if lines[i].strip() == ":::":
                    closed, i = True, i + 1
                    break
                inner.append(lines[i])
                i += 1
            if not closed:
                raise CompileError(f"unclosed ':::' block: '{name}'")
            blocks.append((name, attrs, inner))
        else:
            loose.append(lines[i])
            i += 1
    return loose, blocks


# ---- markdown field extractors --------------------------------------------
def _headings(loose):
    h1 = h2 = h3 = None
    for l in loose:
        s = l.strip()
        if s.startswith("# ") and h1 is None:
            h1 = s[2:].strip()
        elif s.startswith("## ") and h2 is None:
            h2 = s[3:].strip()
        elif s.startswith("### ") and h3 is None:
            h3 = s[4:].strip()
    return h1, h2, h3


def _bullets(loose):
    out = []
    for l in loose:
        s = l.strip()
        if s.startswith(("- ", "* ")):
            out.append(s[2:].strip())
    return out


def _ordered(loose):
    out = []
    for l in loose:
        m = re.match(r"^\d+\.\s+(.*)$", l.strip())
        if m:
            out.append(m.group(1).strip())
    return out


def _paragraph(loose):
    out = []
    for l in loose:
        s = l.strip()
        if not s or s.startswith(("#", "-", "*", ">", "|")) or re.match(r"^\d+\.\s", s):
            continue
        out.append(s)
    return " ".join(out) if out else None


def _blockquote(loose):
    return [re.sub(r"^>\s?", "", l.strip()) for l in loose if l.strip().startswith(">")]


def _table(loose):
    rows = []
    for l in loose:
        s = l.strip()
        if s.startswith("|") and s.endswith("|"):
            rows.append([c.strip() for c in s.strip("|").split("|")])
    # drop separator row(s) like |---|:--:|
    return [r for r in rows if not all(re.match(r"^:?-+:?$", (c or "-")) for c in r)]


def _inner_text(inner):
    return "\n".join(l.rstrip() for l in inner).strip()


def _find_block(blocks, name):
    for b in blocks:
        if b[0] == name:
            return b
    return None


def _all_blocks(blocks, name):
    return [b for b in blocks if b[0] == name]


# ---- per-type builders -----------------------------------------------------
def _attach_common(slide, blocks):
    nb = _find_block(blocks, "notes")
    if nb:
        slide["notes"] = Literal(_inner_text(nb[2]))
    bb = _find_block(blocks, "broll")
    if bb:
        broll = []
        for l in bb[2]:
            s = l.strip().lstrip("-").strip()
            if not s:
                continue
            parts = [p.strip() for p in s.split("|")]
            item = {"type": parts[0]} if parts else {}
            if len(parts) > 1:
                item["desc"] = parts[1]
            if len(parts) > 2:
                item["at"] = parts[2]
            broll.append(item)
        if broll:
            slide["broll"] = broll
    return slide


def build_slide(stype, attrs, loose, blocks, idx):
    h1, h2, h3 = _headings(loose)
    s = {"type": stype}

    if stype == "cover":
        if "chapter" in attrs:
            s["chapter"] = attrs["chapter"]
        s["title"] = h1 or h2 or ""
        s["subtitle"] = h2 if h1 else (h3 or "")
    elif stype == "quote":
        q = _blockquote(loose)
        attribution = ""
        if q and q[-1].lstrip().startswith("—"):
            attribution = q[-1].strip()
            q = q[:-1]
        s["text"] = " ".join(q).strip()
        s["attribution"] = attribution
    elif stype == "section":
        if "number" in attrs:
            s["number"] = attrs["number"]
        s["title"] = h2 or ""
        if h3:
            s["subtitle"] = h3
        cards = []
        for _, a, inner in _all_blocks(blocks, "card"):
            cards.append({
                "label": a.get("label", ""),
                "title": a.get("title", ""),
                "body": Literal(_inner_text(inner)),
            })
        if cards:
            s["cards"] = cards
    elif stype == "content":
        s["title"] = h2 or ""
        if h3:
            s["subtitle"] = h3
        s["bullets"] = _bullets(loose)
        if attrs.get("numbered"):
            s["numbered"] = True
    elif stype == "two_column":
        s["title"] = h2 or ""
        if h3:
            s["subtitle"] = h3
        for side in ("left", "right"):
            b = _find_block(blocks, side)
            if b:
                s[side] = {"header": b[1].get("header", ""), "bullets": _bullets(b[2])}
    elif stype == "timeline":
        s["title"] = h2 or ""
        if h3:
            s["subtitle"] = h3
        rows = _table(loose)
        events = []
        if rows:
            header = [c.lower() for c in rows[0]]
            for r in rows[1:]:
                row = dict(zip(header, r))
                events.append({
                    "year": row.get("year", ""),
                    "title": row.get("title", ""),
                    "body": row.get("body", ""),
                })
        if events:
            s["events"] = events
        cb = _find_block(blocks, "callout")
        if cb:
            s["callout"] = {"title": cb[1].get("title", ""), "bullets": _bullets(cb[2])}
    elif stype == "process":
        s["title"] = h2 or ""
        if h3:
            s["subtitle"] = h3
        steps = []
        for n, item in enumerate(_ordered(loose), start=1):
            m = re.match(r"^\*\*(.+?)\*\*\s*[—-]\s*(.*)$", item)
            if m:
                steps.append({"number": n, "title": m.group(1).strip(),
                              "body": Literal(m.group(2).strip())})
            else:
                steps.append({"number": n, "title": item, "body": ""})
        if steps:
            s["steps"] = steps
        if "footer" in attrs:
            s["footer"] = attrs["footer"]
    elif stype == "table":
        s["title"] = h2 or ""
        if h3:
            s["subtitle"] = h3
        rows = _table(loose)
        if rows:
            s["headers"] = rows[0]
            s["rows"] = rows[1:]
    elif stype == "callout":
        s["style"] = attrs.get("style", "tip")
        s["title"] = h2 or ""
        items = _ordered(loose) or _bullets(loose)
        if not items:
            p = _paragraph(loose)
            items = [p] if p else []
        s["body"] = Literal("\n".join(items))
    elif stype == "demo":
        s["subtitle"] = h2 or h3 or _paragraph(loose) or ""
    elif stype == "screenshot":
        if "screenshot" in attrs:
            s["screenshot"] = attrs["screenshot"]
        if "image" in attrs:
            s["image"] = attrs["image"]
        if h2:
            s["title"] = h2
        if h3:
            s["subtitle"] = h3
        desc = _paragraph(loose)
        if desc:
            s["description"] = desc
    elif stype == "video_demo":
        s["title"] = h2 or ""
        desc = _paragraph(loose)
        if desc:
            s["description"] = desc
        if "duration" in attrs:
            s["duration"] = attrs["duration"]
    else:
        raise CompileError(f"unknown slide type '{stype}' (slide #{idx})")

    return _attach_common(s, blocks)


# ---- top-level compile -----------------------------------------------------
def compile_text(text):
    fm, body = split_frontmatter(text)
    meta = {}
    for k in ("book", "chapter", "title", "subtitle"):
        if fm.get(k) is not None:
            meta[k] = fm[k]
    if "chapter" not in meta:
        raise CompileError("front-matter must define 'chapter'")

    slides = []
    for idx, chunk in enumerate(split_slides(body), start=1):
        # directive must be the first non-empty line
        first = next((l for l in chunk if l.strip()), "")
        parsed = parse_directive(first)
        if not parsed:
            raise CompileError(f"slide #{idx}: missing '<!-- slide: TYPE -->' directive")
        stype, attrs = parsed
        rest = chunk[chunk.index(first) + 1:]
        loose, blocks = split_blocks(rest)
        slide = build_slide(stype, attrs, loose, blocks, idx)
        if "notes" not in slide:
            raise CompileError(f"slide #{idx} ({stype}): missing '::: notes' block")
        slides.append(slide)

    if not slides:
        raise CompileError("no slides found")
    return {"meta": meta, "slides": slides}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compile .slides.md -> chNN.yaml")
    ap.add_argument("input", help="path to CH.slides.md")
    ap.add_argument("-o", "--output", help="output yaml (default: replace .slides.md with .yaml)")
    ap.add_argument("--check", action="store_true", help="validate only, do not write")
    args = ap.parse_args(argv)

    with open(args.input, encoding="utf-8") as f:
        text = f.read()
    try:
        data = compile_text(text)
    except CompileError as e:
        sys.stderr.write(f"[slides_md2yaml] {args.input}: {e}\n")
        return 1

    out_yaml = yaml.dump(data, allow_unicode=True, sort_keys=False, width=100)
    if args.check:
        sys.stderr.write(f"[slides_md2yaml] OK: {len(data['slides'])} slides parse cleanly\n")
        return 0
    out_path = args.output or re.sub(r"\.slides\.md$", ".yaml", args.input)
    if out_path == args.input:
        out_path = args.input + ".yaml"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_yaml)
    sys.stderr.write(f"[slides_md2yaml] wrote {out_path} ({len(data['slides'])} slides)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
