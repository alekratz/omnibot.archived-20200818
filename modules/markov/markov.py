import itertools
from pathlib import Path
from typing import Tuple
from omnibot import Module
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from .models import Base, User, Word, Ngram


Session = sessionmaker()


def window(seq, n: int):
    "Sliding window function stolen from Stackoverflow :^)"
    it = iter(seq)
    result = tuple(itertools.islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


def default_base_dir():
    """
    Gets the default base directory.

    If the script is a file, then the base directory is given. Otherwise, `Path.cwd()` is given.
    """
    try:
        return Path(__file__).parent
    except:
        return Path.cwd()


class Markov(Module):
    default_args = {
        "dsn": "sqlite://" + str(default_base_dir() / "markov.db"),
        "order": 2,
        "reply_chance": 0.01,
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if Base.metadata.bind:
            log.warning(
                "Base.metadata.bind already set; using that instead of loading a new engine"
            )
            self.__engine = Base.metadata.bind
        else:
            self.__engine = create_engine(self.args["dsn"])
            Base.metadata.bind = self.engine
            Session.configure(bind=self.engine)

    def engine(self):
        return self.__engine

    def register(self, channel: str, name: str, line: str):
        """
        Handles registering a markov chain entry in the database.
        """
        words = line.split(" ")


ModuleClass = Markov
