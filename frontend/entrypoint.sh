#!/bin/sh

set -e

if [ -n "$DEV" ]
then
    export REACT_APP_DJENIUS_SOCKET_HOST="\"$DJENIUS_SOCKET_HOST\""
    exec npm run start
else
    export REACT_APP_DJENIUS_SOCKET_HOST=window.location.host
    exec npm run build
fi
