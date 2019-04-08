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
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


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


class Word(Base):
    """
    A single word that has been said.

    This is used to prevent the database from getting a huge number of duplicate strings.
    """
    __tablename__ = "word"

    id = Column(Integer, primary_key=True)
    word = Column(Text, nullable=False, unique=True)
    Index('word_index', word, unique=True)


class NgramGroup(Base):
    __tablename__ = "ngram_group"

    id = Column(Integer, primary_key=True)


class Ngram(Base):
    __tablename__ = "ngram"

    id = Column(Integer, primary_key=True)

    group_id = Column(Integer, ForeignKey("ngram_group.id"))
    group = relationship(group_id)

    n = Column(Integer, nullable=False)  # which word this is in the n-gram group

    word_id = Column(Integer, ForeignKey("word.id"))
    word = relationship(word_id)

    UniqueConstraint("group_id", "n", name="unique_ngram_group_n")

    @staticmethod
    def lookup_or_create(user: User, *ngram) -> "Ngram":
        """
        Looks up or creates an n-gram for the supplied user and words.
        """
        assert len(ngram) > 0, "specified n-gram must be at least 1 word long"


class NgramChain(Base):
    __tablename__ = "ngram_chain"

    id = Column(Integer, primary_key=True)
    weight = Column(Integer, nullable=False, default=1)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(user_id)
    group_id = Column(Integer, ForeignKey('ngram_group.id'))
    group = relationship(group_id)
