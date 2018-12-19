#!/bin/sh

set -e

export MB_DB=${MB_DB:-'postgresql://postgres:musicbot@localhost:5432/musicbot_test'}
pytest -n 4 $@
coverage-badge -f -o doc/coverage.svg
coverage report -m
