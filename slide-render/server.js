// slide-render — Marp + Chromium slide rendering microservice, plus doc-render
// (LibreOffice / poppler / tesseract) for office documents.
//
// POST /slides   (multipart)  markdown=<marp md>  [theme=thai-tech]  [images=<file>…]
//   → 200 application/zip  { deck.pdf, slides/slide-01.png … }
// POST /pptx     (multipart)  file=<.pptx>
//   → 200 application/zip  { deck.pdf, slides/slide-01.png … }   (same shape)
//
// Both render routes return `X-Slide-Count: <n>` — the number of rendered
// pages. The gateway bills per page off that header, so it must be set
// before the zip starts streaming.
// POST /convert /pdf/text /pdf/pages /ocr /html-to-pdf   (doc-render, see below)
// GET  /healthz
//
// Design (see README): the desktop/GUI NEVER calls this directly — the thClaws
// Rust engine relays here (holds the gateway token). Auth: Bearer SLIDE_RENDER_TOKEN
// (skip check if unset — dev only). Renders in an isolated temp dir, cleaned each call.

const express = require("express");
const multer = require("multer");
const { execFile } = require("child_process");
const { promisify } = require("util");
const archiver = require("archiver");
const fs = require("fs/promises");
const fss = require("fs");
const os = require("os");
const path = require("path");
const crypto = require("crypto");

const run = promisify(execFile);
const app = express();
// /slides carries a Marp deck plus its figures — many small files.
const upload = multer({ limits: { fileSize: 25 * 1024 * 1024, files: 60 } });

// /pptx carries ONE big file. Disk storage, not memory: a 200MB deck
// buffered in the Node heap alongside LibreOffice's own footprint is how
// the pod gets OOM-killed. multer streams it to /tmp and we hand
// LibreOffice the path it already wanted.
const uploadPptx = multer({
  dest: os.tmpdir(),
  storage: multer.diskStorage({
    destination: (_req, _file, cb) => cb(null, os.tmpdir()),
    filename: (_req, file, cb) =>
      cb(null, "up-" + crypto.randomBytes(8).toString("hex") + path.extname(safeName(file.originalname))),
  }),
  limits: { fileSize: 200 * 1024 * 1024, files: 1 },
});

const PORT = process.env.PORT || 8080;
const TOKEN = process.env.SLIDE_RENDER_TOKEN || "";
const THEMES_DIR = path.join(__dirname, "themes");
const TIMEOUT_MS = 120000;

const safeName = (n) => path.basename(String(n)).replace(/[^A-Za-z0-9._-]/g, "_");

function auth(req, res, next) {
  if (!TOKEN) return next(); // dev / behind gateway
  const h = req.get("authorization") || "";
  if (h === `Bearer ${TOKEN}`) return next();
  res.status(401).json({ error: "unauthorized" });
}

app.get("/healthz", (_req, res) => res.json({ ok: true, service: "slide-render" }));

app.post("/slides", auth, upload.fields([{ name: "images" }]), async (req, res) => {
  const md = req.body.markdown;
  if (!md || typeof md !== "string") {
    return res.status(400).json({ error: "missing 'markdown' field" });
  }
  const theme = safeName(req.body.theme || "thai-tech");
  const themeCss = path.join(THEMES_DIR, `${theme}.css`);
  if (!fss.existsSync(themeCss)) {
    return res.status(400).json({ error: `unknown theme '${theme}'` });
  }

  const job = path.join(os.tmpdir(), "slide-" + crypto.randomBytes(8).toString("hex"));
  try {
    await fs.mkdir(job, { recursive: true });
    // theme + fonts must sit next to the deck so @font-face url('fonts/…') resolves.
    await fs.cp(THEMES_DIR, path.join(job, "themes"), { recursive: true });
    await fs.writeFile(path.join(job, "deck.md"), md, "utf8");
    // uploaded images (screenshots / figures) referenced by <img src="name.png">
    for (const f of (req.files?.images || [])) {
      await fs.writeFile(path.join(job, safeName(f.originalname)), f.buffer);
    }

    const common = [
      "deck.md", "--theme", `themes/${theme}.css`,
      "--html", "--allow-local-files", "--no-stdin",
    ];
    const marp = process.env.MARP_BIN || "marp";
    await run(marp, [...common, "--pdf", "-o", "deck.pdf"], { cwd: job, timeout: TIMEOUT_MS });
    const outDir = path.join(job, "png");
    await fs.mkdir(outDir, { recursive: true });
    await run(marp, [...common, "--images", "png", "-o", path.join("png", "slide.png")],
      { cwd: job, timeout: TIMEOUT_MS });

    // Count the pages BEFORE streaming: the gateway meters this render per
    // rendered page and reads the count off the response header, which can
    // only be set while headers are still unsent.
    const pngs = (await fs.readdir(outDir)).sort();
    res.set("Content-Type", "application/zip");
    res.set("Content-Disposition", 'attachment; filename="deck.zip"');
    res.set("X-Slide-Count", String(pngs.length));
    const zip = archiver("zip", { zlib: { level: 6 } });
    zip.on("error", (e) => { throw e; });
    zip.pipe(res);
    zip.file(path.join(job, "deck.pdf"), { name: "deck.pdf" });
    for (const png of pngs) {
      zip.file(path.join(outDir, png), { name: `slides/${png}` });
    }
    await zip.finalize();
  } catch (e) {
    if (!res.headersSent) {
      res.status(500).json({ error: "render failed", detail: String(e.stderr || e.message || e).slice(0, 500) });
    }
  } finally {
    fs.rm(job, { recursive: true, force: true }).catch(() => {});
  }
});

// Render an existing .pptx for VIEWING — the Files tab shows only extracted
// text otherwise, and asking every user to install LibreOffice (Windows
// especially) isn't realistic. LibreOffice does pptx→pdf; pdftoppm rasterises.
// Marp/Chromium aren't involved: this is someone else's deck, not one we author,
// so nothing about it is Marp-shaped.
//
// Deliberately the SAME response shape as /slides ({deck.pdf, slides/*.png}) so
// the engine's existing unzip path handles both without a second code path.
app.post("/pptx", auth, uploadPptx.single("file"), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: "missing 'file' field" });
  const name = safeName(req.file.originalname || "deck.pptx");
  if (!/\.(pptx|ppt|odp)$/i.test(name)) {
    return res.status(400).json({ error: `unsupported extension for '${name}'` });
  }

  const job = path.join(os.tmpdir(), "pptx-" + crypto.randomBytes(8).toString("hex"));
  try {
    await fs.mkdir(job, { recursive: true });
    // multer already streamed it to disk — move rather than re-copy.
    const src = path.join(job, name);
    await fs.rename(req.file.path, src);

    // -env:UserInstallation pins a per-job profile: without it concurrent
    // conversions share ~/.config/libreoffice and the second one exits
    // silently having produced nothing.
    const soffice = process.env.SOFFICE_BIN || "soffice";
    await run(
      soffice,
      [
        `-env:UserInstallation=file://${path.join(job, "lo-profile")}`,
        "--headless",
        "--norestore",
        "--convert-to",
        "pdf",
        "--outdir",
        job,
        src,
      ],
      { cwd: job, timeout: TIMEOUT_MS },
    );

    // LibreOffice names the output after the input stem, not "deck".
    const pdfSrc = path.join(job, name.replace(/\.[^.]+$/, "") + ".pdf");
    if (!fss.existsSync(pdfSrc)) {
      return res.status(422).json({
        error: "conversion produced no pdf",
        detail: `libreoffice could not read '${name}'`,
      });
    }
    const pdf = path.join(job, "deck.pdf");
    await fs.rename(pdfSrc, pdf);

    // pdftoppm zero-pads and appends its own index: slide-01.png, slide-02.png…
    // — the numbering the rest of the toolchain pairs against.
    const outDir = path.join(job, "png");
    await fs.mkdir(outDir, { recursive: true });
    await run(
      process.env.PDFTOPPM_BIN || "pdftoppm",
      ["-png", "-r", String(Number(req.body.dpi) || 110), pdf, path.join(outDir, "slide")],
      { cwd: job, timeout: TIMEOUT_MS },
    );

    // Same header contract as /slides — the gateway meters both routes off it.
    const pngs = (await fs.readdir(outDir)).sort();
    res.set("Content-Type", "application/zip");
    res.set("Content-Disposition", 'attachment; filename="deck.zip"');
    res.set("X-Slide-Count", String(pngs.length));
    const zip = archiver("zip", { zlib: { level: 6 } });
    zip.on("error", (e) => {
      throw e;
    });
    zip.pipe(res);
    zip.file(pdf, { name: "deck.pdf" });
    for (const png of pngs) {
      zip.file(path.join(outDir, png), { name: `slides/${png}` });
    }
    await zip.finalize();
  } catch (e) {
    if (!res.headersSent) {
      res.status(500).json({
        error: "pptx render failed",
        detail: String(e.stderr || e.message || e).slice(0, 500),
      });
    }
  } finally {
    fs.rm(job, { recursive: true, force: true }).catch(() => {});
    // If we failed before the rename, multer's temp copy is still there.
    if (req.file?.path) fs.rm(req.file.path, { force: true }).catch(() => {});
  }
});

// ── doc-render (dev-plan/69) ─────────────────────────────────────────────
//
// Office documents for the engine's cloud-side tools: LibreOffice conversion,
// poppler text/raster, tesseract OCR and Chromium HTML→PDF. Every 2xx sets
// X-Page-Count AND X-Slide-Count — the gateway meters on the latter.

const uploadDoc = multer({
  storage: multer.diskStorage({
    destination: (_req, _file, cb) => cb(null, os.tmpdir()),
    filename: (_req, file, cb) =>
      cb(null, "up-" + crypto.randomBytes(8).toString("hex") + path.extname(safeName(file.originalname))),
  }),
  // Thai filenames arrive as UTF-8; multer's latin1 default mangles them.
  defParamCharset: "utf8",
  limits: { fileSize: 200 * 1024 * 1024, files: 61 },
});

const MAX_JOBS = Number(process.env.DOC_RENDER_CONCURRENCY) || 2;
let activeJobs = 0;
const waiting = [];

// LibreOffice, Chromium and tesseract each want a core and several hundred MB;
// unbounded fan-out on one pod is an OOM, so excess jobs queue here and the
// HPA adds pods off the CPU this pins.
async function withSlot(fn) {
  if (activeJobs >= MAX_JOBS) await new Promise((r) => waiting.push(r));
  activeJobs++;
  try {
    return await fn();
  } finally {
    activeJobs--;
    waiting.shift()?.();
  }
}

class HttpError extends Error {
  constructor(status, message, detail) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

const allUploads = (req) =>
  req.file ? [req.file] : Object.values(req.files || {}).flat();

// One job = one temp dir, removed in finally along with any multer temp file
// a failed request left behind.
function docRoute(label, handler) {
  return async (req, res) => {
    const job = path.join(os.tmpdir(), "doc-" + crypto.randomBytes(8).toString("hex"));
    try {
      await fs.mkdir(job, { recursive: true });
      await withSlot(() => handler(req, res, job));
    } catch (e) {
      if (res.headersSent) return;
      if (e instanceof HttpError) {
        return res.status(e.status).json(e.detail ? { error: e.message, detail: e.detail } : { error: e.message });
      }
      res.status(500).json({
        error: `${label} failed`,
        detail: String(e.stderr || e.message || e).slice(0, 500),
      });
    } finally {
      fs.rm(job, { recursive: true, force: true }).catch(() => {});
      for (const f of allUploads(req)) fs.rm(f.path, { force: true }).catch(() => {});
    }
  };
}

function requireFile(req) {
  const f = req.file || req.files?.file?.[0];
  if (!f) throw new HttpError(400, "missing 'file' field");
  return f;
}

// Move the upload into the job dir under a safe name with the given extension.
async function placeUpload(f, job, ext) {
  const stem = safeName(f.originalname || "input").replace(/\.[^.]+$/, "") || "input";
  const dst = path.join(job, `${stem}.${ext}`);
  await fs.rename(f.path, dst);
  return dst;
}

const extOf = (f) => path.extname(String(f.originalname || "")).slice(1).toLowerCase();

function intField(req, name, dflt, min, max) {
  const raw = req.body?.[name];
  if (raw === undefined || raw === "") return dflt;
  const n = Number(raw);
  if (!Number.isInteger(n) || n < min || n > max) {
    throw new HttpError(400, `'${name}' must be an integer in ${min}..${max}`);
  }
  return n;
}

// first/last are 1-based inclusive. An omitted `last` is clamped to the cap;
// an explicit range wider than the cap is refused rather than silently cut.
function pageRange(req, pageCount, cap) {
  const first = intField(req, "first", 1, 1, 1e6);
  const explicit = req.body?.last !== undefined && req.body.last !== "";
  let last = intField(req, "last", first + cap - 1, 1, 1e6);
  if (first > pageCount) throw new HttpError(400, `'first' is ${first} but the document has ${pageCount} pages`);
  if (last < first) throw new HttpError(400, "'last' is before 'first'");
  if (explicit && last - first + 1 > cap) throw new HttpError(400, `at most ${cap} pages per call`);
  last = Math.min(last, pageCount);
  return { first, last };
}

const POPPLER = {
  pdfinfo: process.env.PDFINFO_BIN || "pdfinfo",
  pdftotext: process.env.PDFTOTEXT_BIN || "pdftotext",
  pdftoppm: process.env.PDFTOPPM_BIN || "pdftoppm",
};

async function pdfPageCount(file) {
  let out;
  try {
    ({ stdout: out } = await run(POPPLER.pdfinfo, [file], { timeout: TIMEOUT_MS }));
  } catch (e) {
    throw new HttpError(422, "not a readable pdf", String(e.stderr || e.message).slice(0, 300));
  }
  const m = /^Pages:\s+(\d+)/m.exec(out);
  if (!m) throw new HttpError(422, "not a readable pdf", "pdfinfo reported no page count");
  return Number(m[1]);
}

async function isPdf(file) {
  const fh = await fs.open(file, "r");
  try {
    const buf = Buffer.alloc(5);
    await fh.read(buf, 0, 5, 0);
    return buf.toString("latin1") === "%PDF-";
  } finally {
    await fh.close();
  }
}

async function requirePdf(req, job) {
  const f = requireFile(req);
  const src = await placeUpload(f, job, "pdf");
  if (!(await isPdf(src))) throw new HttpError(400, "'file' is not a pdf");
  return src;
}

function setCounts(res, n) {
  res.set("X-Page-Count", String(n));
  res.set("X-Slide-Count", String(n));
}

// pdftoppm names pages <prefix>-N with N zero-padded to the page-count width.
async function rasterise(pdf, outDir, dpi, first, last) {
  await fs.mkdir(outDir, { recursive: true });
  await run(
    POPPLER.pdftoppm,
    ["-png", "-r", String(dpi), "-f", String(first), "-l", String(last), pdf, path.join(outDir, "p")],
    { timeout: TIMEOUT_MS },
  );
  return (await fs.readdir(outDir))
    .map((f) => ({ f, n: Number(/-(\d+)\.png$/.exec(f)?.[1]) }))
    .filter((p) => p.n)
    .sort((a, b) => a.n - b.n)
    .map((p) => ({ n: p.n, file: path.join(outDir, p.f) }));
}

const WRITER_IN = ["doc", "docx", "odt", "rtf", "txt", "html", "htm"];
const CALC_IN = ["xls", "xlsx", "ods", "csv"];
const IMPRESS_IN = ["ppt", "pptx", "odp"];

// Export filter per (component, target). A pair missing here is refused —
// LibreOffice would otherwise exit 0 having written nothing (xlsx→pptx).
const CONVERT_FILTERS = {
  writer: {
    pdf: "pdf:writer_pdf_Export",
    docx: "docx:MS Word 2007 XML",
    odt: "odt:writer8",
    html: "html:HTML (StarWriter)",
    txt: "txt:Text (encoded):UTF8",
  },
  calc: {
    pdf: "pdf:calc_pdf_Export",
    xlsx: "xlsx:Calc MS Excel 2007 XML",
    ods: "ods:calc8",
    html: "html:HTML (StarCalc)",
    // 44,34,76 = comma, double quote, UTF-8 — the default is the system
    // charset, which turns Thai into '?'.
    csv: "csv:Text - txt - csv (StarCalc):44,34,76",
  },
  impress: {
    pdf: "pdf:impress_pdf_Export",
    pptx: "pptx:Impress MS PowerPoint 2007 XML",
    odp: "odp:impress8",
  },
};

// Import filters for the text-ish inputs whose defaults guess wrong: HTML
// opens in Writer/Web (no docx/odt export) and txt/csv in the system charset.
const CONVERT_INFILTERS = {
  html: "HTML (StarWriter)",
  htm: "HTML (StarWriter)",
  txt: "Text (encoded):UTF8",
  csv: "CSV:44,34,76",
};

const CONTENT_TYPES = {
  pdf: "application/pdf",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  pptx: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  odt: "application/vnd.oasis.opendocument.text",
  ods: "application/vnd.oasis.opendocument.spreadsheet",
  odp: "application/vnd.oasis.opendocument.presentation",
  html: "text/html; charset=utf-8",
  txt: "text/plain; charset=utf-8",
  csv: "text/csv; charset=utf-8",
};

app.post("/convert", auth, uploadDoc.single("file"), docRoute("convert", async (req, res, job) => {
  const f = requireFile(req);
  const inExt = extOf(f);
  const component = WRITER_IN.includes(inExt) ? "writer"
    : CALC_IN.includes(inExt) ? "calc"
    : IMPRESS_IN.includes(inExt) ? "impress" : null;
  if (!component) throw new HttpError(400, `unsupported input extension '.${inExt}'`);
  const to = String(req.body?.to || "").toLowerCase();
  if (!CONTENT_TYPES[to]) throw new HttpError(400, `unsupported 'to' value '${to}'`);
  const filter = CONVERT_FILTERS[component][to];
  if (!filter) throw new HttpError(400, `cannot convert .${inExt} to ${to}`);

  const src = await placeUpload(f, job, inExt);
  const outDir = path.join(job, "out");
  await fs.mkdir(outDir);
  const args = [
    `-env:UserInstallation=file://${path.join(job, "lo-profile")}`,
    "--headless", "--norestore",
  ];
  if (CONVERT_INFILTERS[inExt]) args.push(`--infilter=${CONVERT_INFILTERS[inExt]}`);
  args.push("--convert-to", filter, "--outdir", outDir, src);
  await run(process.env.SOFFICE_BIN || "soffice", args, { cwd: job, timeout: TIMEOUT_MS });

  const produced = (await fs.readdir(outDir)).filter((n) => n.toLowerCase().endsWith(`.${to}`));
  if (produced.length !== 1) {
    throw new HttpError(422, "conversion produced no output", `libreoffice could not convert '${safeName(f.originalname)}' to ${to}`);
  }
  const out = path.join(outDir, produced[0]);
  const pages = to === "pdf" ? await pdfPageCount(out) : 1;

  const stem = String(f.originalname || "document").replace(/\.[^.]+$/, "") || "document";
  const asciiStem = safeName(stem) || "document";
  res.set("Content-Type", CONTENT_TYPES[to]);
  res.set(
    "Content-Disposition",
    `attachment; filename="${asciiStem}.${to}"; filename*=UTF-8''${encodeURIComponent(`${path.basename(stem)}.${to}`)}`,
  );
  setCounts(res, pages);
  res.send(await fs.readFile(out));
}));

app.post("/pdf/text", auth, uploadDoc.single("file"), docRoute("pdf text", async (req, res, job) => {
  const src = await requirePdf(req, job);
  const mode = String(req.body?.mode || "layout");
  if (mode !== "layout" && mode !== "raw") throw new HttpError(400, "'mode' must be layout or raw");
  const pageCount = await pdfPageCount(src);
  const { first, last } = pageRange(req, pageCount, 500);
  const { stdout } = await run(
    POPPLER.pdftotext,
    [`-${mode}`, "-enc", "UTF-8", "-f", String(first), "-l", String(last), src, "-"],
    { timeout: TIMEOUT_MS, maxBuffer: 256 * 1024 * 1024 },
  );
  // pdftotext ends every page with a form feed, blank pages included.
  const texts = stdout.split("\f");
  const pages = [];
  for (let n = first; n <= last; n++) pages.push({ n, text: texts[n - first] ?? "" });
  setCounts(res, pages.length);
  res.json({ page_count: pageCount, pages });
}));

app.post("/pdf/pages", auth, uploadDoc.single("file"), docRoute("pdf pages", async (req, res, job) => {
  const src = await requirePdf(req, job);
  const dpi = intField(req, "dpi", 150, 36, 300);
  const pageCount = await pdfPageCount(src);
  const { first, last } = pageRange(req, pageCount, 20);
  const pngs = await rasterise(src, path.join(job, "png"), dpi, first, last);
  const pages = [];
  for (const p of pngs) pages.push({ n: p.n, png_base64: (await fs.readFile(p.file)).toString("base64") });
  setCounts(res, pages.length);
  res.json({ page_count: pageCount, pages });
}));

let ocrLangs;
async function installedOcrLangs() {
  if (!ocrLangs) {
    const { stdout } = await run(process.env.TESSERACT_BIN || "tesseract", ["--list-langs"], { timeout: 30000 });
    ocrLangs = new Set(stdout.split("\n").slice(1).map((l) => l.trim()).filter((l) => /^[A-Za-z_]+$/.test(l)));
  }
  return ocrLangs;
}

const OCR_IMAGE_EXT = { png: "png", jpg: "jpg", jpeg: "jpg", tif: "tif", tiff: "tif", webp: "webp" };

// Mean of the word confidences in tesseract's TSV (level 5 rows); -1 marks
// non-word rows.
function meanConfidence(tsv) {
  let sum = 0;
  let count = 0;
  for (const line of tsv.split("\n").slice(1)) {
    const cols = line.split("\t");
    if (cols.length < 12 || cols[0] !== "5") continue;
    const conf = Number(cols[10]);
    if (conf < 0 || !cols[11].trim()) continue;
    sum += conf;
    count++;
  }
  return count ? Math.round((sum / count) * 10) / 10 : 0;
}

app.post("/ocr", auth, uploadDoc.single("file"), docRoute("ocr", async (req, res, job) => {
  const f = requireFile(req);
  const lang = String(req.body?.lang || "tha+eng");
  const installed = await installedOcrLangs();
  const langs = lang.split("+");
  if (!langs.every((l) => installed.has(l))) {
    throw new HttpError(400, `unsupported 'lang' '${lang}'`, `installed: ${[...installed].join(", ")}`);
  }
  const dpi = intField(req, "dpi", 300, 72, 600);

  const ext = extOf(f);
  let pageCount;
  let images;
  if (ext === "pdf") {
    const src = await placeUpload(f, job, "pdf");
    if (!(await isPdf(src))) throw new HttpError(400, "'file' is not a pdf");
    pageCount = await pdfPageCount(src);
    const { first, last } = pageRange(req, pageCount, 20);
    images = await rasterise(src, path.join(job, "png"), dpi, first, last);
  } else if (OCR_IMAGE_EXT[ext]) {
    pageCount = 1;
    pageRange(req, 1, 20);
    images = [{ n: 1, file: await placeUpload(f, job, OCR_IMAGE_EXT[ext]) }];
  } else {
    throw new HttpError(400, `unsupported input extension '.${ext}'`);
  }

  const pages = [];
  for (const img of images) {
    const base = path.join(job, `ocr-${img.n}`);
    // One pass writes both: .txt keeps tesseract's line breaks, .tsv carries
    // the per-word confidences.
    await run(
      process.env.TESSERACT_BIN || "tesseract",
      [img.file, base, "-l", lang, "--dpi", String(dpi), "txt", "tsv"],
      // One thread per job: the concurrency limit already spreads jobs over cores.
      { timeout: TIMEOUT_MS, env: { ...process.env, OMP_THREAD_LIMIT: "1" } },
    );
    const text = await fs.readFile(`${base}.txt`, "utf8");
    const tsv = await fs.readFile(`${base}.tsv`, "utf8");
    pages.push({ n: img.n, text: text.replace(/\f$/, ""), confidence: meanConfidence(tsv) });
  }
  setCounts(res, pages.length);
  res.json({ page_count: pageCount, pages });
}));

const PAPER = { a4: "A4", letter: "Letter" };

// Ahead of the author's own CSS, so a document that sets @page itself wins.
function withPageSize(html, size) {
  const rule = `<style>@page{size:${size}}</style>`;
  const head = /<head[^>]*>/i.exec(html);
  if (head) return html.slice(0, head.index + head[0].length) + rule + html.slice(head.index + head[0].length);
  const doctype = /^\s*<!doctype[^>]*>/i.exec(html);
  if (doctype) return doctype[0] + rule + html.slice(doctype[0].length);
  return rule + html;
}

// The page is untrusted. It is served from a loopback server rooted at the
// job dir rather than opened as file:// — a file:// page can embed
// /proc/self/environ into the PDF it hands back — and every other host goes
// to a dead proxy, so it cannot reach the cluster network either.
app.post(
  "/html-to-pdf",
  auth,
  uploadDoc.fields([{ name: "file", maxCount: 1 }, { name: "assets" }, { name: "assets[]" }]),
  docRoute("html to pdf", async (req, res, job) => {
    const f = requireFile(req);
    if (!["html", "htm"].includes(extOf(f))) throw new HttpError(400, "'file' must be .html");
    const formatRaw = String(req.body?.format || "A4").toLowerCase();
    if (!PAPER[formatRaw]) throw new HttpError(400, "'format' must be A4 or Letter");
    const landscape = ["1", "true", "yes", "on"].includes(String(req.body?.landscape || "").toLowerCase());

    const site = path.join(job, "site");
    await fs.mkdir(site);
    for (const a of [...(req.files?.assets || []), ...(req.files?.["assets[]"] || [])]) {
      await fs.rename(a.path, path.join(site, safeName(a.originalname)));
    }
    // latin1 round-trips every byte, so a TIS-620 page keeps its own charset.
    const html = await fs.readFile(f.path, "latin1");
    await fs.writeFile(
      path.join(site, "__index.html"),
      withPageSize(html, `${PAPER[formatRaw]}${landscape ? " landscape" : ""}`),
      "latin1",
    );

    const server = await new Promise((resolve, reject) => {
      const s = express().use(express.static(site, { dotfiles: "deny" })).listen(0, "127.0.0.1");
      s.once("listening", () => resolve(s));
      s.once("error", reject);
    });
    try {
      const origin = `127.0.0.1:${server.address().port}`;
      const pdf = path.join(job, "out.pdf");
      await run(
        process.env.CHROME_PATH || "chromium",
        [
          "--headless=new",
          "--no-sandbox",
          "--disable-gpu",
          "--no-first-run",
          "--disable-extensions",
          `--user-data-dir=${path.join(job, "chrome-profile")}`,
          // Loopback is implicitly bypassed, so only the job server answers;
          // the resolver rule also refuses DNS should a proxy bypass exist.
          "--proxy-server=127.0.0.1:9",
          "--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1",
          "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
          "--no-pdf-header-footer",
          "--virtual-time-budget=15000",
          `--print-to-pdf=${pdf}`,
          `http://${origin}/__index.html`,
        ],
        { cwd: job, timeout: TIMEOUT_MS, env: { ...process.env, HOME: job } },
      );
      if (!fss.existsSync(pdf)) throw new HttpError(422, "chromium produced no pdf");
      const pages = await pdfPageCount(pdf);
      res.set("Content-Type", "application/pdf");
      res.set("Content-Disposition", 'attachment; filename="document.pdf"');
      setCounts(res, pages);
      res.send(await fs.readFile(pdf));
    } finally {
      server.close();
    }
  }),
);

// Multer rejects a malformed upload (unexpected field, too many files, a part
// over the size limit) by throwing BEFORE any route handler runs, so the
// per-route try/catch never sees it and Express answers with an HTML 500. The
// caller is the engine's RenderSlides relay, which parses JSON — give it a
// 400 that names the field instead of an opaque server error.
app.use((err, _req, res, next) => {
  if (res.headersSent) return next(err);
  if (err instanceof multer.MulterError) {
    return res.status(400).json({
      error: "bad upload",
      detail: `${err.code}${err.field ? ` on field '${err.field}'` : ""}`,
    });
  }
  console.error(err);
  res.status(500).json({ error: "internal error" });
});

app.listen(PORT, () => console.log(`slide-render listening on :${PORT}`));
