# slide-render — Marp + Chromium + Thai fonts. One image; not in the engine base.
FROM node:20-bookworm-slim

# Chromium (Marp renders PDF + PNG via it) + Thai fonts (fallback to @font-face in theme)
# libreoffice-impress + poppler-utils back the /pptx endpoint (view an
# existing deck): Impress converts pptx→pdf, pdftoppm rasterises. Only the
# Impress component is installed — the full libreoffice metapackage pulls
# Writer/Calc/Base and roughly triples the layer for no gain here.
RUN apt-get update && apt-get install -y --no-install-recommends \
      chromium fonts-thai-tlwg fonts-noto-core fontconfig ca-certificates tini \
      libreoffice-impress libreoffice-core poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Marp uses the system Chromium (skip its bundled download).
ENV CHROME_PATH=/usr/bin/chromium \
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
