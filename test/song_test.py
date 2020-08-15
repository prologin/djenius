import asyncio
from typing import Optional

import pytest
from aiohttp import web

from djenius.server.song import SongRegistry
from djenius.proto import SongState, Song, UserId, Ability, User
from djenius.fts import WhooshSongSearch
from djenius.auth import AuthProvider


async def _consume(signal):
    while True:
        await signal.get()


@pytest.fixture
def song_search(tmp_path):
    dir = tmp_path / "whoosh"
    return WhooshSongSearch(dir)


@pytest.fixture
def u1():
    return User(id="zopieux", abilities={Ability.ban})


@pytest.fixture
def u2():
    return User(id="seirl")


@pytest.fixture
def auth_provider(u1, u2):
    class Provider(AuthProvider):
        def get_user_id(self, request: web.Request) -> Optional[UserId]:
            raise NotImplementedError()

        def get_user(self, user_id: Optional[UserId]) -> Optional[User]:
            return {u.id: u for u in [u1, u2]}.get(user_id)

    return Provider()


@pytest.yield_fixture
async def registry(song_search, auth_provider):
    sr = SongRegistry(song_search=song_search, auth_provider=auth_provider)
    t = asyncio.create_task(_consume(sr.song_updated_signal))
    yield sr
    t.cancel()


@pytest.fixture
def s1():
    return Song(
        id="song1",
        cover_id="",
        title="The Title",
        artist="The Artist",
        album="The album",
        duration=123,
        explicit=False,
        resolver="spotify",
    )


@pytest.fixture
def s2():
    return Song(
        id="song2",
        cover_id="",
        title="The Title",
        artist="The Artist",
        album="The album",
        duration=123,
        explicit=True,
        resolver="youtube",
    )


@pytest.mark.asyncio
async def test_add_song(registry: SongRegistry, u1, s1):
    stateful = await registry.add(s1, u1, SongState.available)
    assert stateful.song is s1
    assert stateful.state is SongState.available
    assert stateful.votes == 0
    assert stateful.play_count == 0
    assert stateful.review_required is False
    assert stateful.user_vote == 0


@pytest.mark.asyncio
async def test_vote_single_song(registry: SongRegistry, u1, u2, s1):
    await registry.add(s1, u1, SongState.available)

    ss = await registry.upvote_song(s1.id, u1)
    assert ss.song is s1
    assert ss.votes == 1
    assert ss.user_vote == 1

    ss = await registry.downvote_song(s1.id, u2)
    assert ss.song is s1
    assert ss.votes == 0
    assert ss.user_vote == -1

    ss = await registry.upvote_song(s1.id, u2)
    assert ss.song is s1
    assert ss.votes == 2
    assert ss.user_vote == 1


@pytest.mark.asyncio
async def test_vote_two_users(registry: SongRegistry, u1, u2, s1, s2):
    await registry.add(s1, u1, SongState.available)
    await registry.add(s2, u2, SongState.available)

    await registry.upvote_song(s1.id, u1)
    await registry.upvote_song(s1.id, u2)
    ss = registry.top_song()
    assert ss.song is s1
    assert ss.votes == 2
    await registry.unvote_song(s1.id, u1)
    await registry.unvote_song(s1.id, u2)

    await registry.upvote_song(s2.id, u1)
    await registry.upvote_song(s2.id, u2)
    ss = registry.top_song()
    assert ss.song is s2
    assert ss.votes == 2


@pytest.mark.asyncio
async def test_admin_ops(registry: SongRegistry, u1, s1, s2):
    await registry.add(s1, u1, SongState.available)
    await registry.add(s2, u1, SongState.available)
    await registry.upvote_song(s1.id, u1)

    a, b = registry.top_songs(99, u1)
    assert [a.song, b.song] == [s1, s2]

    registry.admin_queue_insert(s1.id)
    registry.admin_queue_insert(s2.id)
    registry.admin_queue_insert(s2.id)

    a, b, c, d, *_ = registry.top_songs(99, u1)
    assert [a.song, b.song, c.song, d.song] == [s1, s2, s2, s1]

    registry.admin_queue_insert(s1.id, 1)
    a, b, c, d, *_ = registry.top_songs(99, u1)
    assert [a.song, b.song, c.song, d.song] == [s1, s1, s2, s2]

    registry.admin_queue_move_up(2)
    a, b, c, d, *_ = registry.top_songs(99, u1)
    assert [a.song, b.song, c.song, d.song] == [s1, s2, s1, s2]

    registry.admin_queue_move_down(0)
    a, b, c, d, *_ = registry.top_songs(99, u1)
    assert [a.song, b.song, c.song, d.song] == [s2, s1, s1, s2]

    registry.admin_queue_remove(s1.id)
    a, b, c, *_ = registry.top_songs(99, u1)
    assert [a.song, b.song, c.song] == [s2, s1, s2]

    registry.admin_queue_remove(s2.id)
    a, b, *_ = registry.top_songs(99, u1)
    assert [a.song, b.song] == [s1, s2]


@pytest.mark.asyncio
async def test_mark_played(registry: SongRegistry, u1, s1, s2):
    await registry.add(s1, u1, SongState.available)
    await registry.add(s2, u1, SongState.available)
    await registry.upvote_song(s1.id, u1)

    a, b, *_ = registry.top_songs(99, u1)
    assert [a.song, b.song] == [s1, s2]
    assert a.play_count == 0
    assert a.votes == 1

    await registry.mark_song_played(s1.id)

    a, b, *_ = registry.top_songs(99, u1)
    assert [a.song, b.song] == [s2, s1]
    assert b.play_count == 1
    assert b.votes == 0
    assert a.play_count == 0

    await registry.mark_song_played(s1.id)
    a, b, *_ = registry.top_songs(99, u1)
    assert [a.song, b.song] == [s2, s1]
    assert b.play_count == 2


@pytest.mark.asyncio
async def test_ban(registry: SongRegistry, u1, s1, s2):
    await registry.add(s1, u1, SongState.available)
    await registry.add(s2, u1, SongState.available)
    await registry.upvote_song(s1.id, u1)

    ts = list(registry.top_songs(99, u1))
    assert len(ts) == 2
    assert ts[0].song == s1
    assert ts[0].votes == 1

    ss = await registry.ban_song(s1.id, u1)
    assert ss.state is SongState.banned
    assert ss.votes == 0

    ts = list(registry.top_songs(99, u1))
    assert len(ts) == 1
    assert ts[0].song == s2

    ss = await registry.unban_song(s1.id, u1)
    assert ss.state is SongState.available
    assert ss.votes == 0


@pytest.mark.asyncio
async def test_accept(registry: SongRegistry, u1, s1, s2):
    await registry.add(s1, u1, SongState.new)
    await registry.add(s2, u1, SongState.new)
    assert len(list(registry.top_songs(99, u1))) == 0

    ss = await registry.accept_song(s1.id, u1)
    assert ss.state is SongState.available
    assert ss.added_by == u1.id
    assert len(list(registry.top_songs(99, u1))) == 1


@pytest.mark.asyncio
async def test_full_test_search(registry: SongRegistry, u1):
    s1 = Song(
        id="song1",
        cover_id="",
        title="Stressed Out",
        artist="21 pilots",
        album="Blurryface",
        duration=123,
        explicit=False,
        resolver="spotify",
    )
    s2 = Song(
        id="song2",
        cover_id="",
        title="Carré magique",
        artist="Cliché",
        album="",
        duration=123,
        explicit=False,
        resolver="spotify",
    )
    s3 = Song(
        id="song3",
        cover_id="",
        title="Bouger bouger",
        artist="Magique System",
        album="",
        duration=123,
        explicit=False,
        resolver="spotify",
    )
    await registry.add(s1, u1, SongState.available)
    await registry.add(s2, u1, SongState.available)
    await registry.add(s3, u1, SongState.available)

    def get_ids(hits):
        return set(h.song.id for h in hits)

    assert get_ids(await registry.search("", 99, u1)) == set()
    assert get_ids(await registry.search("blurce", 99, u1)) == set()
    assert get_ids(await registry.search("stressed", 99, u1)) == {s1.id}
    assert get_ids(await registry.search("streSSSd", 99, u1)) == {s1.id}
    assert get_ids(await registry.search("blurface", 99, u1)) == {s1.id}
    assert get_ids(await registry.search("cliché", 99, u1)) == {s2.id}
    assert get_ids(await registry.search("cliche", 99, u1)) == {s2.id}
    assert get_ids(await registry.search("carr magiqu", 99, u1)) == {s2.id}
    assert get_ids(await registry.search("magique", 99, u1)) == {s2.id, s3.id}
