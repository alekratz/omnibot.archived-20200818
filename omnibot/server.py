import abc
import asyncio
import logging
from typing import Sequence, Optional
from asyncirc.server import Server as IrcServer
from asyncirc.protocol import IrcProtocol
from .loader import ModuleLoader
from .message import Message
from .config import ServerConfig


log = logging.getLogger(__name__)


class Server:
    def __init__(self, loader: ModuleLoader, config: ServerConfig, loop=None) -> None:
        self._config = config
        self._modules = {}
        self._loader = loader
        self._loop = loop or asyncio.get_event_loop()
        self._conn = IrcProtocol(
            [IrcServer(config.addr, config.port, config.ssl)],
            config.nick,
            loop=self._loop,
        )
        self._conn.register("*", self.on_server_message)
        self._active_channels = set()
        self._connected = False

    @property
    def config(self) -> ServerConfig:
        return self._config

    @property
    def addr(self) -> str:
        return self.config.addr

    @property
    def port(self) -> int:
        return self.config.port

    @property
    def close_future(self):
        return self._conn.quit_future

    @property
    def loop(self):
        return self._loop

    async def connect(self) -> None:
        await self.load_modules()
        await self._conn.connect()

    async def disconnect(self) -> None:
        log.debug("Disconnecting from %s", self.addr)
        await self.unload_modules()
        self._connected = False
        self._conn.quit()

    async def reload(self, config: ServerConfig) -> None:
        """
        Reloads a server based on a new configuration.
        """
        assert (
            self.config.addr == config.addr
            and self.config.port == config.port
            and self.config.ssl == config.ssl
        ), "changing a connection must be done through the server manager"
        self._config = config
        await self.reload_modules()

    async def reload_modules(self) -> None:
        """
        Unloads, and then reloads all modules for this server.
        """
        log.debug("Reloading modules")
        unload = []
        for module in self._modules.values():
            if module.name in self.config.modules:
                if (
                    module.config != self.config.modules[module.name]
                    or module.config.always_reload
                ):
                    log.debug("Scheduling %s for reload", module.name)
                    unload += [module.name]
            else:
                unload += [module.name]

        await self.unload_modules(unload)
        await self.load_modules()
        self.match_channels()

    async def load_modules(self) -> None:
        """
        Loads all modules that have not yet been loaded for this server.
        """
        log.debug("Loading modules")
        for config in self.config.modules.values():
            if config.name in self._modules:
                continue
            on_load = None
            try:
                ctor = self._loader.load_module(config.name)
                loaded = ctor(config, self)
                on_load = self.loop.create_task(loaded.on_load())
                await on_load
                if self._connected:
                    await loaded.on_connect()
                self._modules[config.name] = loaded
            except KeyboardInterrupt:
                if on_load is not None:
                    on_load.cancel()
                raise
            except:
                log.exception("Could not load module %s", config.name)
                continue

    async def unload_modules(self, which: Optional[Sequence[str]] = None) -> None:
        """
        Loads specified modules for this server.

        If nothing is specified, all modules are unloaded.

        If explicitly zero modules are specified (i.e. an empty set), no modules are unloaded.
        """
        log.debug("Unloading modules")
        if which is None:
            which = set(self._modules.keys())
        unloaded = []
        for module_name in which:
            self._loader.unload_module(module_name)
            unloaded += [self._modules.pop(module_name).on_unload()]

        await asyncio.gather(*unloaded)

    def match_channels(self):
        need = {
            chan for module in self._modules.values() for chan in module.config.channels
        }
        to_join = need - self._active_channels
        to_leave = self._active_channels - need
        for chan in to_join:
            self._conn.send("JOIN " + chan)
        for chan in to_leave:
            self._conn.send("PART " + chan)

    async def on_server_message(self, conn, msg) -> None:
        """
        Callback that is called whenever a message is received.
        """
        # log.debug("%s", msg)
        if msg.command == "001":
            self._connected = True
            await self.on_connect()
        elif msg.command == "KICK":
            await self.on_kick(msg)
        elif msg.command == "PART":
            await self.on_part(msg)
        elif msg.command == "JOIN":
            await self.on_join(msg)
        else:
            await self.on_message(msg)

    async def on_connect(self) -> None:
        """
        Callback that is run when this server connects.
        """
        self.match_channels()
        futures = [module.on_connect() for module in self._modules.values()]
        tasks = asyncio.gather(*futures, loop=self.loop)
        try:
            await tasks
        except KeyboardInterrupt:
            tasks.cancel()
            raise

    async def on_kick(self, msg):
        """
        Callback that is run when a user is kicked from a channel.
        """
        channel = msg.parameters[0]
        who = msg.parameters[1]
        if who == self.config.nick:
            who = None
            self._active_channels.remove(channel)
        futures = [module.on_kick(channel, who) for module in self._modules.values()]
        tasks = asyncio.gather(*futures, loop=self.loop)
        try:
            await tasks
        except KeyboardInterrupt:
            tasks.cancel()
            raise
        except:
            log.exception("Error while handling kick callback")

        if who is None:
            self.loop.call_later(3.0, self.match_channels)

    async def on_part(self, msg):
        """
        Callback that is run when a user leaves a channel.
        """
        channel = msg.parameters[0]
        who = msg.prefix.nick
        if who == self.config.nick:
            who = None
            self._active_channels.remove(channel)
        futures = [module.on_part(channel, who) for module in self._modules.values()]
        tasks = asyncio.gather(*futures, loop=self.loop)
        try:
            await tasks
        except KeyboardInterrupt:
            tasks.cancel()
            raise
        except:
            log.exception("Error while handling part callback")

        if who is None:
            self.loop.call_later(3.0, self.match_channels)

    async def on_join(self, msg):
        """
        Callback that is run when a user joins a channel.
        """
        channel = msg.parameters[0]
        who = msg.prefix.nick
        if who == self.config.nick:
            who = None
            self._active_channels.add(channel)
        futures = [module.on_join(channel, who) for module in self._modules.values()]
        tasks = asyncio.gather(*futures, loop=self.loop)
        try:
            await tasks
        except KeyboardInterrupt:
            tasks.cancel()
            raise
        except:
            log.exception("Error while handling join callback")

        if who is None:
            self.loop.call_later(3.0, self.match_channels)

    async def on_message(self, msg):
        """
        Callback that is run when a PRIVMSG (i.e. a channel or private message) is received.
        """
        channel = msg.parameters[0]
        if channel not in self._active_channels:
            # private message to us
            channel = None
        if msg.prefix is None:
            return
        who = msg.prefix.nick
        if who == self.config.nick:
            who = None
        text = " ".join(msg.parameters[1:])
        futures = [
            module.on_message(channel, who, text)
            for module in self._modules.values()
            if module.should_handle(msg)
        ]
        tasks = asyncio.gather(*futures, loop=self.loop)
        try:
            await tasks
        except KeyboardInterrupt:
            tasks.cancel()
            raise
        except:
            log.exception("Error handling channel message")

    def send_message(self, target: str, message: str) -> None:
        """
        Sends a message to the server.
        """
        self._conn.send("PRIVMSG {} {}".format(target, message))


class ServerManager:
    def __init__(self, server_configs: Sequence[ServerConfig], loop=None) -> None:
        self._loop = loop or asyncio.get_event_loop()
        # set up all servers from their configs
        self._server_configs = {s.addr: s for s in server_configs}
        self._servers = {
            addr: Server(ModuleLoader(["modules"]), cfg)
            for addr, cfg in self._server_configs.items()
        }
        self._servers_lock = asyncio.Lock()
        self._active = {}
        self._active_lock = asyncio.Lock()
        self._reload_signal = asyncio.Event()
        self._reconnect_servers = {}

    async def _connect(self):
        async def connect_one(server):
            log.info("Connecting to %s", server.addr)
            try:
                await server.connect()
            except KeyboardInterrupt:
                raise
            except:
                log.exception("Could not connect to %s", server.addr)
                return
            async with self._active_lock:
                self._active[server.addr] = server

        async with self._servers_lock:
            connect = set(self._servers.keys()) - set(self._active.keys())
            futures = []
            for addr in connect:
                server = self._servers[addr]
                futures += [connect_one(server)]
            for addr, server in self._reconnect_servers.items():
                assert (
                    addr not in self._active
                ), "attempting to reconnect to an active server"
                self._servers[addr] = server
                futures += [connect_one(server)]
            self._reconnect_servers.clear()
        tasks = asyncio.gather(*futures, loop=self._loop)
        try:
            await tasks
        except KeyboardInterrupt:
            tasks.cancel()
            raise

    async def _disconnect(self):
        """
        Prunes any connections that have been removed from the configuration.
        """
        futures = []
        async with self._servers_lock:
            remove = set(self._active.keys()) - set(self._servers.keys())
        for addr in remove:
            log.info("Closing connection to %s", addr)
            async with self._active_lock:
                server = self._active.pop(addr)
            futures += [server.close_future]
            futures += [server.disconnect()]
        await asyncio.gather(*futures, loop=self._loop)

    async def _server_futures(self):
        async with self._servers_lock:
            return [server.close_future for server in self._servers.values()]

    async def run(self):
        while True:
            await self._disconnect()
            await self._connect()
            futures = await self._server_futures() + [self._reload_signal.wait()]
            await asyncio.wait(
                futures, loop=self._loop, return_when=asyncio.FIRST_COMPLETED
            )
            self._reload_signal.clear()

    async def shutdown(self):
        log.info("Stopping omnibot")
        async with self._servers_lock:
            self._servers.clear()
        await self._disconnect()

    async def reload(self, server_configs: Sequence[ServerConfig]):
        log.info("Reloading server configurations")
        server_configs = {s.addr: s for s in server_configs}
        reload_futures = []
        async with self._servers_lock:
            current = set(self._server_configs.keys())
            new = set(server_configs.keys())
            added = new - current
            removed = current - new
            changed = current & new
            for addr in added:
                log.debug("Added server %s", addr)
                self._servers[addr] = Server(
                    ModuleLoader(["modules"]), server_configs[addr]
                )
            for addr in removed:
                log.debug("Removed server %s", addr)
                self._servers.pop(addr)
            for addr in changed:
                prev = self._server_configs[addr]
                newest = server_configs[addr]
                # check if connection settings changed, and make a new connection if so
                if (prev.addr, prev.port, prev.ssl) != (
                    newest.addr,
                    newest.port,
                    newest.ssl,
                ):
                    log.debug("Reconnecting to server %s", newest.addr)
                    self._servers.pop(prev.addr)
                    self._reconnect_servers[newest.addr] = Server(
                        ModuleLoader(["modules"]), newest
                    )
                else:
                    log.debug("Reconfiguring server %s", newest.addr)
                    reload_futures += [self._servers[addr].reload(server_configs[addr])]
            await asyncio.gather(*reload_futures, loop=self._loop)
            self._server_configs = server_configs
        self._reload_signal.set()
        log.info("Finished reloading server configurations")
