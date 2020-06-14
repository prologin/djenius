export const WS_ENDPOINT = `ws://${window.WS_ENDPOINT}/ws`;
export const RECONNECTION_DELAY = 1.5;

let COVER_URL = '';
let LIBRARY_PAGE_SIZE = 1;

export function updateSettings(state) {
    COVER_URL = state.coverUrl;
    LIBRARY_PAGE_SIZE = state.libraryPageSize;
}

export function coverUrl(song) {
    return `${COVER_URL}/${song.song.coverId}`;
}

export function libraryPageSize() {
    return LIBRARY_PAGE_SIZE;
}
