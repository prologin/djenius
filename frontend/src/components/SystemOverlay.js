import React from 'react';
import classnames from 'classnames';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faPlug } from '@fortawesome/free-solid-svg-icons';

import style from './SystemOverlay.module.scss';

library.add(faPlug);

const SystemOverlay = ({ connected }) => (
    <div
        className={classnames(style.systemOverlay, {
            [style.connected]: connected,
        })}
    >
        <FontAwesomeIcon icon="plug" />
        &nbsp;Connecting…
    </div>
);

export default SystemOverlay;
