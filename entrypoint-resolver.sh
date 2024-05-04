#!/bin/sh

set -e

export PYTHONPATH="djenius-base:devel:${PYTHONPATH}"

exec python -m djenius.bin.resolver \
    --logging=DEBUG \
    --listen=0.0.0.0:8000
