import asyncio
import copy
import logging
import weakref
from typing import Optional, Iterable
import aiohttp.web

from djenius.server.settings import Settings
from djenius.server.song import SongRegistry
from djenius.fts import WhooshSongSearch
from djenius import proto, mpv

logger = logging.getLogger(__name__)


class Main:
    def __init__(self):
        self.auth = None
        self.mpv = mpv.MpvClient()

        self.clients = weakref.WeakSet()
        self.mpv_state = proto.PlayerState()
        self.last_mpv_state = proto.PlayerState()
        self.song_loading_in_mpv: Optional[proto.StatefulSong] = None
        self.next_mpv_update_is_urgent: bool = False
        self.load_timeout_handle = None

    def pre_init(self, app):
        provider = Settings.auth_provider()
        self.auth = provider()
        self.auth.pre_init(app)

    async def on_init(self, app):
        await self.auth.init()

        search = WhooshSongSearch(Settings.WHOOSH_DIRECTORY)
        self.songs = SongRegistry(search, self.auth)

        if Settings.STATE_FILE.exists():
            with Settings.STATE_FILE.open("rb") as f:
                await self.songs.load_state(f)
            logger.info("Loaded state")

        return [
            asyncio.create_task(self.player_state_loop()),
            asyncio.create_task(self.watch_song_updated()),
            asyncio.create_task(self.watch_mpv_events()),
            asyncio.create_task(self.mpv_connect_loop()),
        ]

    async def on_shutdown(self, app):
        with Settings.STATE_FILE.open("wb") as f:
            self.songs.dump_state(f)
        logging.info("Dumped state")
        await self.await_all(
            (ws.close(code=aiohttp.WSCloseCode.GOING_AWAY) for ws in set(self.clients))
        )

    async def mpv_connect_loop(self):
        host, port = Settings.mpv_host_port()
        while True:
            try:
                await self.mpv.connect_and_run(host, port)
            except asyncio.CancelledError:
                return
            except:
                logging.exception("mpv client exception")
            await asyncio.sleep(2)

    async def watch_song_updated(self):
        while True:
            updated_song_id = await self.songs.song_updated_signal.get()
            await self.on_song_updated(updated_song_id)

    async def player_state_loop(self):
        rate = 2
        while True:
            await asyncio.sleep(rate)
            await self.on_player_state_tick(rate)

    async def mpv_load_deadline(self):
        await asyncio.sleep(7)

        if self.song_loading_in_mpv is not None and self.mpv_state.song is None:
            self.song_loading_in_mpv = None
            await self.maybe_load_next_song()

    async def on_player_state_tick(self, rate: int):
        if self.mpv_state.is_playing and self.mpv_state.song is not None:
            self.last_mpv_state.position += rate
            delta = abs(self.mpv_state.position - self.last_mpv_state.position)
            if delta == 1:  # for preventing send update when time is not changed (or the difference is too small)
                self.last_mpv_state.position = self.mpv_state.position

        if self.mpv_state != self.last_mpv_state:
            await self.broadcast_mpv_state()
            self.last_mpv_state = copy.copy(self.mpv_state)

    async def maybe_broadcast_mpv_state(self):
        if self.next_mpv_update_is_urgent:
            await self.broadcast_mpv_state()
        self.next_mpv_update_is_urgent = False

    async def broadcast_mpv_state(self):
        await self.send_broadcast(self.mpv_state)

    def mark_next_mpv_update_as_urgent(self):
        self.next_mpv_update_is_urgent = True

    async def on_song_updated(self, id: proto.SongId):
        def gen_send_to():
            for ws in set(self.clients):
                if id not in ws["subscriptions"]:
                    if "requested" in ws["subscriptions"]:
                        user = self.auth.get_user(ws["user_id"])
                        if user is None or not user.can(proto.Ability.accept):
                            continue
                        if not self.songs.is_song_requested(id):
                            continue
                        song = self.songs.for_user_display(id, user)
                        if not song:
                            continue
                        yield self.send_to(ws, proto.RequestUpdate(song=song))
                    continue

                user = self.auth.get_user(ws["user_id"])
                if user is None:
                    continue
                song = self.songs.for_user_display(id, user)
                if not song:
                    continue
                yield self.send_to(ws, proto.SongUpdate(song=song))

        await self.await_all(gen_send_to())
        await self.maybe_load_next_song()

    async def maybe_load_next_song(self):
        if self.song_loading_in_mpv is not None or self.mpv_state.song is not None:
            return
        top_song = self.songs.top_song()
        if top_song is None:
            logger.debug("I wouldn't mind playing the next song, but queue is empty!")
            return
        self.song_loading_in_mpv = top_song
        # public is need when mpv is not on the same server
        await self.mpv.load_uri(Settings.resolver_track_url(top_song.song.id, public=True))
        # In a few seconds, consider the song failed loading, except if mpv tells us
        # it was successful before that deadline.
        asyncio.create_task(self.mpv_load_deadline())

    async def watch_mpv_events(self):
        while True:
            event = await self.mpv.event_queue.get()
            if isinstance(event, mpv.MpvFileLoaded):
                if not self.song_loading_in_mpv:
                    return
                song_id = self.song_loading_in_mpv.song.id
                self.song_loading_in_mpv = None
                await self.songs.mark_song_played(song_id)
                self.mpv_state.song = self.songs.for_anonymous_display(song_id)
                self.mpv_state.duration = self.mpv_state.song.song.duration
                await self.broadcast_mpv_state()

            if isinstance(event, mpv.MpvFileEnded):
                self.mpv_state.song = None
                await self.broadcast_mpv_state()
                await self.maybe_load_next_song()

            if isinstance(event, mpv.MpvPositionChanged):
                self.mpv_state.position = event.position
                await self.maybe_broadcast_mpv_state()

            if isinstance(event, mpv.MpvVolumeChanged):
                self.mpv_state.volume = event.volume
                await self.maybe_broadcast_mpv_state()

            if isinstance(event, mpv.MpvIsPlayingChanged):
                self.mpv_state.is_playing = event.is_playing
                await self.maybe_broadcast_mpv_state()

            if isinstance(event, mpv.MpvIsAvailable):
                if event.is_available:  # on mpv connect
                    self.mpv_state.song = None
                    await self.broadcast_mpv_state()
                    await self.maybe_load_next_song()

    def list_songs(self, user: proto.User, offset: int):
        yield from self.songs.all_songs(Settings.LIBRARY_PAGE_SIZE, offset, user)
    def request_songs(self, user: proto.User, offset: int):
        yield from self.songs.request_songs(Settings.LIBRARY_PAGE_SIZE, offset, user)
    def banned_songs(self, user: proto.User, offset: int):
        yield from self.songs.banned_songs(Settings.LIBRARY_PAGE_SIZE, offset, user)

    async def search(self, query: str, user: proto.User, channel):
        n = Settings.SEARCH_COUNT
        seen_ids = set()
        query = query.strip()

        def dedupe(songs: Iterable[proto.StatefulSong]):
            for song in songs:
                song_id = song.song.id
                if song_id in seen_ids:
                    continue
                seen_ids.add(song_id)
                yield song

        async def resolver_search(http, resolver: str):
            url = Settings.resolver_search_url(resolver)
            async with http.get(url, params={"q": query, "limit": n}) as resp:
                songs = await resp.json()
                songs = [proto.Song.from_dict(s) for s in songs]  # type: ignore
                songs = list(dedupe(await self.songs.add_all(songs, user)))
                if songs:
                    await channel.put(songs)

        async def local_search():
            songs = list(dedupe(await self.songs.search(query, n, user)))
            if songs:
                await channel.put(songs)

        async with aiohttp.client.ClientSession() as http:
            await asyncio.wait(
                [
                    resolver_search(http, "youtube"),
                    # resolver_search(http, "spotify"),
                    local_search(),
                ]
            )
        await channel.put([])

    async def on_ws_join(self, ws, user: proto.User):
        self.clients.add(ws)
        await self.send_to(
            ws,
            proto.Welcome(
                my_id=user.id,
                caps=list(user.abilities),
                cover_url=Settings.resolver_cover_url(public=True),
                library_page_size=Settings.LIBRARY_PAGE_SIZE,
                login_path=self.auth.get_login_path(),
                logout_path=self.auth.get_logout_path(),
            ),
        )
        await self.send_to(ws, self.mpv_state)

    async def on_ws_part(self, ws):
        self.clients.discard(ws)

    async def on_ws_message(self, ws, data: str):
        user = self.auth.get_user(ws["user_id"])
        if user is None:
            raise aiohttp.web.HTTPForbidden()
        try:
            msg = proto.from_json(data)
        except Exception:
            logger.exception("Could not decode JSON for '%s'", data)
            return

        if isinstance(msg, proto.QueueRequest):
            await self.send_top_songs(ws, user)
            return

        if isinstance(msg, proto.SongSubUnsub):
            if not user.can(proto.Ability.search):
                return
            ws["subscriptions"] -= set(msg.unsubscribe)
            ws["subscriptions"] |= set(msg.subscribe)
            return

        if isinstance(msg, proto.AcceptSongRequest):
            if not user.can(proto.Ability.accept):
                return
            song = await self.songs.accept_song(msg.song_id, user)
            if song is not None:
                await self.send_to(ws, proto.SongUpdate(song))
            return

        if isinstance(msg, proto.Vote):
            song = None
            if msg.value == 1:
                if not user.can(proto.Ability.up_vote):
                    return
                song = await self.songs.upvote_song(msg.song_id, user)
            elif msg.value == -1:
                if not user.can(proto.Ability.down_vote):
                    return
                song = await self.songs.downvote_song(msg.song_id, user)
            elif msg.value == 0:
                if not (user.can(proto.Ability.down_vote) or user.can(proto.Ability.up_vote)):
                    return
                song = await self.songs.unvote_song(msg.song_id, user)
            if song is not None:
                await self.send_to(ws, proto.SongUpdate(song))
            return

        if isinstance(msg, proto.SetBanned):
            if not user.can(proto.Ability.ban):
                return
            if msg.is_banned:
                song = await self.songs.ban_song(msg.song_id, user)
            else:
                song = await self.songs.unban_song(msg.song_id, user)
            if song is not None:
                await self.send_to(ws, proto.SongUpdate(song))
            return

        if isinstance(msg, proto.SetPlaying):
            if not user.can(proto.Ability.pause):
                return
            self.mark_next_mpv_update_as_urgent()
            if msg.is_playing:
                await self.mpv.resume()
            else:
                await self.mpv.pause()
            return

        if isinstance(msg, proto.Seek):
            if not user.can(proto.Ability.seek):
                return
            self.mark_next_mpv_update_as_urgent()
            await self.mpv.seek(msg.position)
            return

        if isinstance(msg, proto.Skip):
            if not user.can(proto.Ability.skip):
                return
            self.mark_next_mpv_update_as_urgent()
            await self.mpv.stop()
            return

        if isinstance(msg, proto.SetVolume):
            if not user.can(proto.Ability.volume):
                return
            self.mark_next_mpv_update_as_urgent()
            await self.mpv.set_volume(msg.volume)
            return

        if isinstance(msg, proto.AdminQueueInsert):
            if not user.can(proto.Ability.admin_queue):
                return
            self.songs.admin_queue_insert(msg.song_id, msg.position)
            await self.send_top_songs(ws, user, urgent=True)
            return

        if isinstance(msg, proto.AdminQueueRemove):
            if not user.can(proto.Ability.admin_queue):
                return
            self.songs.admin_queue_remove(msg.song_id)
            await self.send_top_songs(ws, user, urgent=True)
            return

        if isinstance(msg, proto.AdminQueueMoveUp):
            if not user.can(proto.Ability.admin_queue):
                return
            self.songs.admin_queue_move_up(msg.position)
            await self.send_top_songs(ws, user, urgent=True)
            return

        if isinstance(msg, proto.AdminQueueMoveDown):
            if not user.can(proto.Ability.admin_queue):
                return
            self.songs.admin_queue_move_down(msg.position)
            await self.send_top_songs(ws, user, urgent=True)
            return

        if isinstance(msg, proto.SearchRequest):
            if not user.can(proto.Ability.search):
                return

            if msg.filter == "Library":
                songs = list(self.list_songs(user, msg.offset or 0))
                await self.make_song_list(msg, songs, ws)
                return
            if msg.filter == "Requested":
                songs = list(self.request_songs(user, msg.offset or 0))
                await self.make_song_list(msg, songs, ws)
                return
            if msg.filter == "Banned":
                songs = list(self.banned_songs(user, msg.offset or 0))
                await self.make_song_list(msg, songs, ws)
                return

            channel: asyncio.Queue = asyncio.Queue()

            async def result_sender():
                while True:
                    songs = await channel.get()
                    await self.send_to(
                        ws,
                        proto.SearchResponse(
                            results=songs, opaque=msg.opaque, has_more=False
                        ),
                    )
                    if not songs:  # EOF
                        break

            await asyncio.wait([result_sender(), self.search(msg.query, user, channel)])
            return

    async def make_song_list(self, msg, songs, ws):
        if songs[-1] is None:
            if songs[:-1]:
                await self.send_to(
                    ws,
                    proto.SearchResponse(
                        results=songs[:-1], opaque=msg.opaque
                    ),
                )
            await self.send_to(
                ws, proto.SearchResponse(results=[], opaque=msg.opaque)
            )
        else:
            await self.send_to(
                ws,
                proto.SearchResponse(
                    results=songs, opaque=msg.opaque, has_more=True
                ),
            )
        return

    async def send_top_songs(self, ws, user: proto.User, urgent: bool = False):
        top = list(self.songs.top_songs(Settings.QUEUE_SIZE, user))
        await self.send_to(ws, proto.QueueResponse(queue=top, urgent=urgent))

    async def process_message(self, semaphore, ws, message):
        async with semaphore:
            await self.on_ws_message(ws, message)

    async def worker(self, semaphore, message_queue):
        while True:
            ws, message = await message_queue.get()
            await self.process_message(semaphore, ws, message)
            message_queue.task_done()

    async def ws_handler(self, request: aiohttp.web.Request):
        user_id = await self.auth.get_user_id(request)
        user = self.auth.get_user(user_id)
        if user is None:
            raise aiohttp.web.HTTPForbidden()
        ws = aiohttp.web.WebSocketResponse(autoping=True, heartbeat=4)
        ws["user_id"] = user_id
        ws["subscriptions"] = set()
        await ws.prepare(request)
        try:
            await self.on_ws_join(ws, user)
            # Start workers to process messages
            message_queue = asyncio.Queue()
            semaphore = asyncio.Semaphore(3)
            for _ in range(3):
                asyncio.create_task(self.worker(semaphore, message_queue))
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await message_queue.put((ws, msg.data))
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.warning("WS error", ws.exception())
        finally:
            await self.on_ws_part(ws)
        return ws

    async def send_to(self, ws, message):
        data = proto.to_json(message)
        await ws.send_str(data)

    async def send_broadcast(self, message):
        await self.await_all((self.send_to(ws, message) for ws in set(self.clients)))

    async def await_all(self, coros):
        coros = list(coros)
        if coros:
            await asyncio.wait(coros)
