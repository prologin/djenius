export const humanDuration = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    return Math.floor(minutes % 60) + ':' +
        ('' + Math.floor(seconds % 60)).padStart(2, '0');
};

export const bySongId = song => song.song.id;
export const songKey = song => song.adminIndex !== null ? `admin-${song.adminIndex}` : bySongId(song);
