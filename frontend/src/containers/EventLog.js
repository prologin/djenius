import {connect} from 'react-redux'
import EventLogComponent from '../components/EventLog'

export const EventLog = connect(state => ({
    visible: state.system.eventLog.visible,
    events: state.system.eventLog.events,
}), {})(EventLogComponent);
