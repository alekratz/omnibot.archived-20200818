from collections import defaultdict
import functools
import itertools
import logging
from pathlib import Path
import pickle
import random
from typing import Optional, MutableMapping, Mapping
from omnibot import Module
from .chain import MarkovChain


log = logging.getLogger(__name__)


class Markov(Module):
    default_args = {
        "chainfile": "markov.pickle",
        "order": 2,
        "save_every": 300.0,
        "reply_chance": 0.01,
    }

    chains: MutableMapping[str, MutableMapping[str, MarkovChain]]
    all_chains: MutableMapping[str, MarkovChain]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.chains = defaultdict(functools.partial(defaultdict, MarkovChain))
        self.all_chains = defaultdict(MarkovChain)
        self.__save_task = None

    @property
    def order(self) -> int:
        return self.args["order"]

    @property
    def reply_chance(self) -> float:
        return self.args["reply_chance"]

    @property
    def save_every(self) -> float:
        return self.args["save_every"]

    @property
    def chainfile(self) -> Path:
        return self.data_dir() / Path(self.args['chainfile'])

    async def on_load(self):
        path = self.chainfile
        log.debug("Loading markov chain file %s", path)
        if not path.exists():
            log.info("Markov chain file %s does not exist, it will be created", path)
            return
        with open(path, "rb") as fp:
            self.chains = pickle.load(fp)
        log.debug("Building allchains")
        self.all_chains = defaultdict(MarkovChain)
        for channel, chains in self.chains.items():
            for chain in chains.values():
                self.all_chains[channel].merge(chain)
        log.debug("Registering save handler")
        self.__save_task = self.loop.call_later(self.save_every, self.save)

    async def on_unload(self):
        if self.__save_task is not None:
            self.__save_task.cancel()
        self.save(shutdown=True)

    def save(self, shutdown: bool = False):
        path = self.chainfile
        log.debug("Saving markov chain file %s", path)
        with open(path, "wb") as fp:
            pickle.dump(self.chains, fp)
        if shutdown:
            self.__save_task = None
        else:
            self.__save_task = self.loop.call_later(self.save_every, self.save)

    async def on_message(self, channel: Optional[str], who: Optional[str], text: str):
        if None in (channel, who):
            return
        words = text.split(" ")

        # handle command
        if words and words[0] == "!markov":
            await self.on_command("!markov", channel, who, text)
            return

        chain = self.chains[channel][who]
        if chain.listen == False:
            return
        chain.train(text, self.order)
        self.all_chains[channel].train(text, self.order)
        chance = self.reply_chance if chain.chance is None else chain.chance
        if chance == 0.0:
            return
        if random.random() < chance:
            self.interject(channel, who, chain)

    async def on_command(
        self, command: str, channel: Optional[str], who: Optional[str], text: str
    ):
        if None in (channel, who) or command != "!markov":
            return

        parts = text.split(" ")
        if len(parts) == 1:
            return

        command = parts[1]
        if command == "force":
            self.interject(channel, who)
        elif command == "all":
            allchain = self.all_chains[channel]
            self.interject(channel, who, allchain)
        elif command in ("emulate", "mock"):
            if len(parts) < 3:
                return
            mock = parts[2].lower()
            for name, chain in self.chains[channel].items():
                if mock == name.lower():
                    self.interject(channel, who, chain)
                    break
        elif command == "status":
            my_total = self.chains[channel][who].total_weight()
            all_total = self.all_chains[channel].total_weight()
            if all_total == 0:
                return
            status = (my_total / all_total) * 100.0
            self.server.send_message(
                channel, "{}: you are worth {:.4f}% of the channel".format(who, status)
            )
        elif command == "listen":
            chain[channel][who].listen = True
        elif command == "ignore":
            chain[channel][who].listen = False
        elif command == "help":
            # TODO help command
            pass
        elif command == "chance":
            error_message = "Invalid markov chance format. Must be decimal value between 0.0 and {}".format(
                self.reply_chance
            )
            if len(parts) < 3:
                self.server.send_message(who, error_message)
            try:
                chain[channel][who].chance = float(parts[2])
            except ValueError:
                self.server.send_message(who, error_message)

    def interject(self, channel: str, who: str, chain: MarkovChain = None) -> None:
        if chain is None:
            if who not in self.chains[channel]:
                return
            chain = self.chains[channel][who]
        sentence = chain.make_sentence()
        if sentence is None:
            return
        self.server.send_message(channel, "{}: {}".format(who, sentence))


ModuleClass = Markov
