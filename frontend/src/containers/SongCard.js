import * as types from '../constants/ActionType';

export default (dispatch) => ({
    voteUpClicked(song) {
        const value = song.userVote === +1 ? 0 : +1;
        dispatch({ type: types.Vote, songId: song.song.id, value });
    },
    voteDownClicked(song) {
        const value = song.userVote === -1 ? 0 : -1;
        dispatch({ type: types.Vote, songId: song.song.id, value });
    },
    banClicked(song) {
        dispatch({
            type: types.SetBanned,
            songId: song.song.id,
            isBanned: song.state !== 'Banned',
        });
    },
    addToAdminQueueClicked(song) {
        dispatch({ type: types.AdminQueueInsert, songId: song.song.id });
    },
    removeFromAdminQueueClicked(song) {
        dispatch({ type: types.AdminQueueRemove, songId: song.song.id });
    },
    moveUpAdminQueueClicked(position) {
        dispatch({ type: types.AdminQueueMoveUp, position: position });
    },
    moveDownAdminQueueClicked(position) {
        dispatch({ type: types.AdminQueueMoveDown, position: position });
    },
});
