#!/bin/sh

set -e

export PYTHONPATH="djenius-base:devel:${PYTHONPATH}"

exec python -m djenius.bin.backend \
    --logging=DEBUG \
    --unix=/sock/backend.socket \
    --whoosh-dir=/tmp/djraio-woosh \
    --auth=djenius_auth_dev.DevAuthProvider \
    --state-file=/tmp/djraio.pickle \
    --mpv="$MPV" \
    --resolver="$RESOLVER/resolve"
