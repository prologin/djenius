"""
An asyncio protocol for mpv-over-TCP and a client.
"""

import asyncio
import itertools
import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


class MpvError(ValueError):
    pass


@dataclass
class MpvPositionChanged:
    position: int


@dataclass
class MpvVolumeChanged:
    volume: int


@dataclass
class MpvIsPlayingChanged:
    is_playing: bool


@dataclass
class MpvFileLoaded:
    pass


@dataclass
class MpvFileEnded:
    pass


@dataclass
class MpvIsAvailable:
    is_available: bool


class MpvJsonProtocol(asyncio.Protocol):
    def __init__(self):
        self._connection_status = asyncio.Queue()
        self._queue = asyncio.Queue()
        self._inbound_buf = b""

    def connection_made(self, transport):
        self._connection_status.put_nowait(True)
        logger.debug("Connection made to mpv")

    def connection_lost(self, exc):
        self._connection_status.put_nowait(False)
        logger.debug("Connection lost to mpv")

    def data_received(self, data):
        """
        Accumulate data in a the buffer, split individual lines, parse complete
        lines from JSON and put them in the queue.
        """
        self._inbound_buf += data
        parts = self._inbound_buf.split(b"\n")
        while len(parts) > 1:
            head, *parts = parts
            self._queue.put_nowait(json.loads(head.decode()))
        self._inbound_buf = parts[0]


class MpvClient:
    """
    A client for mpv.

    Relevant events are sent through the :attr:`event_queue` channel.
    The public API defines some commands.
    """

    def __init__(self):
        self.event_queue = asyncio.Queue()

    async def connect_and_run(self, host, port):
        loop = asyncio.get_event_loop()

        def protocol_factory():
            return MpvJsonProtocol()

        self.transport, self.protocol = await loop.create_connection(
            protocol_factory, host, port
        )
        self.tasks = [
            asyncio.create_task(self._status_reader()),
            asyncio.create_task(self._message_reader()),
        ]
        done, pending = await asyncio.wait(
            self.tasks, return_when=asyncio.FIRST_EXCEPTION,
        )
        exc = [f.exception() for f in done]
        logging.info("mpv connect_and_run returned; exceptions if any: %r", exc)

    async def _status_reader(self):
        while True:
            try:
                available = await self.protocol._connection_status.get()
                if available:
                    await self._init()
                else:
                    await self._close()
                await self.event_queue.put(MpvIsAvailable(available))
            except asyncio.CancelledError:
                return

    async def _message_reader(self):
        while True:
            try:
                message = await self.protocol._queue.get()
            except asyncio.CancelledError:
                return
            if message.get("event"):
                await self._handle_event(message)
            else:
                id = message["request_id"]
                try:
                    await self.pending_requests[id].put(message)
                except KeyError:
                    logger.error("received unexpected response for request %s", id)

    async def _init(self):
        self.pending_requests = {}
        self.id = itertools.count(1)
        await asyncio.wait(
            [self._observe(prop) for prop in ("time-pos", "volume", "pause")]
        )

    async def _close(self):
        [task.cancel() for task in self.tasks]
        self.transport.close()

    async def _call(self, *command) -> Any:
        this_id = next(self.id)
        channel: asyncio.Queue
        channel = self.pending_requests[this_id] = asyncio.Queue(1)
        message = (
            json.dumps({"request_id": this_id, "command": list(command)}).encode()
            + b"\n"
        )
        self.transport.write(message)
        try:
            response: dict = await asyncio.wait_for(channel.get(), 1.5)
            success = response.get("error") == "success"
            if not success:
                error = response.get("error", "unknown")
                raise MpvError(f"mpv error for {command}: {error}")
            return response
        except asyncio.TimeoutError:
            raise MpvError(f"timeout waiting for result for {command}") from None
        finally:
            self.pending_requests.pop(this_id)

    async def _handle_event(self, event):
        if event["event"] == "property-change":
            if event["name"] == "time-pos":
                try:
                    pos = int(event["data"])
                    await self.event_queue.put(MpvPositionChanged(pos))
                except TypeError:
                    pass
            elif event["name"] == "volume":
                try:
                    volume = int(event["data"])
                    await self.event_queue.put(MpvVolumeChanged(volume))
                except TypeError:
                    pass
            elif event["name"] == "pause":
                await self.event_queue.put(MpvIsPlayingChanged(not event["data"]))
        elif event["event"] == "file-loaded":
            await self.event_queue.put(MpvFileLoaded())
        elif event["event"] == "end-file":
            await self.event_queue.put(MpvFileEnded())

    async def _set_property(self, name: str, value):
        await self._call("set_property", name, value)

    async def _observe(self, name: str):
        await self._call("observe_property", next(self.id), name)

    async def load_uri(self, uri):
        await self._call("loadfile", uri, "replace")

    async def resume(self):
        await self._set_property("pause", False)

    async def pause(self):
        await self._set_property("pause", True)

    async def stop(self):
        await self._call("stop")

    async def seek(self, position):
        await self._call("seek", position, "absolute")

    async def set_volume(self, volume: int):
        await self._set_property("volume", volume)
