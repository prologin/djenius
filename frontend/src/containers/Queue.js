import { connect } from 'react-redux';
import QueueComponent from '../components/Queue';
import SongCardActions from './SongCard';
import * as types from '../constants/ActionType';

export const Queue = connect(
    (state) => ({
        queue: state.queues.queue.public,
    }),
    (dispatch) => ({
        handleMouseEnter() {
            // Lock queue updates when mouse is over the queue scroll area.
            dispatch({ type: types.InternalQueueLock });
        },
        handleMouseLeave() {
            // Unlock queue updates when mouse leaves the queue scroll area.
            dispatch({ type: types.InternalQueueRelease });
        },
        ...SongCardActions(dispatch),
    })
)(QueueComponent);
