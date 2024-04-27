FROM bash:devel-alpine3.19

RUN apk update && \
    apk add --no-cache bash mpv socat && \
    rm -rf /var/cache/apk/*

COPY mpv.sh mpv.sh
RUN chmod +x mpv.sh

CMD ["./mpv.sh"]
