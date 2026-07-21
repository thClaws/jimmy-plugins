---
name: outline-planner
description: สร้างชุดวางแผนหนังสือ technical/tutorial ครบวงจร — detailed outline (ภาค/บท/subtopics), learning objectives ต่อบท, page plan คุมความหนา และ hand-off notes — สำหรับหัวข้อใดก็ได้ (software, AI tools, hardware, business, howto) Use this skill whenever the user asks to create, refine, audit, or expand a book outline, course outline, or curriculum; mentions "ทำ outline หนังสือ", "วางโครงหนังสือ", "ปรับ outline", "audit outline", "learning objectives", "page plan", "ประเมินจำนวนหน้า", "hand-off notes สำหรับหนังสือ"; or shares a rough chapter list for a chapters/ they want to write — even if they only ask for one piece (เช่นขอแค่ outline) ให้ใช้ skill นี้เพื่อให้ได้มาตรฐานเดียวกันทุกเล่ม
---

## Paths (thai-book-production layout)

หนึ่ง working folder = หนังสือหนึ่งเล่ม Resolve ทุก path จาก `book.yaml → layout:` ที่ root
ของ folder — **ห้าม hardcode** ถ้าไม่มี `book.yaml` แปลว่าไม่ได้อยู่ใน book folder ให้ให้
`init-book` scaffold ก่อน ค่า default:

| what | path |
|------|------|
| chapters | `chapters/chNN.md` |
| outline | `outline/outline.md`, `outline/plan.md` |
| references | `refs/docs/`, `refs/blogs/` |
| slides | `media/slides/chNN.yaml` |
| screenshots (จริง, จับจากโปรแกรม) | `media/screenshots/` (+ `inventory.json`) |
| generated (AI, built-in TextToImage) | `media/generated/` (+ `inventory.json`) |
| reports (QC ทุกชนิด) | `reports/chNN.audit.md`, `reports/chNN.proofread.md`, `reports/chNN.yaml-audit.md` |
| apparatus | `apparatus/glossary.md`, `apparatus/index.md` |
| translations | `translations/<lang>/chapters/chNN.md` |
| assets | `assets/` |
| build output | `build/` |


# Book Outline Planner

สร้างชุดเอกสารวางแผนหนังสือ technical/tutorial ที่ผ่านการ audit ครบถ้วน ประกอบด้วย 4 deliverables:

1. `<slug>-outline.md` — detailed outline: ภาค → บท → subtopics (x.1–x.n) → bullet ย่อย
2. `<slug>-plan.md` — learning objectives ต่อบท + page plan
3. `HANDOFF-<slug>.md` — hand-off notes สำหรับทำต่อใน session อื่น (สร้างเมื่อผู้ใช้ขอ หรือบอกว่าจะย้ายไปทำที่อื่น)
4. อัปเดตไฟล์เหล่านี้เมื่อผู้ใช้เปลี่ยนการตัดสินใจ (เช่น ยกเลิกเล่มอื่น, เปลี่ยน scope)

ภาษา: ไทย คงศัพท์เทคนิคภาษาอังกฤษ เว้นแต่ผู้ใช้กำหนดอื่น

---

## Phase 0 — เก็บ Input

ก่อนเริ่ม ต้องรู้ (ถามเฉพาะที่เดาไม่ได้ ถามครั้งเดียวไม่เกิน 1–2 คำถาม):
- **หัวข้อ** และขอบเขต (ผลิตภัณฑ์เดียว? ecosystem? เวอร์ชันไหน?)
- **Audience หลัก** — กำหนดโทน ศัพท์ และบทที่ต้องมี (developer / knowledge worker / ผู้บริหาร / มือใหม่)
- **draft outline เดิม** ถ้ามี — จะทำ gap analysis เทียบ ไม่ทิ้งของเดิม
- **ความสัมพันธ์กับหนังสือเล่มอื่นของผู้เขียน** — standalone หรือ cross-reference ได้ (default: standalone)
- **นโยบาย beta/unstable features** — cover เต็ม, cover พอรู้จัก, หรือข้าม (default: cover เต็มพร้อมป้ายกำกับ)

ถ้าผู้ใช้ให้ draft outline มา: อย่าเพิ่งถาม — audit เทียบ source ก่อนแล้วเสนอ gap พร้อมโครงใหม่ในรอบเดียว

## Phase 1 — Audit Surface ของหัวข้อ

**ห้ามเขียน outline จากความจำอย่างเดียว** ต้องมี inventory จากแหล่งจริงก่อน:

0. **อ่าน `{refs_docs}/` และ `{refs_blogs}/` ก่อน** — ในโมเดล PLAN แบบลูป `get-book-ref` จะ
   seed เอกสารแกนหลักไว้ให้แล้ว ใช้ของในนั้นเป็นฐาน inventory ถ้า `refs/` ว่าง ให้บอกผู้ใช้ว่า
   ควรรัน `get-book-ref` (seed) ก่อน หรือจะให้ค้น live ในขั้นนี้แทนก็ได้
1. หา authoritative source index — official docs (มองหา llms.txt หรือ sitemap ของ docs), spec, มาตรฐาน, ตำราหลักของสาขา (เสริมจากที่ `refs/` มียังไม่พอ)
2. สร้าง **feature/topic inventory**: รายการทุกความสามารถ/หัวข้อย่อยที่ source ครอบคลุม
3. บันทึกวันที่/เวอร์ชันของ source ที่ใช้ — จะกลายเป็นหมายเหตุ volatility ในเล่ม

ผลลัพธ์ phase นี้: รายการ inventory ที่จะใช้เช็ค coverage ใน Phase 4

## Phase 2 — วางโครงภาคตาม Learning Arc

ใช้ arc มาตรฐาน 7 ช่วง ปรับชื่อ/จำนวนตามหัวข้อ:

| ช่วง | เนื้อหา | หมายเหตุ |
|---|---|---|
| 1. เริ่มต้น | คืออะไร, เลือก platform, ติดตั้ง, **ลงมือครั้งแรก**, โครงตั้งค่า | ต้องมีบท hands-on แรกก่อนเข้า reference เสมอ |
| 2. ใช้งานประจำวัน | workflow จริงประจำวัน, คำสั่ง/เครื่องมือหลัก, session/state | บท "workflow ประจำวัน" คือบทที่คนพลาดบ่อยสุด |
| 3. ควบคุมเชิงลึก | context/memory/config ขั้นสูง, ต้นทุน, เทคนิคชั้นสูง | |
| 4. ความปลอดภัย | สิทธิ์, ขอบเขต, threat model, compliance | แนะนำเบื้องต้นไว้ในบทลงมือครั้งแรก แล้ว deep dive ที่นี่ |
| 5. ขยายความสามารถ | ระบบ extension ทุกแบบ | เปิดภาคด้วย "บทแผนที่" เทียบทุกกลไก + decision framework ก่อนลงรายตัว |
| 6. Automation | งานอัตโนมัติ, ขนาน, orchestration | จบภาคด้วยบท synthesis "เลือกกลไกไหนกับโจทย์ไหน" |
| 7. Production/องค์กร | integration, ทีม, enterprise, deployment | ตัด/ย่อได้ก่อนถ้าเล่มหนาเกิน |

กติกาสำคัญ:
- **หนึ่ง concept หนึ่งบ้าน** — เนื้อหาอยู่บทเดียว บทอื่นใช้ cross-ref "(เจาะลึกบทที่ N)" ห้ามเขียนซ้ำ
- **อย่าประดิษฐ์ศัพท์คู่สมมาตรที่ไม่มีจริงในหัวข้อ** (taxonomy trap) — ถ้าผลิตภัณฑ์ไม่มี feature ชื่อนั้น อย่าตั้งบทชื่อนั้น ให้ปฏิบัติกับมันเป็นแง่มุมของ feature ที่มีจริง
- แต่ละ concept ที่ผู้อ่านเจอเร็ว (permission, error แรก) ต้องมี preview เบา ๆ ในภาค 1 ก่อน deep dive

## Phase 3 — แตกรายละเอียด

ต่อบท:
- subtopics x.1–x.n (ปกติ 3–6 ต่อบท) แต่ละอันมี bullet ย่อย 2–5 ข้อ
- bullet เป็นเนื้อหาจริง ไม่ใช่คำอธิบาย meta ("อธิบายว่า...") — เขียนสิ่งที่บทจะพูด
- ฝัง internal cross-ref เป็นเลขบทตั้งแต่ตอนนี้
- **ไฟล์สุดท้ายห้ามมี annotation กระบวนการ** (เช่น "(ใหม่)", "(ขยาย)", "(ย้ายมาจาก...)") — ใช้ได้เฉพาะฉบับ draft ที่กำลังรีวิวกับผู้ใช้ ก่อนส่งมอบต้องลบหมด
- ภาคผนวกมาตรฐาน: Glossary / Reference tables / Troubleshooting / วิธีติดตามของใหม่ (ระบุแนวปฏิบัติ verify เวอร์ชัน)

## Phase 4 — Audit Pass (ทำทุกครั้งก่อนส่งมอบ)

รัน 4 เช็คนี้ แล้วรายงานผลให้ผู้ใช้เห็น:

1. **Coverage** — ไล่ inventory จาก Phase 1 ทีละรายการว่าอยู่บทไหน รายการที่ไม่อยู่: เพิ่มหรือแจ้งเหตุผลที่ตัด
2. **Learning flow** — ผู้อ่านเจอ concept ก่อนถูกสอนไหม? มี hands-on ก่อน reference ไหม? บทแผนที่อยู่ต้นภาค extension ไม่ใช่ท้าย?
3. **Standalone** (ถ้าเป็นนโยบาย) — `grep` หาการอ้างหนังสือ/ผลงานอื่นของผู้เขียน เหลือได้เฉพาะ official docs และ reference ท้ายเล่ม
4. **Annotation** — `grep` หา "(ใหม่", "(ขยาย", "(ย้าย" และ meta text อื่น ลบให้หมด

## Phase 5 — Learning Objectives + Page Plan

**Objectives** ต่อบท 2–5 ข้อ:
- ขึ้นต้น "ผู้อ่านจะสามารถ..." + verb วัดได้ (ติดตั้ง สร้าง เลือก debug อธิบาย เทียบ ประเมิน) — ห้ามใช้ "เข้าใจ" "รู้จัก" ลอย ๆ
- ต้อง map กลับไป subtopics ของบทนั้นครบ — objective ที่ไม่มี subtopic รองรับ = ช่องโหว่
- บอกผู้ใช้ว่า objectives ใช้เป็น checklist ตอนเขียนจบบท

**Page plan**:
- ระบุสมมติฐาน: รูปเล่ม (default B5), ~350–450 คำ/หน้า รวม code/screenshot
- ถ่วงน้ำหนัก: บท hands-on หนัก = หน้าเยอะ (14–24), บท concept/เทียบ = 8–12
- ตารางรวมต่อภาค + รวมเล่ม (อย่าลืม front/back matter ~10–12 หน้า)
- ถ้าเกิน ~400 หน้า: เสนอ **scenario กระชับ** พร้อมรายการตัดที่เลขบวกลบตรงจริง (ตรวจเลขคณิตก่อนส่ง)
- ระบุ **จุดห้ามตัด** เสมอ: ภาคความปลอดภัย, บท workflow ประจำวัน, บทแผนที่ extension, บทที่เป็นจุดขายของเล่ม
- ถ้าบทใดเป็นแหล่งความลึกเดียวที่เหลือของหัวข้อ (เช่น เล่มคู่ถูกยกเลิก) ถอดออกจากรายการตัด

## Phase 6 — Hand-off Notes (เมื่อผู้ใช้ขอหรือจะย้าย session)

โครง HANDOFF ต้องมี:
- วันที่ + คำเตือนแยก session/folder จากโปรเจกต์อื่นถ้ามีเล่มคู่ขนาน
- สถานะ: เสร็จแล้ว / ยังไม่เริ่ม / **การตัดสินใจที่ค้าง** (ระบุว่าต้องตัดสินใจก่อนขั้นไหน)
- การตัดสินใจที่ปิดแล้วพร้อมเหตุผลย่อ กำกับ "อย่า revisit โดยไม่จำเป็น" — รวมข้อห้าม (เช่น "ห้ามใส่ cross-ref ไปเล่ม X")
- ข้อควรระวัง: volatility ของหัวข้อ + URL แหล่ง verify
- Style & conventions ของเล่ม
- รายการไฟล์ที่ต้องเอาเข้า working folder
- Next steps เรียงลำดับ — แนะนำ draft บท hands-on ก่อนบทที่ 1 (จับโทนก่อน), บท beta/volatile ทีหลังสุด, ทำ screenshot inventory ควบคู่

## Phase 7 — Human approval gate (บังคับก่อนเริ่มเขียนบท)

ส่งมอบ outline แล้ว **ต้องหยุดรอคนรีวิว** — เชิญให้ผู้ใช้ปรับแก้/สั่งแก้จนพอใจ แล้วบอก
"อนุมัติ outline" เมื่ออนุมัติ ให้เขียน `{outline}/APPROVED.md` (วันที่ + สรุปสิ่งที่ปรับ + ผู้อนุมัติ)
— `book-router` ใช้ไฟล์นี้เป็น gate: **ยังไม่มี APPROVED.md = ห้ามเริ่ม write-book-chapter**
ถ้า outline ถูกแก้ใหญ่หลังอนุมัติ ให้ลบ/อัปเดต APPROVED.md แล้วขออนุมัติใหม่

## หลักปฏิบัติตลอดกระบวนการ

- เขียนไฟล์จริงเสมอ (ไม่ใช่แค่ตอบในแชท) และส่งมอบผ่านเครื่องมือ present ไฟล์ที่มี
- เมื่อผู้ใช้เปลี่ยนการตัดสินใจกลางทาง: แก้ให้ครบทุกไฟล์ที่กระทบ (outline + plan + HANDOFF) แล้วสรุปว่าแก้อะไรที่ไหน
- ตัวเลขทุกตาราง (หน้า, จำนวนบท) ตรวจผลรวมก่อนส่งทุกครั้ง
- รายละเอียดที่อิงเวอร์ชัน ให้หมายเหตุ "verify กับ docs ก่อน draft บทนี้" ใน outline หรือ HANDOFF
- ถ้าหัวข้อมี feature ที่ผู้ใช้ถามว่า "มี X ไหม" — ตอบจาก inventory ไม่ใช่จากการเดา ถ้าไม่แน่ใจให้ search ก่อนตอบ
