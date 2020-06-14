import {connect} from 'react-redux'
import UserComponent from '../components/User'

export const User = connect(state => ({
    user: state.user,
}), {})(UserComponent);
