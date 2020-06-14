import React from 'react'
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {library} from '@fortawesome/fontawesome-svg-core';
import {
    faGavel,
    faMeh,
    faSearch,
    faSpinner,
    faStar,
    faThumbsUp,
    faTimes,
    faBook,
} from '@fortawesome/free-solid-svg-icons';
import classnames from 'classnames';

import style from './Search.module.scss';
import {Filter, State} from '../reducers/search';

import SongCard from './SongCard';
import HeadingStub from './HeadingStub';
import Can from './Can';

library.add(faSpinner, faSearch, faTimes, faMeh, faGavel, faStar, faThumbsUp, faBook);

const Checkbox = ({checked, onClick, onChange, ...props}) => (
    <label className={classnames(style.togglerWithIcon)} {...props}>
        <input type="checkbox" checked={checked} onClick={onClick} onChange={onChange}/>
        <span>{props.children}</span>
    </label>
);

const SearchingSpinner = () => (<div>
    <FontAwesomeIcon className={style.paddedIcon} icon="spinner" spin size="2x"/>
    Searching…
</div>);

const Search = ({startSearch, state, searchFilter, clearClicked, results, query, offset, filter, searchNextPage, searchPreviousPage, onQueryChange, acceptClicked, voteUpClicked, voteDownClicked, banClicked, addToAdminQueueClicked}) => (
    <div className={style.search}>
        <HeadingStub className={classnames({[style.spaceBetween]: filter === Filter.Library})}
                     icon={filter === Filter.Library ? "book" : "search"}>
            {filter !== Filter.Library ? <>
                    <input className={style.searchInput} placeholder="Search songs"
                       value={query} onChange={onQueryChange}
                       disabled={state === State.searching}
                       onKeyPress={(e) => (e.key === 'Enter') && startSearch()}/>
                <button onClick={() => clearClicked()}
                        disabled={!query.length}
                        className={classnames(style.clearSearch, {[style.visible]: !!query.length})}>
                    <FontAwesomeIcon icon="times"/>
                </button>
                <Can do="Accept" on="all">
                    <Checkbox checked={filter === Filter.Requested}
                             onChange={() => searchFilter(query, Filter.Requested)}
                             title="Show requested only">R</Checkbox>
                </Can>
                <Can do="Ban" on="all">
                    <Checkbox checked={filter === Filter.Banned}
                             onChange={() => searchFilter(query, Filter.Banned)}
                             title="Show banned only"><FontAwesomeIcon icon="gavel"/></Checkbox>
                </Can>
            <button className={style.searchLibrary} onClick={() => searchFilter(query, Filter.Library)}
                    title="All songs in the library"><FontAwesomeIcon icon="book"/>&nbsp;Library</button>
            </> : <>
                All songs
                <button className={style.searchLibrary}
                        onClick={() => searchFilter(query, Filter.Library)}><FontAwesomeIcon icon="search"/>&nbsp;Back to search</button></>}
        </HeadingStub>
        {(state === State.empty) ? (
            <div className={style.emptyContent}>
                <FontAwesomeIcon className={style.paddedIcon} icon="search"
                                 size="2x"/>
                Find songs using the search above.
            </div>) : ""}
        {(state === State.doneEof && !results.length) ? (
            <div className={style.emptyContent}>
                <FontAwesomeIcon className={style.paddedIcon} icon="meh" size="2x"/>
                No results.<br/>Check the spelling or try something less specific!
            </div>) : ""}
        {(state === State.searching || state === State.doneHasMore || state === State.doneEof) ? (
            <div className={style.scrollArea}>
                {((state === State.doneHasMore || state === State.doneEof) && filter === Filter.Library && offset > 0) ? <button onClick={() => searchPreviousPage()}>Previous Page</button> : ""}
                {results.map((song) =>
                    <SongCard key={song.song.id}
                              song={song}
                              acceptClicked={acceptClicked}
                              voteUpClicked={voteUpClicked}
                              voteDownClicked={voteDownClicked}
                              addToAdminQueueClicked={addToAdminQueueClicked}
                              banClicked={banClicked}/>)}
                {(state === State.searching) ? <SearchingSpinner/> : ""}
                {(state === State.doneHasMore && filter === Filter.Library) ? <button onClick={() => searchNextPage()}>Next Page</button> : ""}
            </div>) : ""}
    </div>
);

export default Search
