from enum import Enum
import logging
from typing import Any, Mapping, Iterator, Sequence
import yaml


log = logging.getLogger(__name__)


class InvalidConfigError(Exception):
    """
    Indicates an invalid configuration
    """


class ModuleConfig:
    def __init__(
        self,
        name: str,
        channels: Sequence[str] = None,
        args: Mapping[str, Any] = None,
        always_reload: bool = None,
    ):
        self._name = name
        self._channels = set(channels or [])
        self._args = args or {}
        self._always_reload = always_reload or False

    @property
    def name(self):
        return self._name

    @property
    def channels(self):
        return self._channels

    @property
    def args(self):
        return self._args

    @property
    def always_reload(self) -> bool:
        return self._always_reload

    def __getitem__(self, key: str) -> Any:
        return self.args[key]

    def __eq__(self, other: "ModuleConfig") -> bool:
        return (
            isinstance(other, ModuleConfig)
            and self.name == other.name
            and self.channels == other.channels
            and self.always_reload == other.always_reload
            and self.args == other.args
        )

    def __hash__(self) -> int:
        return hash(self.name)


class ServerConfig:
    def __init__(
        self,
        *,
        addr: str,
        nick: str,
        port: int = None,
        ssl: bool = None,
        modules: Mapping[str, Any] = None,
        **kwargs
    ):
        self._addr = addr
        self._ssl = ssl or False
        if port is None:
            self._port = 6697 if self._ssl else 6667
        else:
            self._port = int(port)
        self._nick = nick
        modules = modules or {}
        self._modules = {}
        for name, mod in modules.items():
            self._modules[name] = ModuleConfig(name=name, **mod)
        for k in kwargs.keys():
            log.warning("Unused config value for server %s: %s", self._addr, k)

    @property
    def addr(self) -> str:
        return self._addr

    @property
    def port(self) -> int:
        return self._port

    @property
    def ssl(self) -> bool:
        return self._ssl

    @property
    def nick(self) -> str:
        return self._nick

    @property
    def modules(self) -> Mapping[str, ModuleConfig]:
        return self._modules

    def __eq__(self, other: "ServerConfig") -> bool:
        return (
            isinstance(other, ServerConfig)
            and self.addr == other.addr
            and self.port == other.port
            and self.ssl == other.ssl
            and self.modules == other.modules
        )

    def __hash__(self) -> int:
        return hash((self.addr, self.port, self.ssl, list(self.modules.keys())))


def config_from_yaml(text: str):
    obj = yaml.load(text)
    if not obj:
        return []
    return [ServerConfig(**c) for c in obj["servers"]]
