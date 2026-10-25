# slide-render — Marp + Chromium + Thai fonts. One image; not in the engine base.
FROM node:22.23.4-bookworm-slim AS runtime

# Chromium (Marp renders PDF + PNG via it) + Thai fonts (fallback to @font-face in theme)
# libreoffice-impress + poppler-utils back the /pptx endpoint (view an
# existing deck): Impress converts pptx→pdf, pdftoppm rasterises. Only the
# Impress component was installed until doc-render (dev-plan/69): /convert
# needs Writer and Calc too. Base/Draw/Math stay out — the full libreoffice
# metapackage pulls them and Java for nothing this service does.
# tesseract-ocr + tha/eng traineddata back /ocr.
RUN apt-get update && apt-get install -y --no-install-recommends \
      chromium fonts-thai-tlwg fonts-noto-core fontconfig ca-certificates tini \
      libreoffice-impress libreoffice-writer libreoffice-calc libreoffice-core poppler-utils \
      tesseract-ocr tesseract-ocr-tha tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Marp uses the system Chromium (skip its bundled download).
# Chromium for Marp and /html-to-pdf never reaches the network: loopback is
# implicitly bypassed by the proxy, and the resolver rule refuses DNS.
RUN printf '#!/bin/sh\nexec /usr/bin/chromium --proxy-server=127.0.0.1:9 --host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE 127.0.0.1" --force-webrtc-ip-handling-policy=disable_non_proxied_udp "$@"\n' > /usr/local/bin/chromium-offline \
    && chmod 755 /usr/local/bin/chromium-offline
ENV CHROME_PATH=/usr/local/bin/chromium-offline \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    MARP_BIN=marp \
    NODE_ENV=production

WORKDIR /app
# Copy the lockfile and install from it. `npm install` without the lock
# re-resolves every transitive dependency at build time, so two builds of the
# same commit could ship different code — and the audited versions in
# package-lock.json would never actually reach the image.
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm install -g @marp-team/marp-cli@4

COPY server.js ./
COPY themes ./themes
# themes/fonts/*.ttf also installed system-wide (fc fallback beside the @font-face)
RUN cp themes/fonts/*.ttf /usr/share/fonts/truetype/ && fc-cache -f

# Run as a non-root user. Chromium still needs --no-sandbox in a container
# without SYS_ADMIN (below), so this is not the setuid sandbox coming back —
# it is the second half of the defence: a deck that escapes the renderer lands
# as an unprivileged user with no write access to the app or the system.
# The home directory has to be real and writable: fontconfig caches there on
# first render, and LibreOffice falls back to it if a job's -env profile fails.
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin render \
    && chown -R render:render /app
USER render
ENV HOME=/home/render

EXPOSE 8080
# marp-cli reads these: CHROME_NO_SANDBOX makes it launch Chromium with
# --no-sandbox (required in a container — isolation comes from the container +
# no-network render, see README security note); CHROME_DISABLE_GPU drops the GPU
# in headless. Give the pod a larger /dev/shm via an emptyDir (see the k8s
# manifest) so Chromium doesn't OOM on the default 64MB.
ENV CHROME_NO_SANDBOX=1 \
    CHROME_DISABLE_GPU=1
# tini reaps zombie Chromium procs.
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["node","server.js"]

# Every route against the real binaries, Thai included (convert round-trip,
# HTML→PDF→text, tha OCR). A failure fails the build, so a broken image is
# never pushed. The final stage copies the marker to force this stage to run;
# the test files themselves stay out of the shipped image.
FROM runtime AS smoke
COPY test ./test
RUN SMOKE_SLIDES=1 node test/smoke.js && touch /tmp/smoke-passed

FROM runtime
COPY --from=smoke /tmp/smoke-passed /app/.smoke-passed
