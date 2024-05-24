import * as types from '../constants/ActionType';

const initialState = {
    pause: true,
    duration: 0,
    position: 0,
    volume: 0,
    song: null,
};

const player = (state = initialState, action) => {
    switch (action.type) {
        case types.PlayerState:
            return {
                ...state,
                ...action.player,
                duration: action.player.duration,
            };
        case types.InternalPlayerTick:
            return {
                ...state,
                position: state.position + 1,
            };
        default:
            return state;
    }
};

export default player;
