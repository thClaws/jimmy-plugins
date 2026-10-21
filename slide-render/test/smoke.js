// End-to-end smoke test for every route, run against a real server with the
// real binaries — the Dockerfile runs it at build time, so an image that
// cannot convert or OCR Thai never gets pushed.
//
//   node test/smoke.js                     # spawns server.js on a free port
//   SMOKE_BASE=http://host:8080 node test/smoke.js
//   SMOKE_OCR_LANG=eng                     # hosts without tha traineddata
//   SMOKE_SLIDES=1                         # also render a Marp deck (needs marp)

const { spawn } = require("child_process");
const path = require("path");
const assert = require("assert/strict");

const OCR_LANG = process.env.SMOKE_OCR_LANG || "tha+eng";
const THAI = "ประชุม";

const HTML = `<!doctype html>
<html><head><meta charset="utf-8"><link rel="stylesheet" href="style.css"></head>
<body>
<h1>รายงานการประชุม ประจำเดือนตุลาคม</h1>
<h1>Monthly Meeting Report</h1>
<p id="net">NET</p>
<script>
const mark = (t) => document.getElementById("net").append(" " + t);
fetch("http://example.com/", { mode: "no-cors" }).then(() => mark("NETOPEN"), () => mark("NETBLOCKED"));
fetch("http://1.1.1.1/", { mode: "no-cors" }).then(() => mark("IPOPEN"), () => mark("IPBLOCKED"));
fetch("file:///etc/hostname").then(() => mark("FILEOPEN"), () => mark("FILEBLOCKED"));
</script>
</body></html>`;
const CSS = `body{font-size:28px} h1{font-size:44px} body::after{content:"ASSETOK"}`;
const CSV = "ชื่อ,จำนวน\nประชุมใหญ่,3\nสมชาย,42\n";

let failures = 0;
async function check(name, fn) {
  try {
    await fn();
    console.log(`ok   ${name}`);
  } catch (e) {
    failures++;
    console.log(`FAIL ${name}\n     ${String(e.stack || e).split("\n").slice(0, 4).join("\n     ")}`);
  }
}

function form(fields) {
  const fd = new FormData();
  for (const [k, v] of Object.entries(fields)) {
    for (const item of Array.isArray(v) ? v : [v]) {
      if (item && typeof item === "object" && "data" in item) {
        fd.append(k, new Blob([item.data]), item.name);
      } else {
        fd.append(k, String(item));
      }
    }
  }
  return fd;
}

async function post(base, route, fields) {
  const r = await fetch(base + route, { method: "POST", body: form(fields) });
  const buf = Buffer.from(await r.arrayBuffer());
  return { r, buf, json: () => JSON.parse(buf.toString("utf8")) };
}

function counted(r) {
  assert.equal(r.status, 200);
  const pages = r.headers.get("x-page-count");
  assert.ok(pages && Number(pages) >= 1, `X-Page-Count=${pages}`);
  assert.equal(r.headers.get("x-slide-count"), pages);
}

async function waitHealthy(base) {
  for (let i = 0; i < 600; i++) {
    try {
      if ((await fetch(base + "/healthz")).ok) return;
    } catch {}
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error("server never became healthy");
}

async function main() {
  let base = process.env.SMOKE_BASE;
  let child;
  if (!base) {
    const port = 20000 + Math.floor(Math.random() * 20000);
    child = spawn(process.execPath, [path.join(__dirname, "..", "server.js")], {
      env: { ...process.env, PORT: String(port), SLIDE_RENDER_TOKEN: "" },
      stdio: ["ignore", "inherit", "inherit"],
    });
    base = `http://127.0.0.1:${port}`;
  }
  try {
    await waitHealthy(base);
    await run(base);
  } finally {
    child?.kill();
  }
  if (failures) {
    console.log(`${failures} check(s) failed`);
    process.exit(1);
  }
  console.log("smoke: all checks passed");
}

async function run(base) {
  const htmlFile = { data: HTML, name: "รายงาน.html" };
  let pdf;
  let xlsx;

  await check("healthz", async () => {
    const j = await (await fetch(base + "/healthz")).json();
    assert.equal(j.ok, true);
  });

  await check("html-to-pdf renders Thai with assets, no network, no file://", async () => {
    const { r, buf } = await post(base, "/html-to-pdf", {
      file: htmlFile,
      "assets[]": { data: CSS, name: "style.css" },
      format: "A4",
    });
    counted(r);
    assert.equal(r.headers.get("content-type"), "application/pdf");
    assert.equal(buf.subarray(0, 5).toString(), "%PDF-");
    pdf = buf;
  });

  await check("pdf/text extracts Thai", async () => {
    const { r, json } = await post(base, "/pdf/text", { file: { data: pdf, name: "a.pdf" } });
    counted(r);
    const j = json();
    assert.ok(j.page_count >= 1);
    assert.equal(j.pages[0].n, 1);
    const text = j.pages.map((p) => p.text).join("\n");
    assert.ok(text.includes(THAI), `no ${THAI} in: ${text.slice(0, 200)}`);
    assert.ok(text.includes("ASSETOK"), "relative asset was not loaded");
    assert.ok(text.includes("NETBLOCKED") && !text.includes("NETOPEN"), "page reached the network");
    assert.ok(text.includes("IPBLOCKED") && !text.includes("IPOPEN"), "page reached an IP literal");
    assert.ok(text.includes("FILEBLOCKED") && !text.includes("FILEOPEN"), "page read file://");
  });

  await check("pdf/text raw mode", async () => {
    const { r, json } = await post(base, "/pdf/text", { file: { data: pdf, name: "a.pdf" }, mode: "raw", first: 1, last: 1 });
    counted(r);
    assert.ok(json().pages[0].text.includes(THAI));
  });

  await check("pdf/pages rasterises to PNG", async () => {
    const { r, json } = await post(base, "/pdf/pages", { file: { data: pdf, name: "a.pdf" }, dpi: 72 });
    counted(r);
    const png = Buffer.from(json().pages[0].png_base64, "base64");
    assert.equal(png.subarray(1, 4).toString(), "PNG");
  });

  await check(`ocr (${OCR_LANG}) on a pdf`, async () => {
    const { r, json } = await post(base, "/ocr", { file: { data: pdf, name: "a.pdf" }, lang: OCR_LANG, first: 1, last: 1 });
    counted(r);
    const p = json().pages[0];
    const want = OCR_LANG.includes("tha") ? THAI : "Meeting";
    assert.ok(p.text.replace(/ /g, "").includes(want), `no ${want} in: ${p.text.slice(0, 200)}`);
    assert.ok(p.confidence > 50, `confidence ${p.confidence}`);
  });

  await check("ocr on a png", async () => {
    const pages = await post(base, "/pdf/pages", { file: { data: pdf, name: "a.pdf" }, dpi: 200 });
    const png = Buffer.from(pages.json().pages[0].png_base64, "base64");
    const { r, json } = await post(base, "/ocr", { file: { data: png, name: "scan.png" }, lang: OCR_LANG, dpi: 200 });
    counted(r);
    assert.equal(json().page_count, 1);
    assert.ok(json().pages[0].text.includes("Meeting"));
  });

  await check("convert csv (Thai) → xlsx", async () => {
    const { r, buf } = await post(base, "/convert", { file: { data: CSV, name: "ตาราง.csv" }, to: "xlsx" });
    counted(r);
    assert.match(r.headers.get("content-disposition"), /filename="[^"]+\.xlsx"; filename\*=UTF-8''/);
    assert.equal(buf.subarray(0, 2).toString(), "PK");
    xlsx = buf;
  });

  await check("convert xlsx → csv round-trips Thai", async () => {
    const { r, buf } = await post(base, "/convert", { file: { data: xlsx, name: "t.xlsx" }, to: "csv" });
    counted(r);
    assert.equal(buf.toString("utf8").replace(/\r\n/g, "\n").trim(), CSV.trim());
  });

  await check("convert html → docx → pdf keeps Thai", async () => {
    const docx = await post(base, "/convert", { file: htmlFile, to: "docx" });
    counted(docx.r);
    const out = await post(base, "/convert", { file: { data: docx.buf, name: "r.docx" }, to: "pdf" });
    counted(out.r);
    assert.equal(out.r.headers.get("content-type"), "application/pdf");
    const t = await post(base, "/pdf/text", { file: { data: out.buf, name: "r.pdf" } });
    assert.ok(t.json().pages.map((p) => p.text).join("").includes(THAI));
  });

  await check("convert txt (Thai) → txt stays UTF-8", async () => {
    const { r, buf } = await post(base, "/convert", { file: { data: "บันทึกการประชุม\n", name: "n.txt" }, to: "odt" });
    counted(r);
    const back = await post(base, "/convert", { file: { data: buf, name: "n.odt" }, to: "txt" });
    counted(back.r);
    assert.ok(back.buf.toString("utf8").includes("บันทึกการประชุม"));
  });

  const refused = async (name, route, fields, status = 400) =>
    check(name, async () => {
      const { r, json } = await post(base, route, fields);
      assert.equal(r.status, status, `got ${r.status}`);
      assert.ok(json().error);
    });
  await refused("convert refuses xlsx → pptx", "/convert", { file: { data: "x", name: "t.xlsx" }, to: "pptx" });
  await refused("convert refuses unknown input", "/convert", { file: { data: "x", name: "a.exe" }, to: "pdf" });
  await refused("convert refuses unknown target", "/convert", { file: { data: "x", name: "a.docx" }, to: "exe" });
  await refused("pdf/text refuses a non-pdf", "/pdf/text", { file: { data: "hello", name: "a.pdf" } });
  await refused("pdf/pages refuses > 20 pages", "/pdf/pages", { file: { data: pdf, name: "a.pdf" }, first: 1, last: 21 });
  await refused("pdf/pages refuses dpi > 300", "/pdf/pages", { file: { data: pdf, name: "a.pdf" }, dpi: 301 });
  await refused("pdf/text refuses first past the end", "/pdf/text", { file: { data: pdf, name: "a.pdf" }, first: 99 });
  await refused("ocr refuses an uninstalled lang", "/ocr", { file: { data: pdf, name: "a.pdf" }, lang: "zzz" });
  await refused("ocr refuses lang injection", "/ocr", { file: { data: pdf, name: "a.pdf" }, lang: "eng --psm 0" });
  await refused("html-to-pdf refuses a non-html", "/html-to-pdf", { file: { data: "x", name: "a.txt" } });
  await refused("missing file", "/convert", { to: "pdf" });

  if (process.env.SMOKE_SLIDES) {
    await check("slides still renders a Marp deck", async () => {
      const { r, buf } = await post(base, "/slides", { markdown: `---\nmarp: true\n---\n\n# ${THAI}\n` });
      assert.equal(r.status, 200);
      assert.equal(r.headers.get("x-slide-count"), "1");
      assert.equal(buf.subarray(0, 2).toString(), "PK");
    });
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
