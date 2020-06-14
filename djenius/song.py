"""
Layer of abstraction that deals with maintaining the ranked songs, the votes, etc.
"""

import asyncio
import datetime
import dataclasses
import pickle

from sortedcontainers import SortedDict  # type: ignore
import itertools
from typing import (
    Optional as O,
    MutableMapping,
    List,
    Iterable,
    Collection,
    Callable,
    Awaitable,
    Mapping,
    Any,
    Iterator,
    BinaryIO,
)

from djenius.fts import ISongSearch
from djenius.proto import StatefulSong, SongId, SongState, Song, UserId, User
from djenius.auth import AuthProvider


@dataclasses.dataclass(eq=False, order=False)
class ISong:
    """Internal song. Not for use outside this module.

    Has some denormalized state (eg. vote_cache) for performance.
    """

    song: Song
    state: SongState = SongState.new
    play_count: int = 0
    votes: MutableMapping[UserId, int] = dataclasses.field(default_factory=dict)
    vote_cache: int = 0
    added_by: O[UserId] = None
    added_on: O[datetime.datetime] = None
    last_play_date: O[datetime.datetime] = None

    def rank(self):
        """The song scoring function. Smaller means higher in the playlist.

        The smallest rank will be the next song to be played."""
        return (
            # Penalty for unavailable songs.
            0 if self.state is SongState.available else 1,
            # Most voted first.
            -self.vote_cache,
            # Least played first.
            +self.play_count,
            self.added_on,
        )

    def clear_votes(self):
        self.votes.clear()
        self.vote_cache = 0

    def set_vote(self, user_id: str, value: int):
        if value == 0:
            self.votes.pop(user_id, None)
        else:
            self.votes[user_id] = value
        self.vote_cache = sum(self.votes.values())

    def __eq__(self, other):
        return self.song == other.song


class SongRegistry:
    def __init__(self, song_search: ISongSearch, auth_provider: AuthProvider):
        # State.
        self._songs: MutableMapping[SongId, ISong] = SortedDict(self._rank_lookup)
        self._song_map: MutableMapping[SongId, ISong] = {}
        self._admin_songs: List[ISong] = []

        # Helpers.
        self._song_search = song_search
        self._auth_provider = auth_provider

        # Signals.
        self.song_updated_signal = asyncio.Queue(maxsize=1)

    def dump_state(self, fobj: BinaryIO):
        state = {
            "song_map": self._song_map,
            "admin_songs": [isong.song.id for isong in self._admin_songs],
        }
        pickle.dump(state, fobj)

    async def load_state(self, fobj: BinaryIO):
        state = pickle.load(fobj)

        self._songs.clear()
        for id, isong in state["song_map"].items():
            self._song_map[id] = isong
            self._songs[id] = isong
            await self._song_search.index(isong.song)

        self._admin_songs.clear()
        self._admin_songs.extend(self._song_map[id] for id in state["admin_songs"])

    async def search(self, query: str, n: int, user: User) -> Iterable[StatefulSong]:
        def searcher(hit_ids):
            for song_id in hit_ids:
                song = self._song_map.get(song_id)
                if not song:
                    continue
                if user.can_see_song_in_search(song.state):
                    yield song

        hit_ids = await self._song_search.search(query, n)
        return self._for_user_display_it(searcher(hit_ids), user)

    async def add(self, song: Song, user: User, state: SongState) -> O[StatefulSong]:
        if song.id not in self._song_map:
            self._song_map[song.id] = isong = ISong(
                song=song,
                state=state,
                added_by=user.id,
                added_on=datetime.datetime.now(),
            )
            self._songs[song.id] = isong
            await self._song_search.index(song)
            await self._song_updated(song.id)
        return self.for_user_display(song.id, user)

    async def add_all(
        self, songs: Iterable[Song], user: User
    ) -> Collection[StatefulSong]:
        added = [await self.add(song, user, SongState.new) for song in songs]
        return [
            song
            for song in added
            if song is not None and user.can_see_song_in_search(song.state)
        ]

    async def accept_song(self, id: SongId, user: User) -> O[StatefulSong]:
        async def apply(song: ISong):
            if song.state is not SongState.new:
                return
            song.state = SongState.available

        return self.for_user_display(await self._modify(id, apply), user)

    async def upvote_song(self, id: SongId, user: User) -> O[StatefulSong]:
        async def apply(song: ISong):
            if song.state is SongState.banned:
                return
            self._maybe_auto_accept_song(song)
            song.set_vote(user.id, 1)

        return self.for_user_display(await self._modify(id, apply), user)

    async def downvote_song(self, id: SongId, user: User) -> O[StatefulSong]:
        async def apply(song: ISong):
            self._maybe_auto_accept_song(song)
            if song.state is not SongState.available:
                return
            song.set_vote(user.id, -1)

        return self.for_user_display(await self._modify(id, apply), user)

    async def unvote_song(self, id: SongId, user: User) -> O[StatefulSong]:
        async def apply(song: ISong):
            self._maybe_auto_accept_song(song)
            song.set_vote(user.id, 0)

        return self.for_user_display(await self._modify(id, apply), user)

    async def ban_song(self, id: SongId, user: User) -> O[StatefulSong]:
        async def apply(song: ISong):
            song.clear_votes()
            song.state = SongState.banned

        return self.for_user_display(await self._modify(id, apply), user)

    async def unban_song(self, id: SongId, user: User) -> O[StatefulSong]:
        async def apply(song: ISong):
            song.state = SongState.available

        return self.for_user_display(await self._modify(id, apply), user)

    async def mark_song_played(self, id: SongId) -> None:
        async def apply(song: ISong):
            was_from_admin = self.admin_queue_remove(id)
            if not was_from_admin:
                song.clear_votes()
            song.play_count += 1
            song.last_play_date = datetime.datetime.now()

        await self._modify(id, apply)

    def admin_queue_insert(self, id: SongId, position: O[int] = None) -> None:
        try:
            song = self._song_map[id]
        except KeyError:
            return
        if position is None:
            self._admin_songs.append(song)
        else:
            self._admin_songs.insert(position, song)

    def admin_queue_remove(self, id: SongId) -> bool:
        try:
            index = [song.song.id for song in self._admin_songs].index(id)
        except ValueError:
            return False
        self._admin_songs.pop(index)
        return True

    def admin_queue_move_up(self, position: int) -> bool:
        if position <= 0:
            return False
        self._admin_songs.insert(position - 1, self._admin_songs.pop(position))
        return True

    def admin_queue_move_down(self, position: int) -> bool:
        if position >= len(self._admin_songs) - 1:
            return False
        self._admin_songs.insert(position + 1, self._admin_songs.pop(position))
        return True

    def all_songs(self, n: int, offset: int, user: User):
        c = 0
        slice = self._songs.islice(offset)
        for id in slice:
            song = self._songs[id]
            if user.can_see_song_in_search(song.state):
                yield self.for_user_display(id, user)
                c += 1
                if c == n:
                    break
        if next(slice, None) is None:
            yield None

    def top_songs(self, n: int, user: User):
        top_songs = itertools.islice(
            self._for_user_display_it(self._available_user_voted_top_songs(), user),
            0,
            n,
        )
        all_songs = itertools.chain(
            self._for_user_display_it(self._admin_songs, user, is_admin=True), top_songs
        )
        return (
            song
            for song in all_songs
            if user.can_see_song_in_queue(song.state, song.admin_index is not None)
        )

    def top_song(self) -> O[StatefulSong]:
        all_songs = itertools.chain(
            self._admin_songs, self._available_user_voted_top_songs()
        )
        song = next(all_songs, None)
        if song is None:
            return None
        return self.for_anonymous_display(song.song.id)

    def _stateful_kwargs(self, song: ISong) -> Mapping[str, Any]:
        return dict(
            song=song.song,
            state=song.state,
            review_required=song.song.review_required(),
            added_by=None
            if song.added_by is None
            else self._auth_provider.get_user(song.added_by).id,
            added_on="" if song.added_on is None else song.added_on.isoformat(),
            play_count=song.play_count,
            votes=song.vote_cache,
        )

    def for_anonymous_display(self, id: SongId) -> O[StatefulSong]:
        song = self._song_map.get(id)
        if song is None:
            return None
        return StatefulSong(
            **self._stateful_kwargs(song), user_vote=0,  # type: ignore
        )

    def for_user_display(self, id: O[SongId], user: User) -> O[StatefulSong]:
        if id is None:
            return None
        song = self._song_map.get(id)
        if song is None:
            return None
        return StatefulSong(
            **self._stateful_kwargs(song),
            user_vote=song.votes.get(user.id, 0),  # type: ignore
        )

    def _for_user_display_it(
        self, songs: Iterable[ISong], user: User, is_admin: bool = False
    ) -> Iterator[StatefulSong]:
        admin_counter = itertools.count()
        for song in songs:
            admin_index: O[int]
            if is_admin:
                admin_index = next(admin_counter)
            else:
                admin_index = None
            yield StatefulSong(
                **self._stateful_kwargs(song),
                user_vote=song.votes.get(user.id, 0),  # type: ignore
                admin_index=admin_index,  # type: ignore
            )

    def _available_user_voted_top_songs(self) -> Iterator[ISong]:
        for song in self._songs.values():
            if song.state is SongState.available:
                yield song

    def _maybe_auto_accept_song(self, song: ISong) -> None:
        if song.state is SongState.new and not song.song.review_required():
            song.state = SongState.available

    def _rank_lookup(self, key: SongId):
        return self._song_map[key].rank()

    async def _modify(
        self, id: SongId, func: Callable[[ISong], Awaitable[None]]
    ) -> O[SongId]:
        song = self._song_map.get(id)
        if song is None:
            return None
        self._songs.pop(id)
        await func(song)
        self._song_map[id] = song
        self._songs[id] = song
        await self._song_updated(id)
        return id

    async def _song_updated(self, id: SongId) -> None:
        await self.song_updated_signal.put(id)
