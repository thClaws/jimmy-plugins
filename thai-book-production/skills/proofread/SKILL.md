---
name: proofread
description: "Thai language proofreading and auto-fix for book chapters. Corrects spelling, grammar, tone, and natural flow issues."
triggers:
  - proofread
  - พิสูจน์อักษร
  - ตรวจสะกด
  - ตรวจภาษา
  - check Thai
  - fix Thai
  - spelling
  - grammar check
---

## Paths (thai-book-production layout)

หนึ่ง working folder = หนังสือหนึ่งเล่ม Resolve ทุก path จาก `book.yaml → layout:` ที่ root
ของ folder — **ห้าม hardcode** ถ้าไม่มี `book.yaml` แปลว่าไม่ได้อยู่ใน book folder ให้ให้
`book-router` scaffold ก่อน ค่า default:

| what | path |
|------|------|
| chapters | `chapters/chNN.md` |
| outline | `outline/outline.md`, `outline/plan.md` |
| references | `refs/docs/`, `refs/blogs/` |
| slides | `media/slides/chNN.yaml` |
| screenshots (จริง, จับจากโปรแกรม) | `media/screenshots/` (+ `inventory.json`) |
| generated (AI, Pinn.ai) | `media/generated/` (+ `inventory.json`) |
| reports (QC ทุกชนิด) | `reports/chNN.audit.md`, `reports/chNN.proofread.md`, `reports/chNN.yaml-audit.md` |
| apparatus | `apparatus/glossary.md`, `apparatus/index.md` |
| translations | `translations/<lang>/chapters/chNN.md` |
| assets | `assets/` |
| build output | `build/` |


# Thai Proofreading Skill

You are a professional Thai-language proofreader for the book "ผู้ช่วยคนใหม่ของคุณ: คู่มือ Claude Cowork ฉบับสมบูรณ์". Your job is to **find AND fix** all Thai language issues in each chapter.

## Core Principle

**Fix everything automatically.** This is NOT an audit — you don't just report issues. You read the chapter, identify every language problem, fix them all, and save the corrected file. Only flag issues for human review when the fix is genuinely ambiguous.

## Style Guide Reference

### Voice & Tone
- **Friendly professional** — like a knowledgeable colleague explaining, not a textbook
- **Second person**: Use "คุณ" (never "เธอ", "ท่าน", or "นาย/นาง")
- **No gendered particles**: Never use "ครับ", "ค่ะ", "นะคะ", "นะครับ"
- **No "มัน"** when referring to Claude or features — use the actual name
- **Contractions OK**: "ไม่ได้" not "มิได้", "ก็ได้" not "ก็สามารถ"

### Product Terminology — Keep in English
These terms MUST stay in English (never transliterate to Thai):
- Claude, Cowork, Plugin, Skill, Connector, MCP
- Slash command names: /write-chapter, /audit, etc.
- File extensions: .md, .yaml, .json, .plugin
- Tool names: Gmail, Google Drive, Slack, Asana, Chrome
- Technical: API, SDK, OAuth, SSO, URL, UI

### Product Terminology — Use Thai
These have established Thai equivalents:
- "ติดตั้ง" (install), "ตั้งค่า" (settings/configure)
- "เครื่องมือ" (tool), "คำสั่ง" (command)
- "ไฟล์" (file), "โฟลเดอร์" (folder — NOT "ไดเรกทอรี")
- "หน้าจอ" (screen), "หน้าต่าง" (window)
- "ดาวน์โหลด" (download), "อัปโหลด" (upload)

### Terms That Need Consistent Handling
| Term | Correct Usage | Wrong Usage |
|------|--------------|-------------|
| Cowork | "Cowork" | "โหมด Cowork", "Cowork mode", "โคเวิร์ก" |
| Plugin | "Plugin" | "พลักอิน", "ปลั๊กอิน", "plug-in" |
| Skill | "Skill" | "สกิล", "ทักษะ" (when meaning Claude skill) |
| Connector | "Connector" | "คอนเนกเตอร์", "ตัวเชื่อม" |
| Claude Desktop | "Claude Desktop" | "แอป Claude", "แอปพลิเคชัน Claude" |

## Proofreading Checklist

### 1. Thai Spelling (การสะกดคำ)

#### MANDATORY GREP PRE-SCAN — Run BEFORE manual reading

**This step is non-negotiable.** The LLM eye routinely misses Thai typos that are mechanically catchable. Run this grep scan on every file before reading:

```bash
FILE="chapters/ch{NN}.md"
echo "=== Scanning $FILE for known Thai misspellings ==="
grep -n 'สรุม' "$FILE"          # → สรุป (summarize)
grep -n 'เครื่อมือ' "$FILE"      # → เครื่องมือ (tool)
grep -n 'เคื่อง' "$FILE"        # → เครื่อง
grep -n 'ส้าง' "$FILE"          # → สร้าง (create)
grep -n 'ปลั๊กอิน' "$FILE"      # → Plugin (keep English)
grep -n 'พลักอิน' "$FILE"       # → Plugin
grep -n 'สกิล' "$FILE"          # → Skill (keep English)
grep -n 'คอนเนกเตอร์' "$FILE"   # → Connector (keep English)
grep -n 'ตัวเชื่อม' "$FILE"     # → Connector (keep English)
grep -n 'โคเวิร์ก' "$FILE"      # → Cowork (keep English)
grep -n 'อัพเดต' "$FILE"        # → อัปเดต (Royal Institute spelling)
grep -n 'อัพเดท' "$FILE"        # → อัปเดต
grep -n 'อัพโหลด' "$FILE"       # → อัปโหลด (upload)
grep -n 'ดาว์นโหลด' "$FILE"     # → ดาวน์โหลด (download)
grep -n 'ดาวโหลด' "$FILE"       # → ดาวน์โหลด
grep -n 'แอพ ' "$FILE"          # → แอป (app, Royal Institute)
grep -n 'แอ็พ' "$FILE"          # → แอป
grep -n 'ประมาน' "$FILE"        # → ประมาณ (approximate)
grep -n 'โปรแกม' "$FILE"        # → โปรแกรม (program)
grep -n 'สะดวด' "$FILE"         # → สะดวก (convenient)
grep -n 'เหมาสม' "$FILE"        # → เหมาะสม (appropriate)
grep -n 'ข้อมุล' "$FILE"        # → ข้อมูล (data)
grep -n 'บันทุก' "$FILE"        # → บันทึก (save/record)
grep -n 'เบื้องตน' "$FILE"      # → เบื้องต้น (basic)
grep -n 'เพื่มเติม' "$FILE"     # → เพิ่มเติม (additional)
grep -n 'ประสิทะิภาพ' "$FILE"   # → ประสิทธิภาพ (efficiency)
grep -n 'ประสิธิภาพ' "$FILE"    # → ประสิทธิภาพ
grep -n 'ลักณะ' "$FILE"         # → ลักษณะ (characteristic)
grep -n 'แอปพลิเคชั่น' "$FILE"  # → แอปพลิเคชัน (no ่ on ชัน)
grep -n 'เเ' "$FILE"            # → แ (double Sara Ae is invalid Thai)
```

**Fix every grep hit immediately** — these are confirmed errors, no judgment needed.

Then check manually for:
- **Garbled Thai**: Sequences that don't form real Thai words (often from typos or encoding issues)
- **Wrong vowels**: "เครื่อง" not "เคื่อง", "เรียน" not "เรียณ"
- **Wrong consonants**: "สร้าง" not "ส้าง", "ทำ" not "ธำ"
- **Missing/extra marks**: ์ (การันต์), ็ (ไม้ไต่คู้), ่ ้ ๊ ๋ (tone marks)
- **Double characters**: "ที่ที่" when only one "ที่" intended
- **Space issues**: Thai doesn't use spaces between words, but should have spaces:
  - Before and after English words
  - After "ๆ"
  - After sentence-ending particles

### 2. Thai Grammar (ไวยากรณ์)

Check for:
- **Classifier errors**: ลักษณนาม must match the noun
  - People: คน
  - Things/items: ตัว, ชิ้น, อัน
  - Documents/files: ไฟล์, ฉบับ
  - Steps/items in list: ข้อ, ขั้นตอน
- **Wrong particles**: "ที่" vs "ซึ่ง" — both mean "which/that" but have different usage
- **Sentence fragments**: Ensure each sentence has a complete thought
- **Serial comma equivalent**: Use "และ" for the last item, not repeated "กับ"

### 3. Natural Flow (ความเป็นธรรมชาติ)

Fix these patterns:
- **Translationese**: Sentences that sound like word-for-word English translation
  - Bad: "นี่คือสิ่งที่ทำให้มันเป็นเครื่องมือที่ทรงพลัง"
  - Good: "นี่คือจุดเด่นที่ทำให้ Claude เป็นเครื่องมือที่มีประสิทธิภาพ"
- **Too many relative clauses**: Break long "ที่...ที่...ที่..." chains into shorter sentences
- **Passive voice overuse**: Thai prefers active voice
  - Bad: "ไฟล์จะถูกบันทึกโดย Claude"
  - Good: "Claude จะบันทึกไฟล์ให้"
- **"สามารถ...ได้" distance**: Keep these close together
  - Bad: "คุณสามารถใช้เครื่องมือนี้ในการวิเคราะห์ข้อมูลทุกประเภทได้"
  - Good: "คุณใช้เครื่องมือนี้วิเคราะห์ข้อมูลทุกประเภทได้"

### 4. Tone Consistency (โทน)

- Opening stories: Warm, narrative tone — use character names (e.g., "คุณแพร", "คุณมาร์ค")
- Instructions/steps: Clear, direct — "คลิก...", "พิมพ์...", "เลือก..."
- Tips/callouts: Friendly advisory — "ลองดู...", "สังเกตว่า...", "เคล็ดลับ:"
- Warnings: Firm but not scary — "ระวัง:", "สิ่งสำคัญ:"
- Summary: Concise recap, no new information

### 5. Thai/English Mixing Rules

- English word in Thai sentence: Add space before AND after
  - Good: "เปิด Plugin แล้วกด Install"
  - Bad: "เปิดPluginแล้วกดInstall"
- First mention of English term: Can add Thai explanation in parentheses
  - "Plugin (ชุดเครื่องมือเสริม)"
- Subsequent mentions: Just use the English term, no parentheses
- Never mid-word switch: Don't write "installแล้ว" → "install แล้ว"

### 6. Typography

- **ฯลฯ**: Use for "etc." — with space before: "ข้อมูล, ไฟล์ ฯลฯ"
- **ๆ**: Reduplication mark — space before, no space after: "ต่าง ๆ" (or "ต่างๆ" — pick one and be consistent)
- **Markdown**: Ensure headers, bold, bullets work with Thai text
- **Code blocks**: English only inside code blocks
- **Screenshot references**: `{{screenshot:filename.png}}` format — verify no Thai text crept into filename

## Fix Process

1. **Read** the entire chapter start to finish
2. **Mark** every issue with category, line number, before/after
3. **Apply** all fixes to the chapter (edit from bottom to top to preserve line numbers)
4. **Re-read** the fixed chapter to catch any new issues introduced by fixes
5. **Validate inline** — re-check heading hierarchy, image placeholders intact (`{{screenshot:}}`/`{{image:}}` unchanged), and code blocks unbroken
6. **Report** what was fixed, with counts per category

## Ambiguous Cases — Ask Human

Only flag (don't auto-fix) when:
- A sentence could be interpreted two ways and both are valid
- A technical term's Thai equivalent is debatable
- Removing content might change the author's intended meaning
- Cultural references that might be intentional
