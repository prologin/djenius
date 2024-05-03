"""
A standalone HTTP server that serves the following endpoints:

  ``/search/{resolver}?q=<query>&limit=<int>``
    Searches for songs on a resolver and return JSON-encoded results.
    The resolver ordering is preserved.

  ``/download/{resolver}/{opaque}``
    Downloads resolver-specific song audio identified by {opaque}. This directly
    returns the (chunked) audio bytes.

  ``/cover/{resolver}/{opaque}``
    Downloads resolver-specific cover art identified by {opaque}. This directly
    returns the (chunked) image bytes.

All these endpoints should sit behind a cache frontend, as the content they
output is unlikely to change over long period of time (days): while search
results for a given query might change every other day, songs and covers have
no reason to change and may be cached for months.
"""

import asyncio
import json
import logging
from typing import Awaitable, Callable

import aiohttp.web

import djenius.resolver

logger = logging.getLogger(__name__)


def _get_resolver(request: aiohttp.web.Request) -> djenius.resolver.Resolver:
    resolver_name = request.match_info["resolver"]
    return request.app["resolvers"][resolver_name]


async def handle_search(request: aiohttp.web.Request):
    q = request.query.get("q")
    limit = int(request.query.get("limit"))
    method = getattr(_get_resolver(request), "search")
    results: djenius.resolver.SearchResults = await method(q, limit)
    data = [json.loads(song.to_json()) for song in results]  # type: ignore
    return aiohttp.web.json_response(data)


async def _invoke_resolver_method(request: aiohttp.web.Request, method_name: str):
    opaque = request.match_info["opaque"]
    method: Callable[[str], Awaitable] = getattr(_get_resolver(request), method_name)
    response = aiohttp.web.StreamResponse()
    await response.prepare(request)
    async for chunk in (await method(opaque)):
        await response.write(chunk)
    return response


async def handle_song_download(request: aiohttp.web.Request):
    return await _invoke_resolver_method(request, "download")


async def handle_cover_download(request: aiohttp.web.Request):
    return await _invoke_resolver_method(request, "cover")


async def startup(app):
    from djenius.resolver import spotify, youtube

    app["resolvers"] = {
        # "spotify": spotify.Spotify(),
        "youtube": youtube.YouTube(),
    }
    await asyncio.wait([r.setup() for r in app["resolvers"].values()])


async def cleanup(app):
    await asyncio.wait([r.cleanup() for r in app["resolvers"].values()])


if __name__ == "__main__":
    from djenius.bin import (
        CommandLineFeature,
        LoggingFeature,
        ListeningFeature,
        serve,
    )

    args = CommandLineFeature.parse(
        (ListeningFeature, LoggingFeature), description="djenius resolver"
    )

    serve(
        logger=logger,
        routes=[
            aiohttp.web.get("/search/{resolver}", handle_search),
            aiohttp.web.get("/download/{resolver}/{opaque}", handle_song_download),
            aiohttp.web.get("/cover/{resolver}/{opaque}", handle_cover_download),
        ],
        args=args,
        startup=startup,
        cleanup=cleanup,
    )
