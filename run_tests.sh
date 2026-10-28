#!/bin/sh
# Runs the test suite in a throwaway Python container (no local Python setup needed).
# Extra arguments go to pytest as they are:  ./run_tests.sh -k "trash and order"
cd "$(dirname "$0")"
exec docker run --rm -e PYTHONDONTWRITEBYTECODE=1 -v "$PWD":/src -v portarr-pip:/root/.cache/pip -w /src python:3.12-slim \
  sh -c 'pip install -q -r requirements-dev.txt 2>&1 | grep -v -e WARNING -e notice; exec python -m pytest -q -p no:cacheprovider "$@"' sh "$@"
