#!/usr/bin/env python3
"""check-generic.py — fail if a specific book leaks back into the skills.

Every skill in this plugin must work for ANY book: what the book is about comes from
`book.yaml` (`book.subject`, `terminology:`, `sources:`, `mockup:`), never from a skill file.
The first version of this plugin was written while producing one particular book and its
product names ended up baked into prompts, grep scans, UI mockups and examples — which
silently steered every later book toward that same subject. This script is the guard.

Allowed exception: the plugin's own *runtime host*. This plugin runs inside Claude Cowork, so
a file may say so — but only the files listed in HOST_REFERENCES, and only about the host.

Usage:  python3 scripts/check-generic.py [root]      # exit 0 clean, 1 on leakage
"""
import os, re, sys

BANNED = [
    (r"[Cc]owork", "book-subject product name"),
    (r"โคเวิร์ก", "book-subject product name (Thai)"),
    (r"Claude Desktop", "book-subject product name"),
    (r"ผู้ช่วยคนใหม่ของคุณ", "title of one specific book"),
    (r"\bAnthropic\b", "vendor of one specific book's subject"),
    (r"(?:support\.|docs\.)?claude\.com", "source domain of one specific book"),
]

# path -> why a host mention is legitimate there
HOST_REFERENCES = {
    ".claude-plugin/plugin.json": "declares which host the plugin targets",
    ".claude-plugin/marketplace.json": "declares which host the plugin targets",
    "README.md": "documents the host the plugin runs in",
    "skills/book-router/SKILL.md": "describes the host's working-folder model",
    "skills/book-router/references/folder-structure.md": "describes the host's working folder",
    "skills/build-slides-pptx/scripts/slides2preview.py": "names the host's file preview as a pptx viewer",
    "scripts/check-generic.py": "this guard",
}

SCAN_EXT = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".template"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", "assets", "build"}


def main(root="."):
    root = os.path.abspath(root)
    bad = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root)
            if os.path.splitext(fn)[1] not in SCAN_EXT and not fn.endswith(".template"):
                continue
            if rel in HOST_REFERENCES:
                continue
            try:
                lines = open(path, encoding="utf-8").read().splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            for n, line in enumerate(lines, 1):
                for pat, why in BANNED:
                    if re.search(pat, line):
                        bad.append((rel, n, why, line.strip()[:100]))
                        break

    if bad:
        print(f"✗ {len(bad)} book-specific reference(s) leaked into the skills:\n")
        for rel, n, why, line in bad:
            print(f"  {rel}:{n}  [{why}]\n      {line}")
        print("\nFix: move the value into book.yaml (book.subject / terminology / sources / mockup)")
        print("and have the skill read it, or replace the example with a neutral one.")
        return 1

    print(f"✓ no book-specific references outside the {len(HOST_REFERENCES)} host-reference files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
