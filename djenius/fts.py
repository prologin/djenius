import abc
import asyncio
from pathlib import Path
from typing import Iterable
import whoosh.fields
import whoosh.index
import whoosh.qparser

from djenius.proto import SongId, Song


class ISongSearch(abc.ABC):
    @abc.abstractmethod
    async def index(self, song: Song):
        ...

    @abc.abstractmethod
    async def search(self, query: str, n: int) -> Iterable[SongId]:
        ...


class UNIQUEID(whoosh.fields.FieldType):
    indexed = False
    stored = True
    unique = True

    def __init__(self):
        pass


class WhooshSongSearch(ISongSearch):
    schema = whoosh.fields.Schema(
        id=UNIQUEID(),
        rank=whoosh.fields.NUMERIC(sortable=True, stored=True),
        summary=whoosh.fields.TEXT(stored=True),
    )

    def __init__(self, directory: Path):
        if not whoosh.index.exists_in(str(directory)):
            directory.mkdir(exist_ok=True, parents=True)
            whoosh.index.create_in(str(directory), self.schema)

        self._index = whoosh.index.open_dir(str(directory))
        self._lock = asyncio.Lock()

    async def _run_sync(self, func, *args):
        async with self._lock:
            return await asyncio.get_running_loop().run_in_executor(None, func, *args)

    async def index(self, song: Song):
        rank = 10 if song.resolver == "spotify" else 1

        def indexer():
            w = self._index.writer()
            w.update_document(id=song.id, summary=song.summary(), rank=rank)
            w.commit()

        await self._run_sync(indexer)

    async def search(self, query: str, n: int) -> Iterable[SongId]:
        def searcher(query: str, n: int):
            qp = whoosh.qparser.QueryParser("summary", schema=self.schema)
            with self._index.searcher() as s:
                q = qp.parse(query)
                corr = s.correct_query(q, query, maxdist=2, prefix=0)
                return [
                    hit["id"]
                    for hit in s.search(
                        corr.query, limit=n, sortedby="rank", reverse=True
                    )
                ]

        return await self._run_sync(searcher, query, n)
