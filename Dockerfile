FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    CONFIG_DIR=/config \
    PORT=8765

WORKDIR /srv
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

# 568:568 is the "apps" user/group of TrueNAS SCALE
RUN mkdir /config && chown 568:568 /config
USER 568:568
VOLUME /config
EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD ["python", "-c", "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/healthz' % os.environ.get('PORT','8765'), timeout=4)"]

CMD ["python", "-m", "app"]
