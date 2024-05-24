import React from 'react';
import classnames from 'classnames';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { Slider, Rail, Handles, Tracks, Ticks } from 'react-compound-slider';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faGamepad, faVolumeUp } from '@fortawesome/free-solid-svg-icons';

import style from './Controller.module.scss';
import HeadingStub from './HeadingStub';
import Can from './Can';
import { can, Capability, ControlCapabilities } from '../ability';

library.add(faGamepad, faVolumeUp);

const Volume = ({ volume, onChange, onUpdate }) => (
    <Slider
        className={style.volume}
        domain={[0, 120]}
        step={5}
        mode={2}
        disabled={true}
        onChange={(values) => onChange && onChange(values[0])}
        onUpdate={(values) => onUpdate && onUpdate(values[0])}
        values={[volume]}
    >
        <Rail>
            {({ getRailProps }) => (
                <div className={style.rail} {...getRailProps()} />
            )}
        </Rail>
        <Handles>
            {({ handles, getHandleProps }) => (
                <div className="handles">
                    {handles.map(({ id, percent }) => (
                        <div
                            key={id}
                            style={{ left: `${percent}%` }}
                            className={style.handle}
                            {...getHandleProps(id)}
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
                                width: `${target.percent - source.percent}%`,
                            }}
                            {...getTrackProps()}
                        />
                    ))}
                </div>
            )}
        </Tracks>
        <Ticks values={[100]}>
            {({ ticks }) => (
                <div className={style.ticks}>
                    {ticks.map((tick) => (
                        <div
                            key={tick.id}
                            style={{ left: `${tick.percent}%` }}
                            className={style.tick}
                        />
                    ))}
                </div>
            )}
        </Ticks>
    </Slider>
);

const Controller = ({
    player,
    playPauseClicked,
    skipClicked,
    volumeChanged,
    muteClicked,
}) => {
    const canControl = ControlCapabilities.some(can);
    return (
        canControl && (
            <div className={style.controller}>
                <HeadingStub icon="gamepad">
                    <span className={style.heading}>Control the radio</span>
                </HeadingStub>
                <div className={style.body}>
                    <Can I={Capability.Pause}>
                        <button
                            className={classnames(
                                style.button,
                                style.playPause
                            )}
                            onClick={() => playPauseClicked(player.isPlaying)}
                        >
                            <FontAwesomeIcon
                                icon={player.isPlaying ? 'pause' : 'play'}
                            />{' '}
                            {player.isPlaying ? 'Pause' : 'Play'}
                        </button>
                    </Can>
                    <Can I={Capability.Skip}>
                        <button
                            className={classnames(style.button, style.next)}
                            onClick={() => skipClicked()}
                        >
                            <FontAwesomeIcon icon="step-forward" /> Skip
                        </button>
                    </Can>
                    <Can I={Capability.Volume}>
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                            <Can I={Capability.Pause}>
                                <FontAwesomeIcon
                                    icon="volume-up"
                                    className={style.volumeIcon}
                                    onClick={() => muteClicked()}
                                />
                            </Can>
                            <Volume
                                volume={player.volume}
                                onUpdate={volumeChanged}
                            />
                        </div>
                    </Can>
                </div>
            </div>
        )
    );
};

export default Controller;
