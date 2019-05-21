from collections import defaultdict, namedtuple
import itertools
import random
import re
from typing import Any, Optional, Sequence, List, Tuple, MutableMapping, Mapping


def window(seq, n):
    "Returns a sliding window (of width n) over data from the iterable"
    it = iter(seq)
    result = tuple(itertools.islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


NGRAM_RE = re.compile(
    r"""
    [^ .!?,\-\n\r\t]+|[.,!?\-"]+
    """,
    re.X,
)
NGRAM_BREAK = re.compile(
    r"""
    [.?!]+"?
    """,
    re.X,
)

Link = MutableMapping[Optional[str], int]
Ngram = Tuple[Optional[str]]


class MarkovChain:
    def __init__(
        self,
        links: MutableMapping[Ngram, Link] = None,
        chance: Optional[float] = None,
        listen: Optional[bool] = None,
    ):
        self._links = links or {}
        self._chance = chance
        self._listen = listen

    @property
    def links(self) -> MutableMapping[Ngram, Link]:
        return self._links

    @property
    def chance(self) -> Optional[float]:
        return self._chance

    @chance.setter
    def chance(self, chance: Optional[float]):
        self.chance = chance

    @property
    def listen(self) -> bool:
        if self._listen is None:
            return True
        return self._listen

    @listen.setter
    def listen(self, listen: Optional[bool]):
        self.listen = listen

    def update_weight(self, words: Ngram, link: Optional[str], weight: int = None):
        weight = weight or 1
        if words not in self.links:
            self.links[words] = {link: weight}
        elif link not in self.links[words]:
            self.links[words][link] = weight
        else:
            self.links[words][link] += weight

    def choose_ngram(self) -> Optional[Ngram]:
        """
        Randomly chooses an n-gram from this chain's list.
        """
        if len(self.links) == 0:
            return None
        return random.choice(list(self.links.keys()))

    def choose_word(self, ngram: Ngram) -> Optional[str]:
        if ngram not in self.links or len(self.links[ngram]) == 0:
            return None
        links = self.links[ngram]
        return random.choices(list(links.keys()), links.values())[0]

    def make_sentence(self, max_length: int = None) -> Optional[str]:
        last_ngram = self.choose_ngram()
        if last_ngram is None:
            return None
        words = list(filter(bool, last_ngram))
        while True:
            if max_length is not None and len(words) >= max_length:
                break
            word = self.choose_word(last_ngram)
            if word is None:
                break
            words += [word]
            if NGRAM_BREAK.match(word):
                break
            last_ngram = (*last_ngram[1:], word)
            if last_ngram not in self.links:
                break
        sentence = ""
        for i, word in enumerate(words):
            if i != 0 and not NGRAM_BREAK.match(word) and not word.startswith(","):
                sentence += " "
            sentence += str(word)
        return sentence

    def train(self, text: str, order: int) -> None:
        """
        Trains this markov chain with the given string and order.
        """
        words = [match.group(0) for match in NGRAM_RE.finditer(text)]
        while len(words) < order + 1:
            words += [None]
        for view in window(words, order + 1):
            link = view[-1]
            ngram = view[:-1]
            self.update_weight(ngram, link)

    def merge(self, other: 'MarkovChain') -> None:
        for words, weights in other.links.items():
            for link, weight in weights.items():
                self.update_weight(words, link, weight)

    def total_weight(self) -> int:
        total = 0
        for weights in self.links.values():
            for weight in weights.values():
                total += weight
        return total

    def __repr__(self) -> str:
        return "<MarkovChain(ngrams=%r, chance=%s, listen=%s)>" % (
            self.links,
            self.chance,
            self.listen,
        )
