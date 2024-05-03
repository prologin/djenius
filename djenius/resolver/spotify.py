import re
import aiohttp
import logging
import os

from djenius.resolver import Resolver, _download_chunked
from djenius.proto import SongId, CoverId, Song
from djenius.server.settings import Settings

logger = logging.getLogger(__name__)

DESPOTIFY_URL = os.getenv("DESPOTIFY_URL")

URI_REGEXP = re.compile(r"^spotify:track:(.+)$")
THUMB_REGEXP = re.compile(r"^https://i\.scdn\.co/image/(.+)$")


def _make_song(data):
    song_id = URI_REGEXP.search(data["uri"]).group(1)
    cover_id = THUMB_REGEXP.search(data["image"]).group(1)
    return Song(
        id=SongId(f"spotify/{song_id}"),
        cover_id=CoverId(f"spotify/{cover_id}"),
        title=data["name"],
        artist=", ".join(artist["name"] for artist in data["artists"]),
        album=data.get("album", {}).get("name"),
        duration=data["duration"] // 1000,
        explicit=data["explicit"],
        resolver="spotify",
    )


class Spotify(Resolver):
    async def search(self, query: str, limit: int):
        url = f"{DESPOTIFY_URL}/search"
        params = {"q": query, "limit": limit, "category": "tracks"}
        async with aiohttp.ClientSession() as http:
            try:
                async with http.get(url, params=params) as resp:
                    songs = await resp.json()
                    songs = [
                        song
                        for data in songs
                        if (song := _make_song(data)).duration < Settings.MAX_SONG_DURATION
                    ]
                    return songs
            except Exception as e:
                logger.error("Spotify search error")
                return []

    async def download(self, song_id: str):
        return _download_chunked(f"{DESPOTIFY_URL}/download/spotify:track:{song_id}")

    async def cover(self, cover_id: str):
        return _download_chunked(f"https://i.scdn.co/image/{cover_id}")
