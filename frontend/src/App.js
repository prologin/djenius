import React from 'react'

import Can from './components/Can';

import {Player} from './containers/Player'
import {Queue} from './containers/Queue'
import {Search} from './containers/Search'
import {SystemOverlay} from './containers/SystemOverlay';
// import {EventLog} from './containers/EventLog';
import {User} from './containers/User'
import {Controller} from './containers/Controller'

import style from './App.module.scss'
import {Capability} from "./ability";

const App = () => (
    <>
        <SystemOverlay/>
        {/*<TTSModal/>*/}
        <header className={style.header}>
            <h1>djenius</h1>
            <User/>
        </header>
        <Player/>
        <Controller/>
        <Queue/>
        <Can I={Capability.Search}><Search/></Can>
        {/*<Can do="control" on="all"><EventLog/></Can>*/}
    </>
);

export default App
