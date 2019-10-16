from enum import Enum
import logging
from pathlib import Path
from typing import Any, Mapping, Iterator, Sequence


log = logging.getLogger(__name__)


class ConfigError(Exception):
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
        data: str = None,
    ):
        self._name = name
        self._channels = set(channels or [])
        self._args = args or {}
        self._always_reload = always_reload or False
        self._data = data or name

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

    @property
    def data(self) -> Path:
        return Path(self._data)

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
        name: str,
        nick: str,
        address: str = None,
        port: int = None,
        ssl: bool = None,
        data: str = None,
        modules: Mapping[str, Any] = None,
        **kwargs
    ):
        self._address = address or name
        self._ssl = ssl or False
        if port is None:
            self._port = 6697 if self._ssl else 6667
        else:
            self._port = int(port)
        self._nick = nick
        self._data = data or str(Path.cwd() / 'data')
        modules = modules or {}
        self._modules = {}
        for name, mod in modules.items():
            self._modules[name] = ModuleConfig(name=name, **mod)
        for k in kwargs.keys():
            log.warning("Unused config value for server %s: %s", self._address, k)

    @property
    def address(self) -> str:
        "The server's address to connect to."
        return self._address

    @property
    def port(self) -> int:
        "The port to connect to on the server."
        return self._port

    @property
    def ssl(self) -> bool:
        "Whether to use SSL or not."
        return self._ssl

    @property
    def nick(self) -> str:
        "The nickname for this bot to use."
        return self._nick

    @property
    def data(self) -> Path:
        "The data directory that this bot will use."
        return Path(self._data)

    @property
    def modules(self) -> Mapping[str, ModuleConfig]:
        return self._modules

    def __eq__(self, other: "ServerConfig") -> bool:
        return (
            isinstance(other, ServerConfig)
            and self.address == other.address
            and self.port == other.port
            and self.ssl == other.ssl
            and self.modules == other.modules
        )

    def __hash__(self) -> int:
        return hash((self.address, self.port, self.ssl, list(self.modules.keys())))


def config_from_yaml(text: str):
    import pyyaml
    return config_from_obj(pyyaml.load(text))


def config_from_obj(obj: Mapping[str, Any]):
    if not obj:
        return []
    return [ServerConfig(name=name, **c) for name, c in obj["server"].items()]
