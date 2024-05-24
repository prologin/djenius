import { connect } from 'react-redux';
import ControllerComponent from '../components/Controller';
import * as types from '../constants/ActionType';
import { can, Capability } from '../ability';

export const Controller = connect(
    (state) => ({
        player: state.player,
        song: state.player.song,
    }),
    (dispatch) => ({
        volumeChanged(volume) {
            can(Capability.Volume) &&
                dispatch({ type: types.SetVolume, volume });
        },
        muteClicked() {
            can(Capability.Volume) &&
                can(Capability.Pause) &&
                dispatch({ type: types.InternalMute });
        },
        playPauseClicked(playing) {
            can(Capability.Pause) &&
                dispatch({ type: types.SetPlaying, isPlaying: !playing });
        },
        skipClicked() {
            can(Capability.Skip) && dispatch({ type: types.Skip });
        },
    })
)(ControllerComponent);
