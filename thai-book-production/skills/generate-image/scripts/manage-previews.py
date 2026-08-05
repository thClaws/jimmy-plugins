#!/usr/bin/env python3
"""
manage-previews.py — จัดการ `<!-- gen-preview:<id> -->` blocks ใน chapter markdown

    python3 manage-previews.py insert   <chapter.md> [more.md ...]
    python3 manage-previews.py strip    <chapter.md> [more.md ...]
    python3 manage-previews.py validate <chapter.md> [more.md ...]

insert    แทรก/แทนที่ preview ให้ทุก `{{image:id|caption}}` (idempotent — รันซ้ำได้)
strip     ลบ preview ทั้งหมด (ใช้ก่อน resolve placeholder ใน build-epub-pdf)
validate  ตรวจว่า placeholder ไม่พัง ไม่มี orphan/preview ซ้ำ และภาพที่ gen แล้วมี preview ครบ
          (placeholder ที่ยังไม่มีไฟล์ภาพ = ยังไม่ได้ gen ไม่นับเป็นปัญหา)

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
                while j < limit and ')' not in lines[j]:
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

    return problems, pending


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('cmd', nargs='?', choices=['insert', 'strip', 'validate'])
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
