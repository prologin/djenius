#!/bin/sh

set -e

export PYTHONPATH="djenius-base:devel:${PYTHONPATH}"

exec python -m djenius.bin.resolver \
    --logging=DEBUG \
    --unix=./sock/resolver.socket
