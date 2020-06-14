import React from "react";
import {library} from "@fortawesome/fontawesome-svg-core";
import {
    faGavel,
    faMusic,
    faPlus,
    faStar,
    faThumbsDown,
    faThumbsUp,
    faArrowDown,
    faArrowUp,
    faTrash,
} from "@fortawesome/free-solid-svg-icons";
import {faSpotify, faYoutube} from "@fortawesome/free-brands-svg-icons";
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import classnames from "classnames";

import {humanDuration} from "../util";
import style from "./SongCard.module.scss";
import {can, Capability} from "../ability";
import {coverUrl} from "../Settings";

library.add(faThumbsUp, faThumbsDown, faArrowUp, faArrowDown, faTrash, faPlus, faGavel, faStar, faMusic, faSpotify, faYoutube);

const SongCard = ({song, acceptClicked, voteUpClicked, voteDownClicked, banClicked,
                      addToAdminQueueClicked, removeFromAdminQueueClicked,
                      moveUpAdminQueueClicked, moveDownAdminQueueClicked}) => {
    const isAdminSong = song.adminIndex !== null,
        hasCastedVote = song.userVote !== 0,
        isSuggestable = song.state === "New" && song.reviewRequired,
        isVotable = song.state === "Available" || (song.state === "New" && !song.reviewRequired),
        canSuggest = !isAdminSong && isSuggestable && can(Capability.Suggest),
        canAccept = !isAdminSong && isSuggestable && can(Capability.Accept),
        canUpVote = !isAdminSong && isVotable && (hasCastedVote || can(Capability.UpVote)),
        canDownVote = !isAdminSong && isVotable && (hasCastedVote || can(Capability.DownVote)),
        canAdminQueue = can(Capability.AdminQueue);
    return (
        <div className={style.songCard}>
            <div
                className={style.coverArt}
                style={{backgroundImage: `url(${coverUrl(song)})`}}
                title="Cover art"/>
            <span className={style.title} title={song.song.title}>{song.song.title}</span>
            <p color="textSecondary" className={style.infoLine}>
                {song.song.artist && (
                    <span className={!song.song.artist ? style.noArtist : ''}
                          title={song.song.artist}>{song.song.artist}</span>
                )}
                {song.song.explicit && (
                    <span className={style.tag}
                          title="Contains explicit lyrics">explicit</span>
                )}
                {song.playCount > 0 && (
                    <span className={style.tag}
                          title={`Played ${song.playCount} times`}>
                    <FontAwesomeIcon icon="music" size="xs"/> {song.playCount}
                </span>
                )}
            </p>
            <div className={style.votes}>
                {!isAdminSong && can(Capability.Ban) && (
                    <button className={classnames(style.button, style.ban, {
                        [style.extra]: song.state !== "Banned",
                        [style.active]: song.state === "Banned"
                    })}
                            onClick={() => banClicked && banClicked(song)}
                            title="Ban this song (cannot be played nor searched)">
                        <FontAwesomeIcon icon="gavel"/>
                    </button>
                )}
                {isAdminSong && canAdminQueue && (<>
                    <button className={classnames(style.button, style.promote, style.extra)}
                            onClick={() => removeFromAdminQueueClicked && removeFromAdminQueueClicked(song)}
                            title="Remove this song from the admin queue">
                        <FontAwesomeIcon icon="trash"/></button>
                    <button className={classnames(style.button, style.promote, style.extra)}
                            onClick={() => moveUpAdminQueueClicked && moveUpAdminQueueClicked(song.adminIndex)}
                            title="Move up in admin queue">
                        <FontAwesomeIcon icon="arrow-up"/></button>
                    <button className={classnames(style.button, style.promote, style.extra)}
                            onClick={() => moveDownAdminQueueClicked && moveDownAdminQueueClicked(song.adminIndex)}
                            title="Move down in admin queue">
                        <FontAwesomeIcon icon="arrow-down"/></button>
                </>)}
                {!isAdminSong && canAdminQueue && (
                    <button className={classnames(style.button, style.promote, style.extra)}
                             onClick={() => addToAdminQueueClicked && addToAdminQueueClicked(song)}
                             title="Promote this song (last in admin queue)">
                            <FontAwesomeIcon icon="star"/></button>
                    )}
                {isAdminSong && (
                    <span className={style.voteCount}
                          title="Promoted song: plays before other songs">
                        <FontAwesomeIcon icon="star" className={style.promoted} size="xs"/>
                    </span>)}
                {!isAdminSong && song.state === "Available" && (
                    <span className={style.voteCount}>{song.votes}</span>
                )}
                {canUpVote && (
                    <button
                        className={classnames(style.button, style.voteUp, {[style.active]: song.userVote === 1})}
                        onClick={(e) => voteUpClicked && voteUpClicked(song)}
                        title="Up-vote this song">
                        <FontAwesomeIcon icon="thumbs-up"/></button>)}
                {canDownVote && (
                    <button
                        className={classnames(style.button, style.voteDown, {[style.active]: song.userVote === -1})}
                        onClick={(e) => voteDownClicked && voteDownClicked(song)}
                        title="Down-vote this song">
                        <FontAwesomeIcon icon="thumbs-down"/></button>)}
                {(canSuggest && !canAccept) && (
                    // Not yet available, but can request a review (or cancel it).
                    <button
                        className={classnames(style.button, style.suggest)}
                        onClick={(e) => (voteUpClicked && voteUpClicked(song))}
                        title="Request this song to be reviewed">
                        {song.userVote === 0 ? "request review" : "cancel request"}
                        {song.votes > 0 && (<span>&nbsp;({song.votes})</span>)}
                    </button>)}
                {canAccept && (
                    <button
                        className={classnames(style.button, style.suggest)}
                        onClick={(e) => acceptClicked && acceptClicked(song)}
                        title="Accept this song">
                        accept
                        {song.state === "New" && song.votes > 0 && (
                            <span>&nbsp;({song.votes})</span>
                        )}
                    </button>)}
            </div>
            <div className={style.duration} title="Song duration (MM:SS)">
                {humanDuration(song.song.duration)}
            </div>
            <FontAwesomeIcon className={style.resolver}
                             title={`Resolved by ${song.song.resolver}`}
                             icon={['fab', song.song.resolver]}/>
        </div>);
};

export default SongCard
