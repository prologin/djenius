import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { applyMiddleware, createStore } from 'redux';
import createSagaMiddleware from 'redux-saga';

import App from './App';
import reducers from './reducers';
import sagas from './sagas';
import * as types from './constants/ActionType';

const sagaMiddleware = createSagaMiddleware();

const store = createStore(reducers, applyMiddleware(sagaMiddleware));

document.addEventListener(
    'visibilitychange',
    function (e) {
        store.dispatch({
            type: types.InternalVisibilityChange,
            visible: document.visibilityState === 'visible',
        });
    },
    false
);

sagaMiddleware.run(sagas);

ReactDOM.render(
    <Provider store={store}>
        <App />
    </Provider>,
    document.getElementById('root')
);
