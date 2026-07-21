// slide-render — Marp + Chromium slide rendering microservice.
//
// POST /slides   (multipart)  markdown=<marp md>  [theme=thai-tech]  [images=<file>…]
//   → 200 application/zip  { deck.pdf, slides/slide-01.png … }
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
const upload = multer({ limits: { fileSize: 25 * 1024 * 1024, files: 60 } });

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

    res.set("Content-Type", "application/zip");
    res.set("Content-Disposition", 'attachment; filename="deck.zip"');
    const zip = archiver("zip", { zlib: { level: 6 } });
    zip.on("error", (e) => { throw e; });
    zip.pipe(res);
    zip.file(path.join(job, "deck.pdf"), { name: "deck.pdf" });
    for (const png of (await fs.readdir(outDir)).sort()) {
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

app.listen(PORT, () => console.log(`slide-render listening on :${PORT}`));
