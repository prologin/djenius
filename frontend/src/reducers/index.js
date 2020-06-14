import {combineReducers} from 'redux'

import * as types from '../constants/ActionType'
import queues from './queues'
import search from './search'
import player from './player'
import {can, Capability} from "../ability";

const initialSystemState = {
    connected: false,
    visible: true,
    // eventLog: {visible: false, events: []},
};

const system = (state = initialSystemState, action) => {
    switch (action.type) {
        case types.InternalConnected:
            return {
                ...state,
                connected: action.connected,
            };
        case types.InternalVisibilityChange:
            return {
                ...state,
                visible: action.visible,
            };
        // case types.SYSTEM_EVENTLOG:
        //     const new_events = [action.event, ...state.eventLog.events].slice(0, 20);
        //     return {
        //         ...state,
        //         eventLog: {...state.eventLog, events: new_events},
        //     };
        case types.InternalKeypress:
            const event = action.event;
            if (event.key === 'e') {
                if (!can(Capability.EventLog)) return state;
                // Toggle event log.
                return {
                    ...state,
                    eventLog: {
                        ...state.eventLog,
                        visible: !state.eventLog.visible
                    }
                };
            }
            return state;
        default:
            return state;
    }
};

const user = (state = {name: null, coverUrl: '', caps: []}, action) => {
    switch (action.type) {
        case types.Welcome:
            return {
                ...state,
                ...action.user,
            };
        default:
            return state;
    }
};

export default combineReducers({
    system,
    user,
    queues,
    search,
    player,
});
