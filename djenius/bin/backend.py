"""
Implements a standalone HTTP server serving the djenius frontend.
"""

import argparse
import logging
from pathlib import Path

import aiohttp.web

import djenius.server.main
from djenius.bin import CommandLineFeature, ListeningFeature, LoggingFeature, serve
from djenius.server.main import logger
from djenius.server.settings import Settings


class AppFeatures(CommandLineFeature):
    def contribute(self, p: argparse.ArgumentParser):
        p.add_argument(
            "--state-file",
            required=True,
            type=Path,
            help="File in which to store & load the state (available songs, votes)",
        )
        p.add_argument(
            "--whoosh-dir",
            required=True,
            type=Path,
            help="Directory in which to store the Whoosh index (full-text search)",
        )
        p.add_argument(
            "--resolver",
            required=True,
            help="Resolver URI, without the final slash, for instance http://localhost:1234/resolve",
        )
        p.add_argument(
            "--public-resolver",
            required=True,
            help="Public resolver URI, without the final slash, for instance http://localhost:1234/resolve",
        )
        p.add_argument(
            "--auth",
            required=True,
            help="Dotted path to a class inheriting djenius.auth.AuthProvider",
        )
        p.add_argument(
            "--mpv",
            default="localhost:6600",
            help="mpv host:port, default port is 6600",
        )
        p.add_argument(
            "--mvp-windows",
            default='False',
            help="Whether to use mpv windows (via Named Pipe TCP Proxy) or not",
        )
        p.add_argument(
            "--prometheus",
            default="localhost:9090",
            help="Prometheus exporter host:port, default port is 9090",
        )
        p.add_argument(
            "--max-song-duration",
            type=int,
            default=60 * 8,
            help="Maximum song duration in seconds",
        )
        p.add_argument(
            "--queue-size",
            type=int,
            default=6,
            help="Number of songs to display in the 'Up Next' queue",
        )
        p.add_argument(
            "--page-size",
            type=int,
            default=25,
            help="Number of songs per page to display in the library",
        )

    def apply(self, args: argparse.Namespace):
        Settings.STATE_FILE = args.state_file
        Settings.WHOOSH_DIRECTORY = args.whoosh_dir
        Settings.AUTH_PROVIDER = args.auth
        Settings.MAX_SONG_DURATION = args.max_song_duration
        Settings.QUEUE_SIZE = args.queue_size
        Settings.LIBRARY_PAGE_SIZE = args.page_size
        Settings.RESOLVER_URL = args.resolver
        Settings.RESOLVER_PUBLIC_URL = args.public_resolver
        Settings.MPV_HOST_PORT = args.mpv
        Settings.MPV_WINDOWS = args.mvp_windows.lower() == 'true'
        Settings.PROMETHEUS_HOST_PORT = args.prometheus


if __name__ == "__main__":
    args = CommandLineFeature.parse(
        (ListeningFeature, LoggingFeature, AppFeatures), description="djenius backend",
    )

    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)

    main = djenius.server.main.Main()
    serve(
        logger=djenius.server.main.logger,
        routes=[aiohttp.web.get("/ws", main.ws_handler)],
        args=args,
        pre_init=main.pre_init,
        startup=main.on_init,
        cleanup=main.on_shutdown,
    )
