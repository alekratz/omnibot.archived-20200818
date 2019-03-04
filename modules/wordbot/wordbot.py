import itertools
import logging
import operator
from pathlib import Path
import random
import sqlite3
from string import punctuation
import time
from typing import Mapping, Optional, Sequence
from omnibot import Module
from .game import Game


log = logging.getLogger(__name__)


SQL = """
CREATE TABLE IF NOT EXISTS game (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    start INTEGER NOT NULL,
    end INTEGER NOT NULL,
    channel VARCHAR(40) NOT NULL
);
CREATE TABLE IF NOT EXISTS word (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    game INTEGER NOT NULL,
    word VARCHAR(40) NOT NULL,
    FOREIGN KEY (game) REFERENCES game(id),
    UNIQUE(game, word)
);
CREATE TABLE IF NOT EXISTS score (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    game INTEGER NOT NULL,
    word INTEGER NOT NULL,
    user VARCHAR(40) NOT NULL,
    line VARCHAR(1024) NOT NULL,
    FOREIGN KEY (game) REFERENCES game(id),
    FOREIGN KEY (word) REFERENCES word(id),
    UNIQUE(game, word)
);
"""


def default_base_dir():
    """
    Gets the default base directory.

    If the script is a file, then the base directory is given. Otherwise, `os.getcwd()` is given.
    """
    try:
        return Path(__file__).parent
    except:
        return Path.cwd()


class Wordbot(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._games = {}
        self._words = set()

    async def on_load(self):
        """
        Ensures the current database state and recreates the current state if necessary.
        """
        self._ensure_database()
        with open(self.args['wordlist_path']) as fp:
            self._words = set(map(str.strip, fp))
        log.info("loaded %s words", len(self._words))

    async def on_unload(self):
        """
        Flushes the current state to the database before exiting.
        """

    async def on_join(self, channel: str, who: Optional[str]):
        """
        Handles game creation and restoration.
        """
        if who is None:
            self.restore_game(channel)

    async def on_message(self, channel: Optional[str], who: Optional[str], text: str):
        """
        Handle a line of text for Wordbot.

        There are a number of cases where this may bail:

        * If the message is from wordbot,
        * If there is not a currently running game in this channel,
        * If the line is empty (shouldn't happen, but whatever),
        * If the line is a !wordbot command (gets handled appropriately),
        * If the line is starts with a '!' (to avoid treating commands for other bots as input),
        * If the message is a PM and not a !wordbot command.

        Otherwise, the line is stripped, scanned, and checked for winning words.
        """
        parts = text.split()
        if who is None:
            return
        elif channel not in self._games:
            return
        elif len(parts) == 0:
            return
        elif parts[0] == '!wordbot':
            await self.on_command(parts[0], channel, who, text)
        elif parts[0][0] == '!' or channel is None:
            # attempt to ignore other commands and definitely ignore private messages
            return
        else:
            game = self._games[channel]
            parts = set(filter(len, [word.strip(punctuation).lower() for word in parts]))
            matches = parts & game.words
            if not matches:
                return
            with self._db() as db:
                for word in matches:
                    game.score(db, word, who, text)
            for word in matches:
                self.server.send_message(channel, "{}: Congrats! '{}' is good for 1 point.".format(who, word))

    async def on_command(self, command: str, channel: Optional[str], who: Optional[str], text: str):
        pass

    @staticmethod
    def default_args():
        return {
            'database_path': str(default_base_dir() / 'wordbot.db'),
            'words_per_hour': 50,
            'hours_per_round': 5,
            'wordlist_path': str(default_base_dir() / 'words.txt'),
        }

    def _ensure_database(self):
        """
        Ensures that the database exists and the tables also exist.
        """
        log.debug("Ensuring wordbot database (%s)", self.args['database_path'])
        with self._db() as conn:
            conn.executescript(SQL)

    def _db(self):
        """
        Creates a database connection.
        """
        return sqlite3.connect(self.args['database_path'])

    def restore_game(self, channel: str):
        """
        Restores or creates a game for the specified channel.
        """
        if channel in self._games:
            # nothing to do since the game is already running and *should* have a callback set up
            return
        else:
            with self._db() as conn:
                game = Game.restore(conn, channel)
            if game is None:
                # create a new game 
                self.new_game(channel)
            else:
                now = time.time()
                self._games[channel] = game
                if game.end < now:
                    self.loop.call_soon(self.end_game, channel)
                else:
                    duration = game.end - now
                    self.loop.call_later(duration, self.end_game, channel)

    def create_game(self, channel: str):
        """
        Utility method to create a new game.

        This does not save the game after it's been created.
        """
        start = int(time.time())
        duration = self.args['hours_per_round'] * 3600.0
        end = int(start + duration)
        words = self.choose_words()
        #log.debug("Chose these words: %s", words)
        return Game(channel=channel, start=start, end=end, words=words)

    def end_game(self, channel: str):
        """
        Ends a game for a channel, announces winners, and creates a new one.
        """
        lines = ['Game over. Here were the scores:']

        score_key = operator.itemgetter(1)
        score_groups = itertools.groupby(sorted(self.scoreboard(channel).items(), key=score_key, reverse=True),
                                         key=score_key)
        for place, (points, group) in enumerate(score_groups, 1):
            if points > 0:
                for name, _ in group:
                    lines += ["{}. {}. {}".format(place, name, points)]
        for line in lines:
            self.server.send_message(channel, line)
        self.new_game(channel)

    def new_game(self, channel: str):
        """
        Creates a new game for the given channel.
        """
        game = self.create_game(channel)
        with self._db() as conn:
            game.save(conn)
        self.loop.call_later(game.duration, self.end_game, channel)
        self._games[channel] = game

    def scoreboard(self, channel: str) -> Mapping[str, int]:
        """
        Gets the scoreboard for the current game in a channel.
        """
        with self._db() as conn:
            game = Game.restore(conn, channel)
            assert game is not None
            return game.scoreboard(conn)

    def choose_words(self) -> Sequence[str]:
        """
        Chooses a random set of words.
        """
        samples = int(self.args['words_per_hour'] * self.args['hours_per_round'])
        return random.sample(self._words, samples)
