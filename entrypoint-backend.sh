#!/bin/sh

set -e

export PYTHONPATH="djenius-base:devel:${PYTHONPATH}"

exec python -m djenius.bin.backend \
    --logging=DEBUG \
    --listen=0.0.0.0:7001 \
    --whoosh-dir=/tmp/djraio-woosh \
    --auth=djenius_auth_oauth.OauthAuthProvider \
    --state-file=/tmp/djraio.pickle \
    --mpv="${MPV}" \
    --resolver="${RESOLVER_URL}/resolve" \
    --public-resolver="${PUBLIC_RESOLVER_URL}/resolve" \
    --mvp-windows="${MPV_WINDOWS}"
