/**
 * Wraps a list so that it can maintain a "public" vs. "real" state. When "locked", the real state is updated
 * when receiving updates, but the public state remains unchanged. On "release", the real state is copied over the
 * public state to go back to sync.
 * This is useful for the "up next" queue, because we don't want to update the queue (reorder songs) while the user is
 * aiming at a button: otherwise there would be a race between clicking (say "upvote") and the song at that position
 * changing because of external events.
 */
export const Lockable = {
    make: (initial = []) => ({
        _initial: [...initial],
        _real: [...initial],
        public: [...initial],
        _locked: false,
    }),
    reset: (state) => Lockable._maybe_update(state, (q) => state._initial),
    update: (state, newState, urgent) =>
        Lockable._maybe_update(
            state,
            (q) => newState,
            urgent === undefined ? false : urgent
        ),
    updateItem: (state, newItem, keyFunc) => ({
        ...state,
        _real: state._real.map(Lockable._applier(newItem, keyFunc)),
        public: state.public.map(Lockable._applier(newItem, keyFunc)),
    }),
    appendItem: (state, newItem) =>
        Lockable._maybe_update(state, (q) => [...q, newItem]),
    lock: (state) => ({
        ...state,
        _locked: true,
    }),
    release: (state) => ({
        ...state,
        _locked: false,
        public: state._real,
    }),
    _applier: (newItem, keyFunc) => (oldItem) =>
        keyFunc(oldItem) === keyFunc(newItem) ? newItem : oldItem,
    _maybe_update: (state, newStateFunc, urgent) => ({
        ...state,
        _real: newStateFunc(state._real),
        public:
            !urgent && state._locked
                ? state.public
                : newStateFunc(state.public),
    }),
};
