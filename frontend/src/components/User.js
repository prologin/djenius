import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faUser } from '@fortawesome/free-solid-svg-icons';
import style from './User.module.scss';

library.add(faUser);

const User = ({ user }) => (
    <div className={style.user}>
        <FontAwesomeIcon icon="user" />{' '}
        {user.name === null ? <em>anonymous</em> : user.name}
    </div>
);

export default User;
