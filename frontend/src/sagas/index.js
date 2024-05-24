import { delay } from 'redux-saga';
import {
    fork,
    put,
    select,
    take,
    takeLatest,
    throttle,
} from 'redux-saga/effects';

import * as types from '../constants/ActionType';
import { updateAbilities } from '../ability';
import buildWebsocket, { WSClose, WSOpen } from './socket';
import { bySongId } from '../util';
import { updateSettings } from '../Settings';

/**
 * Send a PLAYER_TICK every second to update the player position. This is much
 * more efficient than querying updates from the bin.
 */
function* tickPlayer() {
    while (true) {
        yield delay(1000);
        const isPlaying = yield select((state) => state.player.isPlaying);
        const isVisible = yield select((state) => state.system.visible);
        if (isPlaying && isVisible) {
            yield put({ type: types.InternalPlayerTick });
        }
    }
}

/**
 * Poll the queue (top songs).
 */
function* pollQueue() {
    while (true) {
        const system = yield select((state) => state.system);
        if (system.connected && system.visible) {
            yield put({ type: types.QueueRequest });
        }
        yield delay(2000);
    }
}

function* searchResultWatcher() {
    while (true) {
        const lastResults = yield select((state) => state.search.results._real);
        const action = yield take([
            types.InternalSearchClear,
            types.SearchResponse,
        ]);

        if (action.type === types.InternalSearchClear) {
            yield put({
                type: types.SongSubUnsub,
                unsubscribe: (lastResults || []).map(bySongId),
            });
        } else if (
            action.type === types.SearchResponse &&
            action.results.length
        ) {
            yield put({
                type: types.SongSubUnsub,
                subscribe: action.results.map(bySongId),
            });
        }
    }
}

/**
 * Dispatch bin payloads to client actions.
 */
function* onWebsocketMessage(payload) {
    console.debug('serv→me', payload);

    if (payload instanceof WSOpen) {
        yield put({ type: types.InternalConnected, connected: true });
        return;
    } else if (payload instanceof WSClose) {
        yield put({ type: types.InternalConnected, connected: false });
        return;
    }

    const { type, ...data } = payload;
    switch (type) {
        case types.PlayerState:
            yield put({
                type: types.PlayerState,
                player: data,
            });
            break;
        case types.Welcome:
            yield put({
                type: types.Welcome,
                user: {
                    name: data.myId,
                    caps: data.caps,
                    coverUrl: data.coverUrl,
                    libraryPageSize: data.libraryPageSize,
                },
            });
            break;
        case types.QueueResponse:
            yield put({
                type: types.QueueResponse,
                queue: data.queue,
                urgent: data.urgent,
            });
            break;
        case types.SongUpdate:
            yield put({
                type: types.SongUpdate,
                song: data.song,
            });
            break;
        case types.SearchResponse:
            yield put({
                type: types.SearchResponse,
                opaque: data.opaque,
                hasMore: data.hasMore,
                results: data.results,
            });
            break;
        // case types.SYSTEM_EVENTLOG:
        //     yield put({
        //         type: types.SYSTEM_EVENTLOG,
        //         event: data,
        //     });
        //     break;
        default:
            break;
    }
}

/**
 * Dispatch client actions to WS payloads on wire.
 */
function* websocketActions(socket) {
    function send(action) {
        if (socket.readyState !== WebSocket.OPEN) {
            console.warn('Tried to send a message on a closed socket');
            return;
        }
        console.debug('me→serv', action);
        socket.send(JSON.stringify(action));
    }

    // Needlessly complicated logic to have a smooth fade in/out when muting.
    function* smoothMuteFade() {
        const player = yield select((state) => state.player);
        let volume = player.volume;
        const target = volume === 0 ? 100 : 0;
        const sign = Math.sign(target - volume);
        if (target !== 0 && !player.isPlaying) {
            yield send({ type: types.SetPlaying, isPlaying: true });
        }
        while (volume !== target) {
            volume += sign * 10;
            volume = volume < 0 ? 0 : volume > 100 ? 100 : volume;
            yield delay(100);
            yield send({ type: types.SetVolume, volume: volume });
        }
        if (target === 0 && player.isPlaying) {
            yield send({ type: types.SetPlaying, isPlaying: false });
        }
    }

    function* searchRequest() {
        while (true) {
            yield take([
                types.SearchRequest,
                types.InternalSearchNextPage,
                types.InternalSearchPreviousPage,
            ]);
            const searchState = yield select((state) => state.search);
            const hasQuery = searchState.query && searchState.query.length;
            const hasFilter = !!searchState.filter;
            if (!hasQuery && !hasFilter) {
                console.log('clear search');
                yield put({ type: types.InternalSearchClear });
                continue;
            }
            const opaque = Math.random().toString(36).substring(7);
            yield send({
                type: types.SearchRequest,
                query: searchState.query,
                opaque: opaque,
                filter: searchState.filter,
                offset: searchState.offset,
            });
            while (true) {
                const action = yield take([
                    types.SearchResponse,
                    types.InternalSearchClear,
                ]);
                if (action.type === types.InternalSearchClear) break;
                if (action.opaque !== opaque) continue;
                if (!action.results.length) {
                    // End of results.
                    yield put({
                        type: types.InternalAppendSearchResult,
                        hasMore: false,
                        song: null,
                    });
                    break;
                }
                for (let song of action.results)
                    yield put({
                        type: types.InternalAppendSearchResult,
                        song: song,
                    });
                if (action.hasMore) {
                    yield put({
                        type: types.InternalAppendSearchResult,
                        hasMore: true,
                        song: null,
                    });
                    break;
                }
            }
        }
    }

    // The stupid <Seekbar> component doesn't distinguishes between human clicks
    // (human asks to seek) and system updates (each second +1 on the position).
    // So we prevent sending out-of-bound seek which would confuse MPV a lot.
    function* sendSeek(action) {
        const duration = yield select((state) => state.player.duration);
        if (action.position >= duration) return;
        send(action);
    }

    // Requests and votes
    yield takeLatest(types.Vote, send);
    // Search
    yield fork(searchRequest);

    // Moderation
    yield takeLatest(types.SetBanned, send);
    yield takeLatest(types.AcceptSongRequest, send);
    yield takeLatest(types.AdminQueueInsert, send);
    yield takeLatest(types.AdminQueueRemove, send);
    yield takeLatest(types.AdminQueueMoveUp, send);
    yield takeLatest(types.AdminQueueMoveDown, send);
    // State management
    yield takeLatest(types.SongSubUnsub, send);
    yield takeLatest(types.QueueRequest, send);
    // Control
    yield takeLatest(types.SetPlaying, send);
    yield takeLatest(types.Skip, send);
    yield throttle(250, types.Seek, sendSeek);
    yield throttle(250, types.SetVolume, send);
    yield takeLatest(types.InternalMute, smoothMuteFade);
}

function* observeUserChanges() {
    while (true) {
        yield take(types.Welcome);
        let userState = yield select((state) => state.user);
        updateSettings(userState);
        console.log('user changed:', userState, '; updating abilities');
        updateAbilities(userState);
    }
}

function* rootSaga() {
    // Connect and install handlers.
    yield fork(buildWebsocket, onWebsocketMessage, websocketActions);

    // Update song subscriptions when results come in.
    yield fork(searchResultWatcher);

    // Handle one second tick & queue poll.
    yield fork(pollQueue);

    // Increment player elapsed time each second.
    yield fork(tickPlayer);

    // Handle ability & coverUrl updates.
    yield fork(observeUserChanges);
}

export default rootSaga;
