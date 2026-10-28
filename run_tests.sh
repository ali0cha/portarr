#!/bin/sh
# Runs the test suite in a throwaway Python container, as your own user (like CI: no root-only shortcuts).
# Extra arguments go to pytest as they are:  ./run_tests.sh -k "trash and order"
cd "$(dirname "$0")"
exec docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp/h -e PIP_DISABLE_PIP_VERSION_CHECK=1 -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD":/src -w /src python:3.12-slim \
  sh -c 'pip install -q --user --no-warn-script-location -r requirements-dev.txt 2>&1 | grep -v WARNING; exec python -m pytest -q -p no:cacheprovider "$@"' sh "$@"
