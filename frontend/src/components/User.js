import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faUser } from '@fortawesome/free-solid-svg-icons';
import style from './User.module.scss';

library.add(faUser);

const User = ({ user }) => (
    <div className={style.user} style={{textAlign: 'center'}}>
        <FontAwesomeIcon icon="user" />{' '}
      {user.name === null ? <>
        <em>anonymous</em>
        {user.loginPath !== undefined && <><br/><span>(<a href={user.loginPath}>Login</a>)</span></>}
        </> : <>
        {user.name}
        {user.logoutPath !== undefined && <><br/><span>(<a href={user.logoutPath}>Logout</a>)</span></>}
      </>}
    </div>
);

export default User;
