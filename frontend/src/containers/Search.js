import {connect} from 'react-redux'
import SearchComponent from '../components/Search'
import SongCardActions from './SongCard';
import * as types from '../constants/ActionType'

export const Search = connect(state => ({
    results: state.search.results.public,
    state: state.search.state,
    query: state.search.query,
    filter: state.search.filter,
    offset: state.search.offset,
}), dispatch => ({
    onQueryChange(e) {
        dispatch({type: types.InternalSearchQuery, query: e.target.value});
    },
    acceptClicked(song) {
        dispatch({type: types.AcceptSongRequest, songId: song.song.id});
    },
    clearClicked() {
        dispatch({type: types.InternalSearchClear});
    },
    searchFilter(query, newFilter) {
        dispatch({type: types.InternalSearchFilter, filter: newFilter});
        dispatch({type: types.SearchRequest});
    },
    startSearch() {
        dispatch({type: types.SearchRequest});
    },
    searchNextPage() {
        dispatch({type: types.InternalSearchNextPage});
    },
    searchPreviousPage() {
        dispatch({type: types.InternalSearchPreviousPage});
    },
    ...SongCardActions(dispatch),
}))(SearchComponent);
