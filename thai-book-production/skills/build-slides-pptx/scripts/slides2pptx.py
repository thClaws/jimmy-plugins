#!/usr/bin/env python3
"""slides2pptx.py — standalone renderer: chNN.yaml -> chNN.pptx (python-pptx).

Self-contained: the default "Agentic Press" theme lives in this file (palette, fonts,
sizes, per-type layouts). No external Chapter-Template.pptx required.

Custom theme hook (designed now, usable now):
  --theme theme.json            deep-merges over the default theme
  book.yaml -> style.pptx_theme  (inline dict OR a path to a JSON theme) also merged

Usage:
  python3 slides2pptx.py chNN.yaml [-o chNN.pptx] [--book book.yaml] [--theme t.json]
                                   [--media-dir media]
Requires: python-pptx, pyyaml. Thai renders correctly if Prompt + Sarabun fonts are
installed (bundled in ../assets/fonts).
"""
import sys, os, json, argparse

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML required: pip install pyyaml --break-system-packages\n"); sys.exit(2)
try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.oxml.ns import qn
except ImportError:
    sys.stderr.write("python-pptx required: pip install python-pptx --break-system-packages\n"); sys.exit(2)


# ----------------------------------------------------------------------------- theme
DEFAULT_THEME = {
    "palette": {
        "bg_dark": "0D1B2A", "bg_darkest": "08131F", "parchment": "F8F6F0",
        "card": "FFFFFF", "teal": "007A6E", "teal_soft": "DCEAE8", "gold": "B8860B",
        "navy": "16324F", "dark_text": "0D1B2A", "body_text": "2A3848",
        "gray_text": "5A6A7E", "white": "FFFFFF", "red": "CC3333", "line": "E3DFD5",
    },
    "fonts": {"heading": "Prompt", "body": "Sarabun"},
    "sizes": {
        "cover_title": 46, "cover_sub": 22, "cover_label": 16,
        "title": 32, "subtitle": 17, "body": 18, "card_title": 17, "card_body": 12.5,
        "badge": 13, "quote": 30, "demo": 72, "footer": 13, "table": 14, "num": 26,
    },
}


def deep_merge(base, over):
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            deep_merge(base[k], v)
        else:
            base[k] = v
    return base


# ----------------------------------------------------------------------------- helpers
def C(h):
    return RGBColor.from_string(h)


class Deck:
    def __init__(self, theme, media_dirs):
        self.t = theme
        self.pal = theme["palette"]
        self.hf = theme["fonts"]["heading"]
        self.bf = theme["fonts"]["body"]
        self.sz = theme["sizes"]
        self.media_dirs = media_dirs
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)
        self.prs.slide_height = Inches(7.5)
        self.W = self.prs.slide_width
        self.H = self.prs.slide_height
        self.M = Inches(0.72)

    def blank(self):
        return self.prs.slides.add_slide(self.prs.slide_layouts[6])

    def _set_font(self, run, name, size, color, bold=False):
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = C(color)
        run.font.name = name
        rPr = run._r.get_or_add_rPr()
        for tag in ("a:latin", "a:ea", "a:cs"):
            el = rPr.find(qn(tag))
            if el is None:
                el = rPr.makeelement(qn(tag), {})
                rPr.append(el)
            el.set("typeface", name)

    def rect(self, slide, l, t, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE,
             line_w=None, shadow=False):
        sp = slide.shapes.add_shape(shape, l, t, w, h)
        if fill is None:
            sp.fill.background()
        else:
            sp.fill.solid(); sp.fill.fore_color.rgb = C(fill)
        if line is None:
            sp.line.fill.background()
        else:
            sp.line.color.rgb = C(line)
            sp.line.width = line_w or Pt(1)
        sp.shadow.inherit = shadow
        return sp

    def bg(self, slide, color):
        sp = self.rect(slide, 0, 0, self.W, self.H, fill=color)
        el = sp._element
        el.getparent().remove(el)
        slide.shapes._spTree.insert(2, el)
        return sp

    def text(self, slide, l, t, w, h, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             wrap=True):
        """lines: list of dicts {text,size,color,font,bold,align,space_after,space_before,bullet}"""
        tb = slide.shapes.add_textbox(l, t, w, h)
        tf = tb.text_frame
        tf.word_wrap = wrap
        tf.vertical_anchor = anchor
        tf.margin_left = Pt(4); tf.margin_right = Pt(4)
        tf.margin_top = Pt(2); tf.margin_bottom = Pt(2)
        for i, ln in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = ln.get("align", align)
            if "space_after" in ln:
                p.space_after = Pt(ln["space_after"])
            if "space_before" in ln:
                p.space_before = Pt(ln["space_before"])
            prefix = ln.get("bullet", "")
            run = p.add_run()
            run.text = prefix + str(ln["text"])
            self._set_font(run, ln.get("font", self.bf), ln["size"],
                           ln.get("color", self.pal["body_text"]), ln.get("bold", False))
        return tb

    # ----- image resolution
    def find_image(self, name):
        if not name:
            return None
        if os.path.isabs(name) and os.path.exists(name):
            return name
        for d in self.media_dirs:
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
        return None

    # ------------------------------------------------------------------- slide types
    def render(self, s):
        t = s.get("type", "content")
        fn = getattr(self, f"_s_{t}", None)
        slide = self.blank()
        if fn is None:
            self._s_content(slide, s)
        else:
            fn(slide, s)
        notes = s.get("notes")
        if notes:
            slide.notes_slide.notes_text_frame.text = str(notes)

    def _title_block(self, slide, s, color=None):
        color = color or self.pal["dark_text"]
        lines = []
        title = s.get("title", "")
        tsize = self.sz["title"] if len(str(title)) <= 42 else self.sz["title"] - 6
        lines.append({"text": title, "size": tsize, "color": color, "font": self.hf, "bold": True,
                      "space_after": 2})
        if s.get("subtitle"):
            lines.append({"text": s["subtitle"], "size": self.sz["subtitle"],
                          "color": self.pal["gray_text"], "font": self.bf})
        self.text(slide, self.M, Inches(0.5), self.W - 2 * self.M, Inches(1.4), lines)
        # teal accent underline
        self.rect(slide, self.M, Inches(1.55), Inches(0.9), Pt(4), fill=self.pal["teal"])

    def _s_cover(self, slide, s):
        self.bg(slide, self.pal["bg_dark"])
        cx = self.M
        cw = self.W - 2 * self.M
        if s.get("chapter"):
            self.text(slide, cx, Inches(2.35), cw, Inches(0.5),
                      [{"text": s["chapter"], "size": self.sz["cover_label"], "color": self.pal["teal"],
                        "font": self.hf, "bold": True, "align": PP_ALIGN.CENTER}], align=PP_ALIGN.CENTER)
        self.text(slide, cx, Inches(2.9), cw, Inches(1.6),
                  [{"text": s.get("title", ""), "size": self.sz["cover_title"], "color": self.pal["white"],
                    "font": self.hf, "bold": True, "align": PP_ALIGN.CENTER}],
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        # gold divider
        self.rect(slide, Inches(13.333 / 2 - 0.6), Inches(4.55), Inches(1.2), Pt(3), fill=self.pal["gold"])
        if s.get("subtitle"):
            self.text(slide, cx, Inches(4.75), cw, Inches(0.7),
                      [{"text": s["subtitle"], "size": self.sz["cover_sub"], "color": self.pal["gold"],
                        "font": self.bf, "align": PP_ALIGN.CENTER}], align=PP_ALIGN.CENTER)

    def _s_quote(self, slide, s):
        self.bg(slide, self.pal["bg_dark"])
        self.text(slide, Inches(1.4), Inches(2.2), self.W - Inches(2.8), Inches(2.4),
                  [{"text": "“" + s.get("text", "") + "”", "size": self.sz["quote"],
                    "color": self.pal["white"], "font": self.hf, "align": PP_ALIGN.CENTER}],
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if s.get("attribution"):
            self.text(slide, Inches(1.4), Inches(4.8), self.W - Inches(2.8), Inches(0.6),
                      [{"text": s["attribution"], "size": self.sz["cover_sub"], "color": self.pal["gold"],
                        "font": self.bf, "align": PP_ALIGN.CENTER}], align=PP_ALIGN.CENTER)

    def _s_content(self, slide, s):
        self.bg(slide, self.pal["parchment"])
        self._title_block(slide, s)
        bullets = s.get("bullets", []) or []
        numbered = s.get("numbered", False)
        lines = []
        for i, b in enumerate(bullets[:6]):
            pre = f"{i+1}.  " if numbered else "●  "
            lines.append({"text": b, "size": self.sz["body"], "color": self.pal["body_text"],
                          "font": self.bf, "bullet": pre, "space_after": 10})
        self.text(slide, self.M, Inches(2.0), self.W - 2 * self.M, Inches(5.0), lines,
                  anchor=MSO_ANCHOR.TOP)

    def _s_section(self, slide, s):
        self.bg(slide, self.pal["parchment"])
        head = []
        title = str(s.get("title", ""))
        num = str(s.get("number") or "")
        # If the title already embeds its number (e.g. "1.1 — Foo" with number
        # "1.1"), leave the title as-is and skip the separate number run so it
        # isn't shown twice. Token boundary so number "1" never eats "12 Monkeys".
        embeds = num and title.startswith(num) and (title[len(num):] == "" or title[len(num)] in " .:)-–—·\t")
        if num and not embeds:
            head.append({"text": num, "size": self.sz["subtitle"], "color": self.pal["teal"],
                         "font": self.hf, "bold": True, "space_after": 0})
        head.append({"text": title, "size": self.sz["title"], "color": self.pal["dark_text"],
                     "font": self.hf, "bold": True, "space_after": 2})
        if s.get("subtitle"):
            head.append({"text": s["subtitle"], "size": self.sz["subtitle"], "color": self.pal["gray_text"],
                         "font": self.bf})
        self.text(slide, self.M, Inches(0.5), self.W - 2 * self.M, Inches(1.6), head)
        cards = (s.get("cards") or [])[:5]
        n = max(1, len(cards))
        gap = Inches(0.3)
        total = self.W - 2 * self.M
        cw = int((total - gap * (n - 1)) / n)
        top = Inches(2.35); ch = Inches(4.3)
        for i, card in enumerate(cards):
            l = int(self.M + i * (cw + gap))
            self.rect(slide, l, top, cw, ch, fill=self.pal["card"], line=self.pal["line"],
                      shape=MSO_SHAPE.ROUNDED_RECTANGLE, shadow=True)
            self.rect(slide, l, top, cw, Pt(6), fill=self.pal["teal"])  # top accent
            lines = []
            if card.get("label"):
                lines.append({"text": card["label"], "size": self.sz["badge"], "color": self.pal["teal"],
                              "font": self.hf, "bold": True, "space_after": 4})
            lines.append({"text": card.get("title", ""), "size": self.sz["card_title"],
                          "color": self.pal["dark_text"], "font": self.hf, "bold": True, "space_after": 4})
            if card.get("body"):
                lines.append({"text": card["body"], "size": self.sz["card_body"],
                              "color": self.pal["body_text"], "font": self.bf})
            self.text(slide, l + Inches(0.18), top + Inches(0.28), cw - Inches(0.36), ch - Inches(0.5), lines)

    def _panel(self, slide, l, t, w, h, header, bullets, header_bg):
        self.rect(slide, l, t, w, h, fill=self.pal["card"], line=self.pal["line"],
                  shape=MSO_SHAPE.ROUNDED_RECTANGLE, shadow=True)
        self.rect(slide, l, t, w, Inches(0.62), fill=header_bg, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        self.text(slide, l + Inches(0.2), t, w - Inches(0.4), Inches(0.62),
                  [{"text": header, "size": self.sz["subtitle"], "color": self.pal["white"],
                    "font": self.hf, "bold": True}], anchor=MSO_ANCHOR.MIDDLE)
        lines = [{"text": b, "size": self.sz["card_title"], "color": self.pal["body_text"],
                  "font": self.bf, "bullet": "●  ", "space_after": 8} for b in (bullets or [])[:6]]
        self.text(slide, l + Inches(0.24), t + Inches(0.85), w - Inches(0.48), h - Inches(1.05), lines)

    def _s_two_column(self, slide, s):
        self.bg(slide, self.pal["parchment"])
        self._title_block(slide, s)
        gap = Inches(0.4)
        w = int((self.W - 2 * self.M - gap) / 2)
        top = Inches(2.05); h = Inches(4.75)
        left = s.get("left", {}) or {}
        right = s.get("right", {}) or {}
        self._panel(slide, self.M, top, w, h, left.get("header", ""), left.get("bullets", []),
                    self.pal["navy"])
        self._panel(slide, int(self.M + w + gap), top, w, h, right.get("header", ""),
                    right.get("bullets", []), self.pal["teal"])

    def _s_table(self, slide, s):
        self.bg(slide, self.pal["parchment"])
        self._title_block(slide, s)
        headers = s.get("headers", []) or []
        rows = (s.get("rows", []) or [])[:8]
        ncol = max(1, len(headers))
        nrow = len(rows) + 1
        gtbl = slide.shapes.add_table(nrow, ncol, self.M, Inches(2.05),
                                      self.W - 2 * self.M, Inches(0.55) * min(nrow, 9))
        tbl = gtbl.table
        for j, htext in enumerate(headers):
            cell = tbl.cell(0, j)
            cell.fill.solid(); cell.fill.fore_color.rgb = C(self.pal["navy"])
            self._cell_text(cell, htext, self.pal["white"], bold=True)
        for i, row in enumerate(rows):
            for j in range(ncol):
                cell = tbl.cell(i + 1, j)
                cell.fill.solid()
                cell.fill.fore_color.rgb = C(self.pal["teal_soft"] if i % 2 else self.pal["card"])
                val = row[j] if j < len(row) else ""
                self._cell_text(cell, val, self.pal["body_text"])

    def _cell_text(self, cell, text, color, bold=False):
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]
        run = p.add_run(); run.text = str(text)
        self._set_font(run, self.bf, self.sz["table"], color, bold)
        cell.margin_left = Inches(0.12); cell.margin_right = Inches(0.12)
        cell.margin_top = Inches(0.04); cell.margin_bottom = Inches(0.04)

    def _s_callout(self, slide, s):
        self.bg(slide, self.pal["parchment"])
        style = s.get("style", "tip")
        accent = {"tip": self.pal["gold"], "warning": self.pal["red"], "concept": self.pal["teal"]}.get(style, self.pal["gold"])
        icon = {"tip": "✦", "warning": "▲", "concept": "◆"}.get(style, "✦")
        box_l, box_t = self.M, Inches(1.4)
        box_w, box_h = self.W - 2 * self.M, Inches(4.6)
        self.rect(slide, box_l, box_t, box_w, box_h, fill=self.pal["card"], line=self.pal["line"],
                  shape=MSO_SHAPE.ROUNDED_RECTANGLE, shadow=True)
        self.rect(slide, box_l, box_t, Inches(0.14), box_h, fill=accent)  # accent bar
        self.text(slide, box_l + Inches(0.45), box_t + Inches(0.3), box_w - Inches(0.9), Inches(0.7),
                  [{"text": f"{icon}  {s.get('title','')}", "size": self.sz["title"] - 4,
                    "color": accent, "font": self.hf, "bold": True}])
        body = s.get("body", "")
        items = [x for x in str(body).split("\n") if x.strip()]
        lines = [{"text": it, "size": self.sz["body"], "color": self.pal["body_text"], "font": self.bf,
                  "bullet": f"{i+1}.  ", "space_after": 8} for i, it in enumerate(items[:6])]
        self.text(slide, box_l + Inches(0.45), box_t + Inches(1.2), box_w - Inches(0.9), box_h - Inches(1.5), lines)

    def _s_demo(self, slide, s):
        self.bg(slide, self.pal["bg_darkest"])
        self.text(slide, self.M, Inches(2.2), self.W - 2 * self.M, Inches(1.6),
                  [{"text": "DEMO", "size": self.sz["demo"], "color": self.pal["teal"], "font": self.hf,
                    "bold": True, "align": PP_ALIGN.CENTER}], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if s.get("subtitle"):
            self.text(slide, self.M, Inches(4.2), self.W - 2 * self.M, Inches(0.8),
                      [{"text": s["subtitle"], "size": self.sz["cover_sub"], "color": self.pal["white"],
                        "font": self.bf, "align": PP_ALIGN.CENTER}], align=PP_ALIGN.CENTER)

    def _s_video_demo(self, slide, s):
        self.bg(slide, self.pal["bg_dark"])
        self.rect(slide, Inches(13.333 / 2 - 0.5), Inches(2.3), Inches(1.0), Inches(1.0),
                  fill=self.pal["teal"], shape=MSO_SHAPE.ISOSCELES_TRIANGLE).rotation = 90
        self.text(slide, self.M, Inches(3.6), self.W - 2 * self.M, Inches(1.0),
                  [{"text": s.get("title", ""), "size": self.sz["title"], "color": self.pal["white"],
                    "font": self.hf, "bold": True, "align": PP_ALIGN.CENTER}], align=PP_ALIGN.CENTER)
        if s.get("description"):
            self.text(slide, self.M, Inches(4.6), self.W - 2 * self.M, Inches(0.8),
                      [{"text": s["description"], "size": self.sz["subtitle"], "color": self.pal["gray_text"],
                        "font": self.bf, "align": PP_ALIGN.CENTER}], align=PP_ALIGN.CENTER)
        if s.get("duration"):
            self.text(slide, self.M, Inches(5.3), self.W - 2 * self.M, Inches(0.5),
                      [{"text": "●  " + str(s["duration"]), "size": self.sz["badge"],
                        "color": self.pal["teal"], "font": self.bf, "align": PP_ALIGN.CENTER}], align=PP_ALIGN.CENTER)

    def _s_screenshot(self, slide, s):
        self.bg(slide, self.pal["parchment"])
        if s.get("title") or s.get("subtitle"):
            self._title_block(slide, s)
            top = Inches(2.0)
        else:
            top = Inches(0.6)
        img = self.find_image(s.get("screenshot") or s.get("image"))
        area_l, area_w = self.M, self.W - 2 * self.M
        area_h = self.H - top - Inches(0.5)
        if img:
            try:
                from PIL import Image
                iw, ih = Image.open(img).size
            except Exception:
                iw, ih = 16, 9
            ratio = iw / ih
            aw, ah = area_w, int(area_w / ratio)
            if ah > area_h:
                ah, aw = area_h, int(area_h * ratio)
            l = int(area_l + (area_w - aw) / 2)
            self.rect(slide, l - Pt(3), top - Pt(3), aw + Pt(6), ah + Pt(6), fill=self.pal["card"],
                      line=self.pal["line"], shadow=True)
            slide.shapes.add_picture(img, l, top, aw, ah)
        else:
            self.rect(slide, area_l, top, area_w, area_h, fill=self.pal["teal_soft"],
                      line=self.pal["teal"], shape=MSO_SHAPE.ROUNDED_RECTANGLE)
            self.text(slide, area_l, top, area_w, area_h,
                      [{"text": s.get("description") or "[ screenshot ]", "size": self.sz["subtitle"],
                        "color": self.pal["teal"], "font": self.bf, "align": PP_ALIGN.CENTER}],
                      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    def _s_timeline(self, slide, s):
        self.bg(slide, self.pal["parchment"])
        self._title_block(slide, s)
        events = (s.get("events") or [])[:5]
        top = Inches(2.15); row_h = Inches(0.92)
        line_x = self.M + Inches(0.35)
        if events:
            self.rect(slide, line_x, top, Pt(2.5), int(row_h * len(events)), fill=self.pal["teal_soft"])
        for i, ev in enumerate(events):
            ct = int(top + i * row_h)
            self.rect(slide, self.M, ct, Inches(0.7), Inches(0.7), fill=self.pal["teal"],
                      shape=MSO_SHAPE.OVAL)
            self.text(slide, self.M, ct, Inches(0.7), Inches(0.7),
                      [{"text": ev.get("year", ""), "size": 11, "color": self.pal["white"],
                        "font": self.hf, "bold": True, "align": PP_ALIGN.CENTER}],
                      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            lines = [{"text": ev.get("title", ""), "size": self.sz["card_title"], "color": self.pal["dark_text"],
                      "font": self.hf, "bold": True, "space_after": 1}]
            if ev.get("body"):
                lines.append({"text": ev["body"], "size": self.sz["card_body"] + 1,
                              "color": self.pal["gray_text"], "font": self.bf})
            self.text(slide, self.M + Inches(1.0), ct, self.W - self.M - Inches(1.7), row_h, lines,
                      anchor=MSO_ANCHOR.MIDDLE)

    def _s_process(self, slide, s):
        self.bg(slide, self.pal["parchment"])
        self._title_block(slide, s)
        steps = (s.get("steps") or [])[:6]
        cols = 2
        gap = Inches(0.4)
        cw = int((self.W - 2 * self.M - gap) / cols)
        ch = Inches(1.35)
        top = Inches(2.05)
        for i, st in enumerate(steps):
            r, c = divmod(i, cols)
            l = int(self.M + c * (cw + gap))
            t = int(top + r * (ch + Inches(0.2)))
            self.rect(slide, l, t, cw, ch, fill=self.pal["card"], line=self.pal["line"],
                      shape=MSO_SHAPE.ROUNDED_RECTANGLE, shadow=True)
            self.rect(slide, l + Inches(0.18), t + Inches(0.28), Inches(0.62), Inches(0.62),
                      fill=self.pal["teal"], shape=MSO_SHAPE.OVAL)
            self.text(slide, l + Inches(0.18), t + Inches(0.28), Inches(0.62), Inches(0.62),
                      [{"text": str(st.get("number", i + 1)), "size": 18, "color": self.pal["white"],
                        "font": self.hf, "bold": True, "align": PP_ALIGN.CENTER}],
                      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            lines = [{"text": st.get("title", ""), "size": self.sz["card_title"], "color": self.pal["dark_text"],
                      "font": self.hf, "bold": True, "space_after": 1}]
            if st.get("body"):
                lines.append({"text": st["body"], "size": self.sz["card_body"] + 1,
                              "color": self.pal["gray_text"], "font": self.bf})
            self.text(slide, l + Inches(0.95), t + Inches(0.2), cw - Inches(1.1), ch - Inches(0.35), lines,
                      anchor=MSO_ANCHOR.MIDDLE)
        if s.get("footer"):
            self.text(slide, self.M, Inches(6.9), self.W - 2 * self.M, Inches(0.4),
                      [{"text": s["footer"], "size": self.sz["footer"], "color": self.pal["gray_text"],
                        "font": self.bf, "align": PP_ALIGN.CENTER}], align=PP_ALIGN.CENTER)


def load_theme(book_path, theme_path):
    theme = json.loads(json.dumps(DEFAULT_THEME))  # deep copy
    if book_path and os.path.exists(book_path):
        try:
            by = yaml.safe_load(open(book_path, encoding="utf-8")) or {}
            pt = (by.get("style") or {}).get("pptx_theme")
            if isinstance(pt, str) and os.path.exists(pt):
                pt = json.load(open(pt, encoding="utf-8"))
            if isinstance(pt, dict):
                deep_merge(theme, pt)
        except Exception as e:
            sys.stderr.write(f"[slides2pptx] warning: could not read book.yaml theme: {e}\n")
    if theme_path:
        deep_merge(theme, json.load(open(theme_path, encoding="utf-8")))
    return theme


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render chNN.yaml -> chNN.pptx (standalone)")
    ap.add_argument("input", help="path to chNN.yaml")
    ap.add_argument("-o", "--output", help="output .pptx (default: replace .yaml with .pptx)")
    ap.add_argument("--book", help="book.yaml (for style.pptx_theme + media dirs)")
    ap.add_argument("--theme", help="theme.json to deep-merge over the default")
    ap.add_argument("--media-dir", action="append", default=[],
                    help="dir(s) to resolve screenshot/image filenames (repeatable)")
    args = ap.parse_args(argv)

    data = yaml.safe_load(open(args.input, encoding="utf-8"))
    if not data or "slides" not in data:
        sys.stderr.write("[slides2pptx] input has no 'slides'\n"); return 1
    theme = load_theme(args.book, args.theme)

    media_dirs = list(args.media_dir)
    base = os.path.dirname(os.path.abspath(args.input))
    for rel in ("media/screenshots", "media/generated", "../screenshots", "../generated"):
        media_dirs.append(os.path.normpath(os.path.join(base, "..", "..", rel)))
    media_dirs = [d for d in media_dirs if os.path.isdir(d)]

    deck = Deck(theme, media_dirs)
    for s in data["slides"]:
        deck.render(s)

    out = args.output or (args.input[:-5] + ".pptx" if args.input.endswith(".yaml") else args.input + ".pptx")
    deck.prs.save(out)
    sys.stderr.write(f"[slides2pptx] wrote {out} ({len(data['slides'])} slides)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
