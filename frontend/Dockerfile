FROM node:14

COPY package.json yarn.lock .

RUN \
    yarn install && \
    adduser app

WORKDIR /home/app/

RUN mv /node_modules .

USER app

COPY . .

CMD ["npm", "run", "start"]

