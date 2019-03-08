import os
import sqlite3
import time
import pytest
from modules import wordbot


@pytest.fixture
def db():
    with sqlite3.connect(':memory:') as db:
        db.executescript(wordbot.SQL)
        yield db

def test_wordbot_game(db):
    now = time.time()
    game_save = wordbot.Game(channel="#test", start=now, end=now + 30, words=['a', 'b', 'c'])
    game_save.save(db)
    assert game_save.id is not None

    game_restore = wordbot.Game.restore(db, "#test")
    assert game_restore.id == game_save.id
    assert game_restore.channel == game_save.channel
    assert game_restore.start == game_save.start
    assert game_restore.end == game_save.end
    assert game_restore.words == game_save.words

def test_wordbot_score(db):
    now = time.time()
    game_save = wordbot.Game(channel="#test", start=now, end=now + 30, words=['a', 'b', 'c'])
    game_save.save(db)
    assert game_save.id is not None

    assert len(game_save.words) == 3
    game_save.score(db, 'a', 'testuser', 'a test word')
    assert len(game_save.words) == 2
    assert 'a' not in game_save.words

    game_restore = wordbot.Game.restore(db, "#test")
    assert 'a' not in game_save.words
    assert len(game_restore.words) == 2
    scoreboard = game_restore.scoreboard(db)
    assert scoreboard == game_save.scoreboard(db)
    assert len(scoreboard) > 0
    assert scoreboard['testuser'] == 1
