import binascii
import io
import os
import shutil

import pytest

from djenius.resolver.spotify import Spotify
from djenius.resolver.youtube import YouTube


def strip_resolver(identifier: str):
    return identifier.split("/", 1)[1]


async def _copy_to_file(gen, f):
    async for chunk in (await gen):
        f.write(chunk)


async def base_test_resolver(resolver):
    await resolver.setup()

    query = "The Shortest Song In The World vinnie"
    results = await resolver.search(query, 1)
    assert len(results) > 0
    song = results[0]

    cover_data = io.BytesIO()
    await _copy_to_file(resolver.cover(strip_resolver(song.cover_id)), cover_data)
    # JPEG header.
    assert (
        binascii.hexlify(cover_data.getvalue()[:64])
        .decode()
        .startswith("ffd8ffe000104a4649460001")
    )

    song_data = io.BytesIO()
    await _copy_to_file(resolver.download(strip_resolver(song.id)), song_data)
    header = binascii.hexlify(song_data.getvalue()[:64]).decode()
    # Ogg or EBML (Matroska) or MPEG-4 header.
    assert (
        header.startswith("4f6767530002")
        or header.startswith("6572726f")
        or header.startswith("1a45")
        or header.startswith("0000001866747970")
    )

    await resolver.cleanup()


@pytest.mark.skipif(
    shutil.which("youtube-dl") is None, reason="youtube-dl binary not available"
)
@pytest.mark.asyncio
async def test_youtube():
    await base_test_resolver(YouTube())


@pytest.mark.skipif(
    os.getenv("DESPOTIFY_URL", None) is None, reason="despotify server not available"
)
@pytest.mark.asyncio
async def test_spotify():
    await base_test_resolver(Spotify())
