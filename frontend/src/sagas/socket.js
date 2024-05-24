/**
 * Boilerplate to wrap a native WebSocket object into a Saga channel.
 */
import { delay, eventChannel, END, buffers } from 'redux-saga';
import { call, cancel, fork, take } from 'redux-saga/effects';

import { RECONNECTION_DELAY, WS_ENDPOINT } from '../Settings';

export class WSOpen {}
export class WSClose {}

function buildSocketConnection() {
    return new Promise((resolve, reject) => {
        console.log('Connecting to WS:', WS_ENDPOINT);
        const socket = new WebSocket(WS_ENDPOINT);
        socket.onopen = function () {
            console.log('Connected to WS');
            resolve(socket);
        };
        socket.onerror = function (evt) {
            reject(evt);
        };
    });
}

function buildSocketChannel(socket) {
    return eventChannel((emit) => {
        socket.onmessage = (event) => {
            emit(JSON.parse(event.data));
        };
        socket.onclose = () => {
            emit(new WSClose());
            emit(END);
        };
        socket.onerror = (event) => {};
        emit(new WSOpen());
        return () => {
            // unsubscribe
            socket.onmessage = null;
        };
    }, buffers.expanding(20));
}

/**
 * Auto-reconnecting WebSocket channel listener.
 *
 * @param onMessage: callback yielded for each JSON message received on the WS.
 *                   Already parsed.
 * @param actions: generator that is forked alongside the channel with the
 *                 WebSocket as first argument, so user can send messages on it.
 */
let attempts = 0;
export default function* listenForSocket(onMessage, actions) {
    let socket, channel, actionTask;
    try {
        socket = yield call(buildSocketConnection);
        channel = yield call(buildSocketChannel, socket);
        actionTask = yield fork(actions, socket);
        attempts = 0;
        while (true) {
            const payload = yield take(channel);
            yield onMessage(payload);
        }
    } catch (error) {
    } finally {
        if (channel) channel.close();
        if (socket) socket.close();
        if (actionTask) yield cancel(actionTask);
        const duration = Math.min(10, Math.pow(RECONNECTION_DELAY, attempts++));
        console.warn(`WS disconnected; reconnecting in ${duration} s`);
        yield delay(duration * 1000);
        yield listenForSocket(onMessage, actions);
    }
    return socket;
}
