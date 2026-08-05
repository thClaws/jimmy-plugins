#!/usr/bin/env python3
"""
manage-previews.py — จัดการ `<!-- gen-preview:<id> -->` blocks ใน chapter markdown

    python3 manage-previews.py insert   <chapter.md> [more.md ...]
    python3 manage-previews.py strip    <chapter.md> [more.md ...]
    python3 manage-previews.py validate <chapter.md> [more.md ...]
    python3 manage-previews.py repair   <chapter.md> [more.md ...]

insert    แทรก/แทนที่ preview ให้ทุก `{{image:id|caption}}` (idempotent — รันซ้ำได้)
strip     ลบ preview ทั้งหมด (ใช้ก่อน resolve placeholder ใน build-epub-pdf)
validate  ตรวจ placeholder↔preview + ความเสียหายเชิงกลทุกชั้น (ดู Deep checks ข้างล่าง)
          exit 1 เมื่อพบปัญหา — ใช้เป็น gate ก่อน "สรุปงาน/commit" ทุกครั้ง
repair    ลบของเสียเชิงกลที่เกิดจากบั๊กแทรก preview (self-heal — deterministic, ตรวจดู
          output ได้) แล้วรัน validate ซ้ำให้ — ปลอดภัยต่อไฟล์ที่สะอาด (no-op)

การป้องกัน 3 ชั้น (กันบั๊ก "extensive destruction" ซ้ำรอบ 3):
  Layer 1 — ป้องกัน: ห้ามแทรก/แก้ preview ด้วยมือหรือ line-based — ใช้ insert เสมอ
  Layer 2 — ซ่อมเอง: repair ลบของเสียที่เกิดแล้ว (raw image, fragment tail,
            heading/paragraph ซ้ำ) — deterministic, ไม่แตะของกำกวม
  Layer 3 — ตรวจจับ: validate จับทุกชั้นของความเสียหาย + เช็ค placeholder พัง/orphan/ซ้ำ
            (รันก่อนสรุปงานทุกครั้ง — exit != 0 = ยังไม่เสร็จ)

Deep checks (validate): raw `![...]` ที่ไม่มี gen-preview นำหน้า, image path ซ้ำ,
  syntax `](]`/`]]` พัง, heading (H2/H3) ซ้ำ, ย่อหน้า (>40 ตัวอักษร) ซ้ำกันทุกตัวอักษร,
  placeholder พัง/ไม่มี preview (เมื่อไฟล์ภาพมีอยู่แล้ว)/orphan/ซ้ำ

options
    --rel PATH   path ของ generated images เทียบกับไฟล์บท (default ../media/generated)
    --ext EXT    นามสกุลไฟล์ภาพ (default .png)

exit 1 เมื่อพบปัญหา — placeholder caption ยาวข้ามบรรทัดรองรับเต็มรูปแบบ
"""

import argparse
import os
import re
import sys

# caption ห้ามคร่อม `}}` / `{{` / บรรทัดว่าง — กัน placeholder ที่ปิดไม่ครบ
# ไม่ให้กลืนตัวบททั้งย่อหน้าเข้าไปเป็น caption
PLACEHOLDER_RE = re.compile(
    r'\{\{image:([a-z0-9][a-z0-9._-]*)\|((?:(?!\}\}|\{\{|\n[ \t]*\n).)*?)\}\}', re.S)
OPEN_RE = re.compile(r'\{\{image:([a-z0-9][a-z0-9._-]*)\|')
PREVIEW_COMMENT_RE = re.compile(r'^\s*<!--\s*gen-preview:([a-z0-9][a-z0-9._-]*)\s*-->\s*$')

MAX_IMAGE_LINES = 10  # ขอบเขตกันหลงลบ ถ้า `![...]` ที่ตามมาไม่มี `)` ปิด


def _read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def _write(path, text):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def _alt(caption):
    """caption หลายบรรทัด → alt text บรรทัดเดียวที่ปลอดภัยใน markdown"""
    alt = ' '.join(caption.split())
    return alt.replace('\\', r'\\').replace('[', r'\[').replace(']', r'\]')


def _broken_placeholders(text):
    """id ของ placeholder ที่เปิด `{{image:` แล้วไม่มี `}}` ปิดในบรรทัด/ย่อหน้าเดียวกัน"""
    ok = {m.start() for m in PLACEHOLDER_RE.finditer(text)}
    return [m.group(1) for m in OPEN_RE.finditer(text) if m.start() not in ok]


def _strip_previews(lines):
    """ลบ comment marker + บล็อก `![...](...)` ที่ตามมา คืน (lines, จำนวนบล็อกที่ลบ)"""
    out, removed, i = [], 0, 0
    while i < len(lines):
        if PREVIEW_COMMENT_RE.match(lines[i]):
            removed += 1
            i += 1
            if i < len(lines) and lines[i].lstrip().startswith('!['):
                j, limit = i, min(len(lines), i + MAX_IMAGE_LINES)
                while j < limit and not ('../media/generated/' in lines[j] and lines[j].rstrip().endswith(')')):
                    j += 1
                i = j + 1 if j < limit else i  # ไม่เจอ `)` → ลบแค่ comment
            # เก็บกวาดบรรทัดว่างที่บล็อกทิ้งไว้ (ก่อนหน้าว่าง + หลังว่าง)
            if (out and not out[-1].strip()
                    and i < len(lines) and not lines[i].strip()):
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return out, removed


def _preview_ids(text):
    return [m.group(1) for line in text.split('\n')
            for m in [PREVIEW_COMMENT_RE.match(line)] if m]


def _line_end(text, pos):
    """ตำแหน่งท้ายบรรทัดที่ pos อยู่ (ก่อน `\\n`) — แทรก preview หลังจากนี้"""
    nl = text.find('\n', pos)
    return len(text) if nl == -1 else nl


def insert(path, rel, ext):
    text = _read(path)
    broken = _broken_placeholders(text)
    if broken:
        return {'broken': broken}

    text = '\n'.join(_strip_previews(text.split('\n'))[0])

    parts, last, seen = [], 0, set()
    for m in PLACEHOLDER_RE.finditer(text):
        pid, cap = m.group(1), m.group(2)
        if pid in seen:
            continue
        seen.add(pid)
        cut = _line_end(text, m.end())
        parts.append(text[last:cut])
        parts.append(f'\n<!-- gen-preview:{pid} -->\n'
                     f'![{_alt(cap)}]({rel.rstrip("/")}/{pid}{ext})')
        last = cut
    parts.append(text[last:])
    result = ''.join(parts)
    _write(path, result)
    return {'placeholders': len(set(p for p, _ in PLACEHOLDER_RE.findall(text))),
            'previews': len(_preview_ids(result))}


def strip(path):
    lines, removed = _strip_previews(_read(path).split('\n'))
    _write(path, '\n'.join(lines))
    return removed


def validate(path, rel, ext):
    text = _read(path)
    problems, pending = [], []

    for pid in _broken_placeholders(text):
        problems.append(f'placeholder {pid} ไม่มี }}}} ปิด (พัง)')

    ph_ids = [pid for pid, _ in PLACEHOLDER_RE.findall(text)]
    prev_ids = _preview_ids(text)

    base = os.path.dirname(os.path.abspath(path))
    for pid in sorted(set(ph_ids) - set(prev_ids)):
        # ยังไม่ได้ gen → ไม่ใช่ปัญหา; มีไฟล์แล้วแต่ไม่มี preview → ปัญหา
        if os.path.isfile(os.path.join(base, rel, pid + ext)):
            problems.append(f'placeholder {pid} ไม่มี preview')
        else:
            pending.append(pid)
    for pid in sorted(set(prev_ids) - set(ph_ids)):
        problems.append(f'orphan preview {pid} (ไม่มี placeholder)')
    for pid in sorted(set(p for p in prev_ids if prev_ids.count(p) > 1)):
        problems.append(f'preview {pid} ซ้ำ {prev_ids.count(pid)} ชุด')

    # preview ที่ถูกแทรกกลาง placeholder — อาการของบั๊กเดิม
    for m in PLACEHOLDER_RE.finditer(text):
        if 'gen-preview:' in m.group(2) or '![' in m.group(2):
            problems.append(f'placeholder {m.group(1)} มี preview แทรกอยู่ข้างใน (พัง)')

    # deep checks — ความเสียหายเชิงกล (รอบ 2: raw image, path ซ้ำ, syntax, heading/paragraph ซ้ำ)
    for ln, msg in _deep_problems(text.split('\n')):
        problems.append(f'L{ln}: {msg}')

    return problems, pending


def _media_line_idxs(lines):
    """index ของบรรทัดที่อยู่ใน {{image:...}} placeholder หรือ ![..](..) image block —
    caption ของทั้งสอง mirror กันโดย design → ต้อง exclude ออกจาก dup checks"""
    idx = set()
    for i, l in enumerate(lines):
        if '{{image:' in l:
            j = i
            while j < len(lines) and '}}' not in lines[j]:
                idx.add(j)
                j += 1
            if j < len(lines):
                idx.add(j)
        if l.lstrip().startswith('!['):
            j = i
            while j < len(lines) and ')' not in lines[j]:
                idx.add(j)
                j += 1
            if j < len(lines):
                idx.add(j)
    return idx



def _comment_image_ok(lines, rel='../media/generated', ext='.png'):
    """ทุก gen-preview comment ต้องมีบล็อกภาพตามจริง (path ตรง pid) ภายใน MAX_IMAGE_LINES
    คืน list ของ comment id ที่ไม่มีภาพ"""
    missing = []
    for i, l in enumerate(lines):
        m = PREVIEW_COMMENT_RE.match(l)
        if m:
            pid = m.group(1)
            j = i + 1
            found = False
            while j < min(len(lines), i + MAX_IMAGE_LINES + 1):
                if lines[j].lstrip().startswith('!['):
                    k = j
                    while k < len(lines) and not ('../media/generated/' in lines[k]
                                                  and lines[k].rstrip().endswith(')')):
                        k += 1
                    if k < len(lines) and f'/{pid}{ext}' in lines[k]:
                        found = True
                    break
                j += 1
            if not found:
                missing.append((i + 1, f'comment {pid} ไม่มีภาพตามจริง'))
    return missing


def _deep_problems(lines):
    """ความเสียหายเชิงกลจากบั๊กแทรก preview — validate รอบ 2 (ครอบคลุมของที่รอบ 1 พลาด)
    คืน list ของ (line_no, message)"""
    problems = []
    media_idx = _media_line_idxs(lines)

    # 0. ทุก comment ต้องมีภาพตามจริง (กันบั๊ก "ภาพถูกกินโดยไม่รู้ตัว")
    for ln0, msg in _comment_image_ok(lines):
        problems.append((ln0, msg))

    # 1. raw `![...]` ที่ไม่ได้อยู่ถัดจาก gen-preview comment — orphan/ของซ้ำ
    for i, l in enumerate(lines):
        if l.lstrip().startswith('!['):
            prev = lines[i - 1] if i > 0 else ''
            prevprev = lines[i - 2] if i > 1 else ''
            if not PREVIEW_COMMENT_RE.match(prev) and not PREVIEW_COMMENT_RE.match(prevprev):
                problems.append((i + 1, 'raw image (ไม่มี <!-- gen-preview --> ก่อนหน้า) — orphan หรือของซ้ำ'))

    # 2. syntax พัง `](]` / ปิดด้วย `]]`
    for i, l in enumerate(lines):
        if '](]' in l or l.rstrip().endswith(']]'):
            problems.append((i + 1, 'image syntax ผิด (พบ "](]" หรือ "]]")'))

    # 3. ภาพ path อ้างซ้ำ — placeholder เดียวต้องมี preview เดียว
    seen = {}
    for i, l in enumerate(lines):
        for m in re.finditer(r'\.\./media/generated/([a-z0-9][a-z0-9._-]*)\.(?:png|jpe?g|webp)', l):
            seen.setdefault(m.group(1), []).append(i + 1)
    for pid, locs in sorted(seen.items()):
        if len(locs) > 1:
            problems.append((locs[0], f'อ้างอิงภาพ {pid} ซ้ำ {len(locs)} จุด (L{"/L".join(map(str, locs))}) — ควรมีจุดเดียว'))

    # 4. heading (H2/H3) ซ้ำ
    heads = {}
    for i, l in enumerate(lines):
        m = re.match(r'^(#{2,3})\s+(.*\S)\s*$', l)
        if m:
            heads.setdefault((m.group(1), m.group(2)), []).append(i + 1)
    for (lvl, title), locs in sorted(heads.items()):
        if len(locs) > 1:
            problems.append((locs[0], f'heading "{title}" ซ้ำ {len(locs)} ครั้ง (L{"/L".join(map(str, locs))})'))

    # 5. ย่อหน้า (>40 ตัวอักษร) ซ้ำกันทุกตัวอักษร (ไม่นับย่อหน้าที่เป็น placeholder/รูปภาพ)
    paras = {}
    cur, cur_start = [], None
    def flush():
        nonlocal cur, cur_start
        if cur:
            p = ' '.join(x.strip() for x in cur)
            if len(p) > 40 and not any(('{{image:' in x or x.lstrip().startswith('![')) for x in cur):
                paras.setdefault(p, []).append(cur_start)
        cur, cur_start = [], None
    for i, l in enumerate(lines):
        if l.strip():
            if cur_start is None:
                cur_start = i + 1
            cur.append(l)
        else:
            flush()
    flush()
    for p, locs in paras.items():
        if len(locs) > 1:
            problems.append((locs[0], f'ย่อหน้าซ้ำ {len(locs)} ครั้ง (L{"/L".join(map(str, locs))}): {p[:60]}…'))

    # 6. บรรทัดซ้ำ (exact, >=25 ตัวอักษร, ไม่ใช่ horizontal rule, ไม่ใช่ caption ของ placeholder/รูป)
    lines_seen = {}
    for i, l in enumerate(lines):
        s = l.strip()
        if i in media_idx or len(s) < 25 or re.match(r'^([-*_])\1{2,}$', s):
            continue
        lines_seen.setdefault(s, []).append(i + 1)
    for s, locs in sorted(lines_seen.items()):
        if len(locs) > 1:
            problems.append((locs[0], f'บรรทัดซ้ำ {len(locs)} ครั้ง (L{"/L".join(map(str, locs))}): {s[:60]}…'))

    problems.sort(key=lambda x: x[0])
    return problems


def repair(path, rel='../media/generated', ext='.png'):
    """ลบของเสียเชิงกลจากบั๊กแทรก preview — deterministic, เก็บของที่ดีไว้หมด
    (1) raw `![...]` / fragment tail ที่ไม่ใช่ preview ตัวจริงของ placeholder
        (ระบุ preview ตัวจริงด้วยการ match caption กับ placeholder — กันลบภาพจริงผิด)
    (2) heading/paragraph/บรรทัดที่ซ้ำกันทุกตัวอักษร (เก็บอันแรก)
    (3) blank 3+ บรรทัด
    คืน (lines_removed, รายการที่ลบ) — ไม่แตะ placeholder / preview block ที่ถูกต้อง"""
    lines = _read(path).split('\n')
    text = _read(path)
    # placeholder caption ต่อ id — ใช้ระบุ preview ตัวจริง
    captions = {m.group(1): _alt(m.group(2)) for m in PLACEHOLDER_RE.finditer(text)}
    removed, log = 0, []

    def count(n):
        nonlocal removed
        removed += n

    # ---- Pass 1: ลบ raw image / fragment tail / orphan ที่แทรกคั่น ----
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        m = PREVIEW_COMMENT_RE.match(l)
        if m:
            pid = m.group(1)
            out.append(l)
            i += 1
            # หา preview ตัวจริง: บล็อก `![` ที่ caption ตรงกับ placeholder
            # (ลอง caption ก่อน แล้วค่อย fallback เป็น filename — ไม่เจอ = ไม่ลบอะไร)
            legit = None
            j = i
            limit = min(len(lines), i + MAX_IMAGE_LINES * 2)
            while j < limit:
                if lines[j].lstrip().startswith('!['):
                    k = j
                    while k < len(lines) and not ('../media/generated/' in lines[k] and lines[k].rstrip().endswith(')')):
                        k += 1
                    if k < len(lines):
                        img = lines[j:k + 1]
                        alt_flat = re.sub(r'\s+', ' ', img[0][2:].strip())
                        if captions.get(pid) and alt_flat == captions[pid]:
                            legit = (j, k)
                            break
                        if f'/{pid}{ext}' in img[-1]:
                            legit = (j, k)  # fallback: filename ตรง แต่ caption ไม่ตรง — กันลบภาพจริง
                            # (ถ้าเจอ caption ตรงภายหลัง จะแทนที่ด้วย caption-match)
                j += 1
            if legit:
                # ลบ orphan `![` ใด ๆ ที่แทรกคั่นก่อนภาพจริง
                for t in range(i, legit[0]):
                    if lines[t].lstrip().startswith('!['):
                        count(1)
                        log.append(f'ลบ raw image แทรกคั่น L{t + 1}: {lines[t].strip()[:60]}…')
                out.extend(lines[legit[0]:legit[1] + 1])
                i = legit[1] + 1
                # ลบ tail ที่ตามมา (path ซ้ำ / `![` ซ้ำ) จนถึง prose
                while i < len(lines):
                    cur = lines[i]
                    if cur.lstrip().startswith('!['):
                        # ข้ามทั้งบล็อกของภาพซ้ำ
                        k = i
                        while k < len(lines) and not ('../media/generated/' in lines[k] and lines[k].rstrip().endswith(')')):
                            k += 1
                        count(k + 1 - i if k < len(lines) else 1)
                        log.append(f'ลบภาพซ้ำหลัง preview L{i + 1}: {cur.strip()[:60]}…')
                        i = k + 1 if k < len(lines) else i + 1
                        continue
                    if '../media/generated/' in cur:
                        count(1)
                        log.append(f'ลบ fragment tail L{i + 1}: {cur.strip()[:60]}…')
                        i += 1
                        continue
                    if cur.strip() == '':
                        out.append(cur)   # blank ตัวคั่นภาพกับ prose — เก็บไว้ (Pass 3 จะยุบซ้ำ)
                        i += 1
                        continue
                    break
            else:
                i += 1  # ไม่เจอภาพจริง — เก็บ comment ไว้ (validate จะชี้)
            continue
        if l.lstrip().startswith('!['):  # raw image นอก preview
            j, limit = i, min(len(lines), i + MAX_IMAGE_LINES)
            while j < limit and not ('../media/generated/' in lines[j] and lines[j].rstrip().endswith(')')):
                j += 1
            count((j + 1 - i) if j < limit else 1)
            log.append(f'ลบ raw image L{i + 1}: {l.strip()[:60]}…')
            i = j + 1 if j < limit else i + 1
            continue
        if '../media/generated/' in l:  # fragment tail นอก preview
            count(1)
            log.append(f'ลบ fragment tail L{i + 1}: {l.strip()[:60]}…')
            i += 1
            continue
        out.append(l)
        i += 1
    lines = out

    # ---- Pass 2: dedupe heading / paragraph / บรรทัด (exact, เก็บอันแรก) ----
    media_idx = _media_line_idxs(lines)
    seen_head, seen_para, seen_line = set(), set(), set()
    out, i, cur = [], 0, []
    start_line = None

    def flush_para():
        nonlocal cur
        if cur:
            p = ' '.join(x.strip() for x in cur)
            if (len(p) > 40 and p in seen_para
                    and not any(('{{image:' in x or x.lstrip().startswith('![')) for x in cur)):
                count(len(cur))
                log.append(f'ลบย่อหน้าซ้ำ L{start_line}: {p[:60]}…')
            else:
                if len(p) > 40:
                    seen_para.add(p)
                out.extend(cur)
        cur = []
    while i < len(lines):
        l = lines[i]
        m = re.match(r'^(#{2,3})\s+(.*\S)\s*$', l)
        if m:
            flush_para()
            key = (m.group(1), m.group(2))
            if key in seen_head:
                count(1)
                log.append(f'ลบ heading ซ้ำ L{i + 1}: {l.strip()}')
            else:
                seen_head.add(key)
                out.append(l)
            i += 1
            continue
        s = l.strip()
        if (len(s) >= 25 and not re.match(r'^([-*_])\1{2,}$', s)
                and i not in media_idx):
            if s in seen_line:
                count(1)
                log.append(f'ลบบรรทัดซ้ำ L{i + 1}: {s[:60]}…')
                i += 1
                continue
            seen_line.add(s)
        if s:
            if not cur:
                start_line = i + 1
            cur.append(l)
        else:
            flush_para()
            out.append(l)   # เก็บบรรทัดว่าง (paragraph separator) ไว้
        i += 1
    flush_para()
    lines = out

    # ---- Pass 3: blank 3+ → 1 ----
    out = []
    for l in lines:
        if l.strip() == '' and out and out[-1].strip() == '':
            count(1)
            continue
        out.append(l)
    lines = out

    # Safety guard: repair ต้องไม่ทำให้ comment ใดเสียภาพ — ถ้าเสีย = ยกเลิก (ไม่เขียน)
    missing = _comment_image_ok(lines)
    if missing:
        return (-1, [f'ยกเลิก (ไม่เขียนไฟล์) — มี comment ที่ไม่มีภาพตามจริง: '
                     f'{", ".join(f"L{ln} {m}" for ln, m in missing)}'])

    _write(path, '\n'.join(lines))
    return removed, log


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('cmd', nargs='?', choices=['insert', 'strip', 'validate', 'repair'])
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--rel', default='../media/generated')
    ap.add_argument('--ext', default='.png')
    args = ap.parse_args()

    if not args.cmd or not args.paths:
        print(__doc__)
        sys.exit(1)

    failed = False
    for path in args.paths:
        if not os.path.isfile(path):
            print(f'[{args.cmd}] {path}: ไม่พบไฟล์')
            failed = True
            continue

        if args.cmd == 'insert':
            r = insert(path, args.rel, args.ext)
            if 'broken' in r:
                print(f'[insert] {path}: ยกเลิก — placeholder พัง: '
                      f'{", ".join(r["broken"])} (แก้ให้มี }}}} ปิดก่อน)')
                failed = True
                continue
            ok = r['placeholders'] == r['previews']
            failed = failed or not ok
            print(f'[insert] {path}: placeholders={r["placeholders"]}, '
                  f'previews={r["previews"]} → {"OK" if ok else "CHECK"}')

        elif args.cmd == 'strip':
            print(f'[strip] {path}: ลบ preview {strip(path)} ชุด')

        elif args.cmd == 'repair':
            removed, log = repair(path)
            if removed == -1:
                failed = True
                print(f'[repair] {path}: {log[0]}')
                continue
            if log:
                print(f'[repair] {path}: ลบ {removed} บรรทัด:')
                for entry in log:
                    print(f'  - {entry}')
            else:
                print(f'[repair] {path}: ไม่มีของเสีย (no-op) ✅')
            problems, pending = validate(path, args.rel, args.ext)
            if problems:
                failed = True
                print(f'[repair→validate] {path}: ยังพบปัญหา {len(problems)}:')
                for p in problems:
                    print(f'  - {p}')
            else:
                print(f'[repair→validate] {path}: OK ✅')

        else:
            problems, pending = validate(path, args.rel, args.ext)
            note = f' (ยังไม่ได้ gen {len(pending)})' if pending else ''
            if problems:
                failed = True
                print(f'[validate] {path}: พบปัญหา {len(problems)}{note}:')
                for p in problems:
                    print(f'  - {p}')
            else:
                print(f'[validate] {path}: OK{note}')

    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
