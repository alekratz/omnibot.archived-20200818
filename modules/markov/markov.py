from contextlib import contextmanager
import itertools
import logging
from pathlib import Path
from typing import Optional
from omnibot import Module
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import Session as OrmSession
from sqlalchemy import create_engine, or_, and_
from sqlalchemy_utils import database_exists, create_database
from .models import Base, User, Word, Ngram, NgramChain


Session: OrmSession = sessionmaker()
log = logging.getLogger(__name__)


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
        "dsn": "sqlite:///" + str(default_base_dir() / "markov.db"),
        "order": 2,
        "reply_chance": 0.01,
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        log.debug("configuration: %s", self.args)
        if Base.metadata.bind:
            log.warning(
                "Base.metadata.bind already set; using that instead of loading a new engine"
            )
            self.__engine = Base.metadata.bind
        else:
            self.__engine = create_engine(self.args["dsn"])
            Base.metadata.bind = self.engine
        Session.configure(bind=self.engine)

    @property
    def engine(self):
        return self.__engine

    @contextmanager
    def session(self):
        session = Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    async def on_load(self):
        dsn = self.args["dsn"]
        if not database_exists(dsn):
            create_database(dsn)
        Base.metadata.create_all(self.engine)

    async def on_message(self, channel: Optional[str], who: Optional[str], text: str):
        if channel is None or who is None:
            return


ModuleClass = Markov
