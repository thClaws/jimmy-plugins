// slide-render — Marp + Chromium slide rendering microservice.
//
// POST /slides   (multipart)  markdown=<marp md>  [theme=thai-tech]  [images=<file>…]
//   → 200 application/zip  { deck.pdf, slides/slide-01.png … }
// POST /pptx     (multipart)  file=<.pptx>
//   → 200 application/zip  { deck.pdf, slides/slide-01.png … }   (same shape)
//
// Both render routes return `X-Slide-Count: <n>` — the number of rendered
// pages. The gateway bills per page off that header, so it must be set
// before the zip starts streaming.
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
