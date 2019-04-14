import argparse
import asyncio
import logging
import pathlib
import signal
from omnibot import config_from_ucl, ServerManager

log = logging.getLogger(__name__)
manager = None


def __reload_config(loop, filename: str, manager: ServerManager):
    log.info("Reloading configuration")
    try:
        # TODO is there a better way to determine the filetype?
        with open(filename) as fp:
            contents = fp.read()
        coro = manager.reload(config_from_ucl(contents))
        asyncio.ensure_future(coro, loop=loop)
    except Exception:
        logging.exception("Could not reload configuration")


async def __main(loop, args):
    global manager
    logging.basicConfig(level=logging.DEBUG)
    with open(args.config) as fp:
        config = config_from_ucl(fp.read())
    manager = ServerManager(config, loop=loop)

    loop.add_signal_handler(signal.SIGUSR1, __reload_config, loop, args.config, manager)

    await manager.run()


def parse_args():
    parser = argparse.ArgumentParser(description="Run an IRC bot")
    parser.add_argument("-c", "--config", metavar="CONFIG", default="omnibot.ucl")
    return parser.parse_args()


args = parse_args()
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(__main(loop, args))
except KeyboardInterrupt:
    log.info("Caught ctrl-c, attempting graceful exit")
    tasks = asyncio.gather(*asyncio.Task.all_tasks(loop=loop), return_exceptions=True)
    tasks.add_done_callback(lambda _: loop.stop())
    tasks.cancel()
    loop.run_forever()
    loop.run_until_complete(manager.shutdown())
finally:
    loop.stop()
