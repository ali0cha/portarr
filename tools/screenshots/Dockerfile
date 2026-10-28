# Throwaway image used only to regenerate the README screenshots: headless Chromium driven by Playwright,
# plus pngquant to keep the images small. Not part of the Portarr image.
FROM python:3.12-slim
RUN pip install --no-cache-dir playwright \
 && playwright install --with-deps chromium \
 && apt-get install -y --no-install-recommends pngquant \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /work
