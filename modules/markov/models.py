from contextlib import contextmanager
import itertools
import random
from typing import Optional, Sequence, Tuple, Type
from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    UniqueConstraint,
    Integer,
    Float,
    String,
    Boolean,
    Text,
    LargeBinary,
    or_,
    and_,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import Session as OrmSession
from .chain import MarkovChain


def window(seq, n: int):
    "Sliding window function stolen from Stackoverflow :^)"
    it = iter(seq)
    result = tuple(itertools.islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


Base: DeclarativeMeta = declarative_base()


class User(Base):
    """
    A user with a unique channel and username.

    `channel` - the channel this user is a part of.
    `name` - this user's name.
    `listen` - whether to listen to or ignore this user.
    `reply_chance` - the chance, from [0, 1], to reply to the user with a random sentence.
    """

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    channel = Column(String(40), nullable=False)
    name = Column(String(40), nullable=False)
    listen = Column(Boolean, default=True, nullable=False)
    reply_chance = Column(Float(asdecimal=True))

    UniqueConstraint("channel", "name", name="unique_channel_name")

    def __repr__(self) -> str:
        return "<User(id={}, channel={}, name={}, listen={}, reply_chance={})>".format(
            self.id, self.channel, self.name, self.listen, self.reply_chance
        )


class Word(Base):
    """
    A single word that has been said.

    This is used to prevent the database from getting a huge number of duplicate strings.
    """

    __tablename__ = "word"

    id = Column(Integer, primary_key=True)
    word = Column(Text, nullable=False, unique=True)
    Index("word_index", word, unique=True)

    def __repr__(self) -> str:
        return "<Word(id={}, word={})>".format(self.id, self.word)


class NgramGroup(Base):
    __tablename__ = "ngram_group"

    id = Column(Integer, primary_key=True)
    order = Column(Integer, nullable=False)
    Index("ngram_group_order_index", order)

    def __repr__(self) -> str:
        return "<NgramGroup(id={}, order={})>".format(self.id, self.order)


class Ngram(Base):
    __tablename__ = "ngram"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("ngram_group.id"))
    group = relationship(NgramGroup, back_populates="ngrams")
    n = Column(Integer, nullable=False)  # which word this is in the n-gram group
    word_id = Column(Integer, ForeignKey("word.id"), nullable=True)
    word = relationship(Word, back_populates="ngrams")

    UniqueConstraint("group", "n", name="unique_ngram_group_n")
    Index("ngram_group_id_index", group_id)
    Index("ngram_n_index", n)
    Index("ngram_word_id_index", word_id)

    def __repr__(self) -> str:
        return "<Ngram(id={}, group={}, n={}, word={})>".format(
            self.id, self.group, self.n, self.word
        )


Word.ngrams = relationship(Ngram, back_populates="word")
NgramGroup.ngrams = relationship(Ngram, back_populates="group")


class NgramChain(Base):
    __tablename__ = "ngram_chain"

    id = Column(Integer, primary_key=True)
    weight = Column(Integer, nullable=False, default=1)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship(User, back_populates="chains")
    group_id = Column(Integer, ForeignKey("ngram_group.id"))
    group = relationship(NgramGroup)
    next_word_id = Column(Integer, ForeignKey("word.id"), nullable=True)
    next_word = relationship(Word)

    Index("chain_user_id_index", user_id)
    Index("chain_group_id_index", group_id)
    Index("chain_user_id_group_id_index", user_id, group_id)


User.chains = relationship(NgramChain, order_by=NgramChain.id, back_populates="user")


class MarkovModelChain(MarkovChain):
    def __init__(
        self, session_type: Type[OrmSession], channel: str, user: str, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._user = user
        self._channel = channel
        self._session_type = session_type

    @property
    def user(self) -> str:
        return self._user

    @property
    def channel(self) -> str:
        return self._channel

    @contextmanager
    def session(self):
        session = self._session_type()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def get_or_create(self, session: OrmSession, model: Base, **kwargs):
        item = session.query(model).filter_by(**kwargs).one_or_none()
        if item is None:
            item = model(**kwargs)
            session.add(item)
        return item

    def get_user(self, session: OrmSession) -> User:
        return self.get_or_create(session, User, channel=self.channel, name=self.user)

    def get_words(
        self, session: OrmSession, words: Sequence[Optional[str]]
    ) -> Sequence[Optional[Word]]:
        return [
            None if word is None else self.get_or_create(session, Word, word=word)
            for word in words
        ]

    def get_ngram_group(
        self, session: OrmSession, words: Sequence[Word]
    ) -> Optional[Ngram]:
        assert len(words) == self.order
        query = (
            session.query(Ngram)
            .filter(
                or_(
                    *(
                        and_(Ngram.n == n, Ngram.word == word)
                        for n, word in enumerate(words)
                    )
                )
            )
            .order_by(Ngram.group_id)
        )  # groupby needs things to be in order
        ngrams = [
            (group, (*grams,))
            for group, grams in itertools.groupby(query.all(), lambda gram: gram.group)
        ]
        for group, grams in ngrams:
            if len(grams) == self.order and group.order == self.order:
                return group
        return None

    def insert_all(self, text_words: Sequence[str]) -> None:
        with self.session() as session:
            user = self.get_user(session)
            words = list(self.get_words(session, text_words)) + [None]
            while len(words) < self.order + 1:
                words += [None]
            session.commit()

            for view in window(words, self.order + 1):
                next_word = view[-1]
                view = view[:-1]
                ngram_group = self.get_ngram_group(session, view)
                # there was not an exact n-gram node for this entry, so insert it
                if ngram_group is None:
                    ngram_group = NgramGroup(order=self.order)
                    session.add(ngram_group)
                    for n, word in enumerate(view):
                        session.add(Ngram(n=n, group=ngram_group, word=word))
                    session.commit()
                # see if there's a chain entry for this ngram group, next_word, and user
                chain = (
                    session.query(NgramChain)
                    .filter(
                        NgramChain.user == user,
                        NgramChain.group == ngram_group,
                        NgramChain.next_word == next_word,
                    )
                    .one_or_none()
                )
                if chain is None:
                    chain = NgramChain(
                        weight=0, user=user, group=ngram_group, next_word=next_word
                    )
                    session.add(chain)
                chain.weight += 1
                session.commit()

    def weights(self, text_words: Sequence[str]) -> Sequence[Tuple[str, int]]:
        assert len(text_words) == self.order
        with self.session() as session:
            user = self.get_user(session)
            words = self.get_words(session, text_words)
            ngram_group = self.get_ngram_group(session, words)
            if ngram_group is None:
                return []

            chains = (
                session.query(NgramChain)
                .filter(NgramChain.user == user, NgramChain.group == ngram_group)
                .all()
            )

            return [
                (
                    None if chain.next_word is None else chain.next_word.word,
                    chain.weight,
                )
                for chain in chains
                if chain.group.order == self.order
            ]

    def choose_ngram(self) -> Optional[Sequence[Optional[str]]]:
        with self.session() as session:
            user = self.get_user(session)
            chain = session.query(NgramChain).filter(NgramChain.user == user).order_by(
                func.random()
            ).limit(1).one_or_none()
            if chain is None:
                return None
            return [None if ngram.word is None else ngram.word.word for ngram in chain.group.ngrams]

    def choose_word(self, text_words: Sequence[Optional[str]]) -> Optional[str]:
        with self.session() as session:
            user = self.get_user(session)
            words = self.get_words(session, text_words)
            group = self.get_ngram_group(session, words)
            if group is None:
                return None
            chains = session.query(NgramChain).filter(user == user, group == group).all()
            if len(chains) == 0:
                return None
            # NOTE requires python 3.6
            choice = random.choices(chains, weights=[c.weight for c in chains])
            word = choice[0].next_word
            if word is None:
                return None
            else:
                return word.word
