import { connect } from 'react-redux';
import PlayerComponent from '../components/Player';
import * as types from '../constants/ActionType';
import { can, Capability } from '../ability';

export const Player = connect(
    (state) => ({
        player: state.player,
        song: state.player.song,
    }),
    (dispatch) => ({
        trackSeek(position) {
            can(Capability.Seek) &&
                dispatch({
                    type: types.Seek,
                    position: parseInt(parseFloat(position)),
                });
        },
    })
)(PlayerComponent);
