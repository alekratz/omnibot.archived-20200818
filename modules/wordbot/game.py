import logging
from typing import Optional, Mapping, Sequence


log = logging.getLogger(__name__)


class Game:
    def __init__(self, *, id: Optional[int] = None, channel: str, start: int, end: int,
                 words: Sequence[str] = None):
        self.id = id
        self.channel = channel
        self.start = start
        self.end = end
        self.words = set(words)

    @property
    def duration(self) -> int:
        return self.end - self.start

    def save(self, conn):
        cur = conn.cursor()
        try:
            if self.id is None:
                # insert
                cur.execute("""
                            INSERT INTO game (channel, start, end)
                            VALUES (:channel, :start, :end)
                            """, {'channel': self.channel, 'start': self.start, 'end': self.end})
                this = Game.restore(conn, self.channel)
                self.id = this.id
                assert self.id is not None
                # insert words
                words = [(self.id, word) for word in self.words]
                cur.executemany("""
                            INSERT INTO word (game, word)
                            VALUES (?, ?)
                            """, words)
            else:
                # update
                cur.execute("""
                            UPDATE game
                            SET channel = :channel
                                start = :start
                                end = :end
                            WHERE id = :id
                            """, {'channel': self.channel, 'start': self.start, 'end': self.end,
                                  'id': self.id})
        finally:
            cur.close()

    @staticmethod
    def restore(conn, channel: str) -> Optional['Game']:
        cur = conn.cursor()
        cur.execute("""
                    SELECT game.id, start, end, channel, group_concat(word.word) FROM game
                    LEFT OUTER JOIN word ON word.game = game.id
                        AND word.id NOT IN (SELECT word FROM score WHERE score.game = game.id)
                    WHERE channel = :channel
                    AND start = (SELECT MAX(start) FROM game WHERE channel = :channel)
                    GROUP BY game.id, start, end, channel
                    """,
                    {'channel': channel})
        try:
            (id, start, end, channel, words) = cur.fetchone()
            if words is None:
                # sometimes, a set of words may not be present for a game - if that's the case then
                # it's an empty set.
                words = set()
            else:
                words = set(words.split(','))
            return Game(id=id, channel=channel, start=start, end=end, words=words)
        except TypeError:
            # game doesn't exist
            return None
        finally:
            cur.close()

    def score(self, conn, word: str, user: str, line: str):
        cur = conn.cursor()
        assert word in self.words
        self.words.remove(word)
        try:
            cur.execute("""
                        INSERT INTO score (game, word, user, line)
                        VALUES (
                            :game,
                            (SELECT id FROM word WHERE word.word = :word AND game = :game),
                            :user,
                            :line)
                        """, {'game': self.id, 'word': word, 'user': user, 'line': line})
        finally:
            cur.close()

    def scoreboard(self, conn) -> Mapping[str, int]:
        """
        Gets a mapping of user scores per channel.
        """
        assert self.id is not None
        cur = conn.cursor()
        cur.execute("SELECT user FROM score WHERE game = ?", (self.id,))
        scores = {}
        try:
            for user, in cur.fetchall():
                if user not in scores:
                    scores[user] = 0
                scores[user] += 1
        except:
            log.exception("Could not retrieve scoreboard for game with id = %s and channel = %s",
                          self.id, self.channel)
            raise
        finally:
            cur.close()
        return scores
