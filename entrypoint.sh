#!/bin/sh

set -e

ls 'djenius-base'
export PYTHONPATH="djenius-base:devel:${PYTHONPATH}"
echo "$MPV"

if [ "$BACKEND" -eq 1 ]; then
    exec python -m djenius.bin.backend \
        --logging=DEBUG \
        --unix=./devel/sock/backend.socket \
        --whoosh-dir=/tmp/djraio-woosh \
        --auth=djenius_auth_dev.DevAuthProvider \
        --state-file=/tmp/djraio.pickle \
        --mpv="$MPV" \
        --resolver="$RESOLVER/resolve"
else
    exec python -m djenius.bin.resolver \
        --logging=DEBUG \
        --unix=./devel/sock/resolver.socket
fi

exec "$@"
