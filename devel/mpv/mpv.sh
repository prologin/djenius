#!/bin/bash

trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

set -x

PORT=6600
SOCKET=/tmp/mpv.sock

function run_mpv() {
    while true
    do
        mpv --input-ipc-server=$SOCKET \
            --idle --input-terminal=yes --no-ytdl --no-audio-display --force-seekable=yes \
            || sleep 1
    done
}

function run_socat() {
    while true
    do
        socat TCP-LISTEN:$PORT,reuseaddr,pf=ip4,fork UNIX-CONNECT:$SOCKET || sleep 1
    done
}

run_socat &
run_mpv
