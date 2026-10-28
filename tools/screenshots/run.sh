#!/bin/sh
# Regenerates docs/screenshots/{en,fr}/*.png: the real app + fake Radarr/Sonarr/Lidarr/Whisparr/Prowlarr servers
# + headless Chromium, all in throwaway containers. Needs Docker and Internet (the TRaSH catalogue is downloaded).
# Usage: ./tools/screenshots/run.sh [en] [fr]   (both by default)
set -e
cd "$(dirname "$0")/../.."
docker image inspect portarr-shots >/dev/null 2>&1 || docker build -q -t portarr-shots tools/screenshots

for lang in ${@:-en fr}; do
  docker rm -f portarr-shots-demo >/dev/null 2>&1 || true
  # fresh servers for every language: the "done" screen really applies an import.
  # PORTARR_UPDATE_CHECK=0 keeps the "new version" link out of the pictures.
  docker run -d --rm --name portarr-shots-demo --network host -v "$PWD":/src:ro -v portarr-pip:/root/.cache/pip -w /src \
    -e PYTHONDONTWRITEBYTECODE=1 -e CONFIG_DIR=/tmp/cfg -e PORTARR_UPDATE_CHECK=0 python:3.12-slim sh -c '
      pip install -q -r requirements.txt 2>&1 | grep -v -e WARNING -e notice
      python -m tests.fake_arr radarr-a:7001 radarr-b:7002 sonarr-a:7003 sonarr-b:7004 lidarr-a:7005 lidarr-b:7006 \
        whisparr-a:7007 whisparr-b:7008 prowlarr-a:7009 prowlarr-b:7010 &
      exec python -m app' >/dev/null
  for i in $(seq 1 90); do curl -sf localhost:8765/healthz >/dev/null && break; sleep 1; done
  mkdir -p "docs/screenshots/$lang"
  docker run --rm --network host -v "$PWD/tools/screenshots":/work/tools:ro -v "$PWD/docs/screenshots":/out -e OUT=/out portarr-shots sh -c "
    python /work/tools/shots.py $lang
    pngquant --quality=65-90 --speed 1 --force --ext .png /out/$lang/*.png
    chown -R $(id -u):$(id -g) /out"
  docker rm -f portarr-shots-demo >/dev/null
done
echo "done: docs/screenshots/en and docs/screenshots/fr"
