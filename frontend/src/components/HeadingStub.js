import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

import style from './HeadingStub.module.scss';
import * as classnames from 'classnames';

export default ({ icon, children, className }) => (
    <div className={classnames(style.headingStub, className)}>
        <FontAwesomeIcon className={style.icon} icon={icon} />
        {children}
    </div>
);
