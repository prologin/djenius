import signal

from aiohttp import web
import argparse
import asyncio
import logging
import os


class CommandLineFeature:
    def contribute(self, p: argparse.ArgumentParser):
        raise NotImplementedError()

    def apply(self, args: argparse.Namespace):
        pass

    @classmethod
    def parse(cls, features, **kwargs):
        p = argparse.ArgumentParser(**kwargs)
        features = [feature() for feature in features]
        [feature.contribute(p) for feature in features]
        args = p.parse_args()
        [feature.apply(args) for feature in features]
        return args


class LoggingFeature(CommandLineFeature):
    """Provides --logging=<LEVEL> flag."""

    def contribute(self, p: argparse.ArgumentParser):
        p.add_argument("--logging", default="INFO")

    def apply(self, args: argparse.Namespace):
        logging.basicConfig(level=getattr(logging, args.logging))


class ListeningFeature(CommandLineFeature):
    """Provide --listen=127.0.0.1:1234 or --unix=/path/to/socket."""

    def contribute(self, p: argparse.ArgumentParser):
        listen = p.add_mutually_exclusive_group(required=True)
        listen.add_argument("--unix", help="Unix domain path")
        listen.add_argument("--listen", help="Host and port")


def register_signal_handlers(loop):
    """
    Register signal handlers for SIGINT and SIGTERM.
    """
    def handle_signal(signal, loop):
        logging.info(f"Received signal {signal.name}, shutting down...")
        for task in asyncio.all_tasks(loop):
            task.cancel()
        loop.stop()

    loop.add_signal_handler(signal.SIGINT, lambda: handle_signal(signal.SIGINT, loop))
    loop.add_signal_handler(signal.SIGTERM, lambda: handle_signal(signal.SIGTERM, loop))

def serve(logger, routes, args, pre_init, startup, cleanup):
    """
    Boilerplate to initialize an aiohttp server.
    """
    app = web.Application()
    app.add_routes(routes)

    if callable(pre_init):
        pre_init(app)

    if callable(startup):
        app.on_startup.append(startup)

    if callable(cleanup):
        app.on_cleanup.append(cleanup)

    runner = web.AppRunner(app)

    async def setup():
        await runner.setup()

        if args.unix:
            site = web.UnixSite(runner, args.unix)
        elif args.listen:
            host, port = args.listen.split(":")
            port = int(port)
            site = web.TCPSite(runner, host, port)
        else:
            raise ValueError()

        await site.start()
        if args.unix:
            os.chmod(args.unix, 0o777)
        return site

    loop = asyncio.get_event_loop()

    # Setup.
    logger.info("site starting")
    site = loop.run_until_complete(setup())
    logger.info("site started: %s", site.name)

    # Register signal handlers.
    register_signal_handlers(loop)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.warning("keyboard interrupt")

    # Cleanup.
    logger.info("cleaning up before exiting")
    loop.run_until_complete(runner.cleanup())
