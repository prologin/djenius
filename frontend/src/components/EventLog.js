import React from "react";
import classnames from 'classnames';
import {library} from "@fortawesome/fontawesome-svg-core";
import {
    faDoorClosed,
    faDoorOpen,
    faClock,
    faPause,
    faPlay,
    faStepForward,
    faCheckCircle,
    faGavel,
    faStar,
    faFile,
    faMusic,
    faThumbsDown,
    faThumbsUp,
    faVolumeUp
} from "@fortawesome/free-solid-svg-icons";

import style from './EventLog.module.scss';
import * as types from '../constants/ActionType';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {humanDuration} from '../util';
import HeadingStub from "./HeadingStub";

library.add(faThumbsDown, faThumbsUp, faClock, faVolumeUp, faPlay, faPause, faStepForward, faCheckCircle, faGavel, faStar, faFile, faMusic, faDoorOpen, faDoorClosed);

const Action = (props) => (
    <td className={style.action}>{props.children}</td>
);

const Subject = (props) => (
    <td className={style.subject} width="100%">{props.children}</td>
);

const Song = ({song}) => (<><strong>{song.song.title}</strong> ⋅ {song.song.artist}</>);

const VoteIcon = ({vote, disabled}) => (
    <FontAwesomeIcon icon={`thumbs-${vote}`} className={classnames({
        [style.upVoteColor]: !disabled && vote === +1,
        [style.downVoteColor]:!disabled && vote === -1,
    })}/>
);

const UserJoinEvent = () => (
    <><Action><FontAwesomeIcon icon="door-open" className={style.upVoteColor}/></Action><Subject/></>
);

const UserPartEvent = () => (
    <><Action><FontAwesomeIcon icon="door-closed" className={style.downVoteColor}/></Action><Subject/></>
);

const PlayingEvent = ({event}) => (
    <>
        <Action><FontAwesomeIcon
            icon={event.isPlaying ? "play" : "pause"}/></Action>
        <Subject/>
    </>
);

const SeekEvent = ({event}) => (
    <>
        <Action><FontAwesomeIcon icon="clock"/></Action>
        <Subject>{humanDuration(event.position)}</Subject>
    </>
);
const VolumeSetEvent = ({event}) => (
    <>
        <Action><FontAwesomeIcon icon="volume-up"/></Action>
        <Subject>{event.volume}&nbsp;%</Subject>
    </>
);

const VoteEvent = ({event}) => (
    <>
        <Action>
            {event.vote === "unset" ? <>
                <VoteIcon vote={event.old_vote} disabled/>
            </> : <VoteIcon vote={event.vote}/>
            }
        </Action>
        <Subject><Song song={event.song}/></Subject>
    </>
);

const SkipEvent = () => (
    <><Action><FontAwesomeIcon icon="step-forward"/></Action><Subject/></>
);

const SearchEvent = ({event}) => (
    <>
        <Action><FontAwesomeIcon icon="search"/></Action>
        <Subject>“{event.query}”</Subject>
    </>
);

const AcceptRequestEvent = ({event}) => (
    <>
        <Action><FontAwesomeIcon icon="check-circle" className={style.upVoteColor}/></Action>
        <Subject><Song song={event.song}/></Subject>
    </>
);

const BanEvent = ({event}) => (
    <>
        <Action><FontAwesomeIcon icon="gavel" className={event.available ? style.upVoteColor : style.downVoteColor}/></Action>
        <Subject><Song song={event.song}/></Subject>
    </>
);

const PromoteEvent = ({event}) => (
    <>
        <Action><FontAwesomeIcon icon="star" className={classnames({[style.promoteColor]: event.promoted})}/></Action>
        <Subject><Song song={event.song}/></Subject>
    </>
);

const PlayerEvent = ({event}) => (
    <>
        <Action><FontAwesomeIcon icon="music"/></Action>
        <Subject><Song song={event.song}/></Subject>
    </>
);

const EventLog = ({events, visible}) => (
    <div className={style.eventLog}>
        <HeadingStub icon="file">
            <span className={style.heading}>Event log</span>
        </HeadingStub>
        <table><tbody>
            {events.map(event => (
                <tr className={style.event}>
                    <td className={style.actor}>{event.actor}</td>
                    {(function () {
                        switch (event.event) {
                            case types.SearchRequest:
                                return <SearchEvent event={event}/>;
                            case types.Seek:
                                return <SeekEvent event={event}/>;
                            case types.SetPlaying:
                                return <PlayingEvent event={event}/>;
                            case types.PlayerState:
                                return <PlayerEvent event={event}/>;
                            case types.Skip:
                                return <SkipEvent/>;
                            case types.SetVolume:
                                return <VolumeSetEvent event={event}/>;
                            case types.AcceptSongRequest:
                                return <AcceptRequestEvent event={event}/>;
                            case types.SetBanned:
                                return <BanEvent event={event}/>;
                            case types.Vote:
                                return <VoteEvent event={event}/>;
                        }
                    })()}
                </tr>
            ))}
        </tbody></table>
    </div>
);

export default EventLog;
