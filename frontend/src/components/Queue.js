import React from 'react';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faListAlt, faMeh } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import posed, { PoseGroup } from 'react-pose';

import SongCard from './SongCard';
import HeadingStub from './HeadingStub';
import style from './Queue.module.scss';
import { songKey } from '../util';

library.add(faListAlt, faMeh);

const ForwardRefSongCard = React.forwardRef((props, ref) => (
    <div ref={ref}>
        <SongCard {...props} />
    </div>
));
const AnimatedSongCard = posed(ForwardRefSongCard)({
    flip: { transition: { ease: 'easeOut' } },
});

const Queue = ({
    queue,
    voteUpClicked,
    voteDownClicked,
    banClicked,
    addToAdminQueueClicked,
    removeFromAdminQueueClicked,
    moveUpAdminQueueClicked,
    moveDownAdminQueueClicked,
    handleMouseEnter,
    handleMouseLeave,
}) => (
    <div className={style.queue}>
        <HeadingStub icon="list-alt">
            <span className={style.heading}>Up next</span>
        </HeadingStub>
        {!queue.length ? (
            <div className={style.emptyContent}>
                <FontAwesomeIcon
                    icon="meh"
                    size="2x"
                    className={style.paddedIcon}
                />
                Queue is empty.
            </div>
        ) : (
            ''
        )}
        <div
            className={style.scrollArea}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
        >
            <PoseGroup animateOnMount={false}>
                {queue.map((song) => (
                    <AnimatedSongCard
                        key={songKey(song)}
                        song={song}
                        voteUpClicked={voteUpClicked}
                        voteDownClicked={voteDownClicked}
                        banClicked={banClicked}
                        addToAdminQueueClicked={addToAdminQueueClicked}
                        removeFromAdminQueueClicked={
                            removeFromAdminQueueClicked
                        }
                        moveUpAdminQueueClicked={moveUpAdminQueueClicked}
                        moveDownAdminQueueClicked={moveDownAdminQueueClicked}
                    />
                ))}
            </PoseGroup>
        </div>
    </div>
);

export default Queue;
