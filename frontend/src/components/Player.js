import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import {
    faMeh,
    faMusic,
    faPause,
    faPlay,
    faStepForward,
} from '@fortawesome/free-solid-svg-icons';

import classnames from 'classnames';

import { humanDuration } from '../util';
import HeadingStub from './HeadingStub';
import style from './Player.module.scss';
import { Handles, Rail, Slider, Tracks } from 'react-compound-slider';
import { can, Capability } from '../ability';
import { coverUrl } from '../Settings';

library.add(faPlay, faPause, faMeh, faStepForward, faMusic);

const SeekBar = ({ position, duration, onChange, onUpdate }) => {
    const canSeek = can(Capability.Seek);
    return (
        <Slider
            className={style.seek}
            domain={[0, parseInt(duration || 0)]}
            mode={2}
            onChange={(values) => onChange && onChange(values[0])}
            onUpdate={(values) => onUpdate && onUpdate(values[0])}
            values={[parseInt(position || 0)]}
        >
            <Rail>
                {({ getRailProps }) => (
                    <div
                        className={style.rail}
                        {...(canSeek ? getRailProps() : {})}
                    />
                )}
            </Rail>
            <Handles>
                {({ handles, getHandleProps }) => (
                    <div className={style.handles}>
                        {handles.map(({ id, percent }) => (
                            <div
                                key={id}
                                style={{ left: `${percent}%` }}
                                className={style.handle}
                                {...(canSeek ? getHandleProps(id) : {})}
                            />
                        ))}
                    </div>
                )}
            </Handles>
            <Tracks right={false}>
                {({ tracks, getTrackProps }) => (
                    <div className={style.tracks}>
                        {tracks.map(({ id, source, target }) => (
                            <div
                                key={id}
                                className={style.track}
                                style={{
                                    left: `${source.percent}%`,
                                    width: `${
                                        target.percent - source.percent
                                    }%`,
                                }}
                                {...(canSeek ? getTrackProps() : {})}
                            />
                        ))}
                    </div>
                )}
            </Tracks>
        </Slider>
    );
};

const Player = ({ player, song, trackSeek, skipClicked, banClicked }) => {
    const isAdminSong = !song ? false : song.adminIndex !== null;
    return (
        <div className={style.player}>
            <HeadingStub icon={player.isPlaying ? 'play' : 'pause'}>
                <span className={style.heading}>
                    Currently {player.isPlaying ? 'playing' : 'paused'}
                </span>
            </HeadingStub>
            {!song ? (
                <div className={style.emptyContent}>
                    <FontAwesomeIcon
                        icon="music"
                        size="2x"
                        className={style.paddedIcon}
                    />
                    Nothing's playing.
                </div>
            ) : (
                ''
            )}
            {song ? (
                <div className={style.songCard}>
                    <div
                        className={style.coverArt}
                        style={{ backgroundImage: `url(${coverUrl(song)})` }}
                        title="Cover art"
                    />
                    <span className={style.title} title={song.song.title}>
                        {song.song.title}
                    </span>
                    <p className={style.infoLine}>
                        <span
                            className={song.song.artist ? '' : style.noArtist}
                            title={song.song.artist}
                        >
                            {song.song.artist
                                ? song.song.artist
                                : 'Unknown artist'}
                        </span>
                        {song.song.explicit ? (
                            <span
                                className={style.tag}
                                title="Contains explicit lyrics"
                            >
                                explicit
                            </span>
                        ) : (
                            ''
                        )}
                        <span
                            className={style.tag}
                            title={`played ${song.playCount} times`}
                        >
                            <FontAwesomeIcon icon="music" size="xs" />{' '}
                            {song.playCount}
                        </span>
                    </p>

                    <div className={style.progress}>
                        <span className={style.position}>
                            {humanDuration(player.position)}
                        </span>
                        <SeekBar
                            position={player.position}
                            duration={player.duration}
                            onChange={(e) => trackSeek(e)}
                        />
                        <span className={style.duration}>
                            {humanDuration(player.duration)}
                        </span>
                    </div>

                    <div className={style.ban}>
                        {!isAdminSong && can(Capability.Ban) && (
                            <button
                                className={classnames(
                                    style.button,
                                    style.banButton
                                )}
                                onClick={() =>
                                    banClicked(song) || skipClicked()
                                }
                                title="Ban this song (cannot be played nor searched)"
                            >
                                <FontAwesomeIcon icon="gavel" />
                            </button>
                        )}
                    </div>
                </div>
            ) : (
                ''
            )}
        </div>
    );
};

export default Player;
