import { connect } from 'react-redux';
import SystemOverlayComponent from '../components/SystemOverlay';

export const SystemOverlay = connect(
    (state) => ({
        connected: state.system.connected,
    }),
    {}
)(SystemOverlayComponent);
