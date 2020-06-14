from dataclasses import dataclass
from typing import Optional
import asyncio
import logging
import re
from dataclasses_json import dataclass_json

from djenius.proto import SongId, CoverId, Song
from djenius.resolver import (
    Resolver,
    _download_chunked,
)
from djenius.settings import Settings

logger = logging.getLogger(__name__)

REGEXP_THUMB = re.compile(r"https://i\.ytimg\.com/vi/(.+?)/.+?\.jpg")


@dataclass_json
@dataclass
class YouTubeDlResult:
    id: str
    title: str
    alt_title: Optional[str]
    creator: Optional[str]
    track: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    view_count: int
    duration: int
    thumbnail: str


def _first_of(*args):
    return next(
        (stripped for arg in args if arg is not None and (stripped := arg.strip())), ""
    )


def _make_song(result: YouTubeDlResult):
    cover_id = REGEXP_THUMB.search(result.thumbnail).group(1) or "unavailable"
    return Song(
        id=SongId(f"youtube/{result.id}"),
        cover_id=CoverId(f"youtube/{cover_id}"),
        title=_first_of(result.track, result.title),
        artist=_first_of(result.artist, result.alt_title),
        album=_first_of(result.album),
        duration=result.duration,
        explicit=False,
        resolver="youtube",
    )


class YouTube(Resolver):
    async def search(self, query: str, limit: int):
        p = await asyncio.create_subprocess_exec(
            "youtube-dl",
            "-4",
            "--no-call-home",
            "--ignore-config",
            "--skip-download",
            "--dump-json",
            "--format=best",
            "--match-filter=!is_live",
            f"ytsearch{limit}:{query}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await p.communicate()
        results = [YouTubeDlResult.from_json(line) for line in stdout.splitlines()]
        return [
            song
            for result in results
            if (song := _make_song(result)).duration < Settings.MAX_SONG_DURATION
        ]

    async def download(self, opaque: str):
        p = await asyncio.create_subprocess_exec(
            "youtube-dl",
            "-4",
            "--no-call-home",
            "--ignore-config",
            "--format=bestaudio",
            "-g",
            f"https://www.youtube.com/watch?v={opaque}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await p.communicate()
        url = stdout.strip().decode().splitlines(keepends=False)[0]
        return _download_chunked(url)

    async def cover(self, opaque: str):
        return _download_chunked(f"https://i.ytimg.com/vi/{opaque}/default.jpg")
