import importlib
from pathlib import Path
from typing import Type

from djenius.auth import AuthProvider
from djenius.proto import SongId


class Settings:
    # Directory for the full-text song search index (Whoosh).
    WHOOSH_DIRECTORY: Path = Path("/tmp/djenius-whoosh")

    # State save file.
    STATE_FILE: Path = Path("/tmp/djenius-state.pickle")

    # Dotted-path to the auth provider module and class name.
    AUTH_PROVIDER: str = "djenius.user_registry.AuthProvider"

    # Where the resolver server lives.
    RESOLVER_URL: str = "http://localhost:8000/resolve"

    # mpv host and port.
    MPV_HOST_PORT: str = "localhost:6600"

    # Prometheus exporter host and port.
    PROMETHEUS_HOST_PORT: str = "localhost:9100"

    # Number of search results to query (per resolver).
    SEARCH_COUNT: int = 4

    # Page size when listing songs.
    LIBRARY_PAGE_SIZE = 25

    # Songs longer than this will be filtered out of search results. In seconds.
    MAX_SONG_DURATION: int = 60 * 8

    # How many songs to display in the "Up Next" list.
    QUEUE_SIZE: int = 6

    @classmethod
    def auth_provider(cls) -> Type[AuthProvider]:
        path, cls_name = cls.AUTH_PROVIDER.rsplit(".", 1)
        return getattr(importlib.import_module(path), cls_name)

    @classmethod
    def mpv_host_port(cls):
        host, port = cls.MPV_HOST_PORT.split(":", 1)
        return host, int(port)

    @classmethod
    def prometheus_host_port(cls):
        host, port = cls.PROMETHEUS_HOST_PORT.split(":", 1)
        return host, int(port)

    @classmethod
    def resolver_search_url(cls, resolver):
        return f"{cls.RESOLVER_URL}/search/{resolver}"

    @classmethod
    def resolver_track_url(cls, song_id: SongId):
        return f"{cls.RESOLVER_URL}/download/{song_id}"

    @classmethod
    def resolver_cover_url(cls):
        return f"{cls.RESOLVER_URL}/cover"
