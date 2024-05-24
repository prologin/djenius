import * as types from '../constants/ActionType';
import { Lockable } from './util';
import { songKey } from '../util';

const initialState = {
    queue: Lockable.make(),
};

const queues = (state = initialState, action) => {
    switch (action.type) {
        case types.QueueResponse:
            return {
                ...state,
                queue: Lockable.update(
                    state.queue,
                    action.queue,
                    action.urgent
                ),
            };
        case types.SongUpdate:
            return {
                ...state,
                queue: Lockable.updateItem(state.queue, action.song, songKey),
            };
        case types.InternalQueueLock:
            return { ...state, queue: Lockable.lock(state.queue) };
        case types.InternalQueueRelease:
            return { ...state, queue: Lockable.release(state.queue) };
        default:
            return state;
    }
};

export default queues;
