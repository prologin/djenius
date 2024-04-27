FROM python:3.8-alpine3.18

COPY requirements.txt .

RUN \
    apk update && \
    apk add --no-cache \
        python3-dev \
        gcc \
        libc-dev \
        libffi-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/cache/apk/*

#RUN adduser -D app

#WORKDIR /home/app/

#USER app

COPY . .

CMD ["./entrypoint.sh"]
