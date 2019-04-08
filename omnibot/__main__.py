import argparse
import asyncio
import logging
import signal
from omnibot import config_from_yaml, ServerManager

log = logging.getLogger(__name__)


def __reload_config(loop, filename: str, manager: ServerManager):
    log.info("Reloading configuration")
    try:
        with open(filename) as fp:
            contents = fp.read()
        coro = manager.reload(config_from_yaml(contents))
        asyncio.ensure_future(coro, loop=loop)
    except Exception:
        logging.exception("Could not reload configuration")


async def __main(loop, args):
    logging.basicConfig(level=logging.DEBUG)
    with open(args.config) as fp:
        config = config_from_yaml(fp.read())
    manager = ServerManager(config, loop=loop)

    loop.add_signal_handler(signal.SIGUSR1, __reload_config, loop, args.config, manager)

    await manager.run()


def parse_args():
    parser = argparse.ArgumentParser(description="Run an IRC bot")
    parser.add_argument("-c", "--config", metavar="CONFIG", default="omnibot.yml")
    return parser.parse_args()


args = parse_args()
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(__main(loop, args))
finally:
    loop.stop()
