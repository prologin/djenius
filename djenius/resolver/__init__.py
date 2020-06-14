from typing import AsyncGenerator, List
import aiohttp

from djenius.proto import Song

SearchResults = List[Song]


class Resolver:
    async def setup(self):
        """
        Called once at initialization. This is a chance for the resolver to
        setup its internal logic.
        """
        pass

    async def cleanup(self):
        """
        Called once at shutdown. This is a chance for the resolver to release
        resources.
        """
        pass

    async def search(self, query: str, limit: int) -> SearchResults:
        """
        Search songs by text query and yield results.

        :param query: the query to search for on the resolver
        :param limit: maximum number of results to return
        :return: an async generator of Search
        """
        raise NotImplementedError()

    async def download(self, opaque: str) -> AsyncGenerator[bytes, None]:
        """
        Download the song.

        :param opaque: resolver-specific ID for the song
        """
        raise NotImplementedError()

    async def cover(self, opaque: str) -> AsyncGenerator[bytes, None]:
        """
        Download the cover.

        :param opaque: resolver-specific ID for the cover art
        """
        raise NotImplementedError()


async def _download_chunked(url, **kwargs) -> AsyncGenerator[bytes, None]:
    async with aiohttp.ClientSession() as http:
        async with http.get(url, **kwargs) as resp:
            async for chunk in resp.content.iter_chunked(32 * 1024):
                yield chunk
