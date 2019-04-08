from collections import ChainMap
from typing import Any, Mapping, Optional, Sequence


class ModuleError(Exception):
    """
    An error that occurs as a result of a misconfigured module.
    """


class Module:
    """
    A pluggable module for a bot.
    """

    def __init__(
        self, config: "ModuleConfig", server: "Server", commands: Sequence[str] = None
    ) -> None:
        self.__config = config
        self.__server = server
        self.__commands = commands or []
        clazz = self.__class__
        self.__args = ChainMap(self.__config.args, clazz.default_args())

    @property
    def name(self) -> str:
        "The name of this module."
        return self.config.name

    @property
    def config(self) -> "ModuleConfig":
        "The configuration supplied to this module."
        return self.__config

    @property
    def args(self) -> Mapping[str, Any]:
        return self.__args

    @property
    def server(self) -> "Server":
        return self.__server

    @property
    def loop(self):
        return self.server.loop

    @property
    def commands(self) -> Sequence[str]:
        return self.__commands

    async def on_unload(self):
        """
        Callback for when a module is unloaded.
        """

    async def on_load(self):
        """
        Callback for when a module is loaded.
        """

    async def on_connect(self):
        """
        Callback for when a module connects to a server.
        """

    async def on_join(self, channel: str, who: Optional[str]):
        """
        Callback for when a user joins a channel.

        If the bot is the one who is joining, 'who' is None.
        """

    async def on_kick(self, channel: str, who: Optional[str]):
        """
        Callback for when a user is kicked from a channel.

        If the bot is the one who is kicked, 'who' is None.
        """

    async def on_part(self, channel: str, who: Optional[str]):
        """
        Callback for when a user leaves a channel.

        If the bot is the one who is leaving, 'who' is None.
        """

    async def on_message(self, channel: Optional[str], who: Optional[str], text: str):
        """
        Callback for when a message is received.
        """
        if who is None:
            return
        parts = text.split()
        if not parts:
            return
        if parts[0] in self.commands:
            await self.on_command(parts[0], channel, who, text)

    async def on_command(
        self, command: str, channel: Optional[str], who: Optional[str], text: str
    ):
        """
        Callback for when a message is prefixed with a known command.
        """

    def should_handle(self, msg) -> bool:
        """
        Checks if this message should be handled by this bot.

        If True, the message will be passed on to the on_message handler; otherwise, false.
        """
        return (
            bool(msg.parameters)
            and msg.command == "PRIVMSG"
            and msg.parameters[0] in self.config.channels
        )

    @staticmethod
    def default_args():
        """
        A list of all default arguments.
        """
        return {}


def module_commands(*commands):
    def wrapper(cls):
        class _Wrapped(cls):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, commands=commands, **kwargs)

        return _Wrapped

    return wrapper
