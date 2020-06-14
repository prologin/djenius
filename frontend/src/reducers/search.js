import * as types from '../constants/ActionType'
import {Lockable} from "./util";
import {bySongId} from "../util";
import {libraryPageSize} from "../Settings";

export const State = {
    empty: 0, searching: 1, doneHasMore: 2, doneEof: 3, error: 4,
};

export const Filter = {
    Requested: "Requested", Banned: "Banned", Library: "Library",
};

const initialState = {
    query: '',
    results: Lockable.make([]),
    state: State.empty,
    filter: null,
    offset: 0,
};

const search = (state = initialState, action) => {
    switch (action.type) {
        case types.InternalSearchQuery:
            return {
                ...state,
                query: action.query,
            };
        case types.SearchRequest:
            return {
                ...state,
                state: State.searching,
                results: Lockable.reset(state.results),
            };
        case types.InternalSearchNextPage:
            if (state.state === State.searching) return state;
            return {
                ...state,
                offset: state.offset + libraryPageSize(),
                results: Lockable.reset(state.results),
            };
        case types.InternalSearchPreviousPage:
            if (state.state === State.searching) return state;
            return {
                ...state,
                offset: state.offset - libraryPageSize(),
                results: Lockable.reset(state.results),
            };
        case types.InternalSearchFilter:
            // Toggle filter.
            const newFilter =
                state.filter === action.filter ? null : action.filter;
            return {
                ...state,
                filter: newFilter,
                offset: 0,
            };
        case types.InternalSearchClear:
            return {
                ...state,
                state: State.empty,
                query: '',
                filter: null,
                offset: 0,
            };
        case types.InternalSearchError:
            return {
                ...state,
                state: State.error,
                results: Lockable.reset(state.results),
            };
        case types.InternalAppendSearchResult:
            const song = action.song;
            return {
                ...state,
                state: song === null ? (action.hasMore ? State.doneHasMore : State.doneEof) : State.searching,
                results: song === null ? state.results : Lockable.appendItem(state.results, song),
            };
        case types.SongUpdate:
            return {
                ...state,
                results: Lockable.updateItem(state.results, action.song, bySongId),
            };
        default:
            return state
    }
};

export default search
