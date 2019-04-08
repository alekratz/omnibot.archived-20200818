import logging
from omnibot import Module, ModuleError, Server

log = logging.getLogger(__name__)

class Nickserv(Module):
    default_args = {
        'nickserv': 'NickServ',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_load(self):
        required = {'password', 'email',}
        present = set(self.args.keys())
        missing = required - present
        if missing:
            raise ModuleError("Missing required configuration values: {}".format(missing))

    async def on_message(self, channel, who, text):
        if text.startswith("Nickname") and text.endswith("registered.") and not text.endswith("may not be registered."):
            self.login()
        elif 'This nickname is registered' in text:
            self.login()
        elif 'Your nickname is not registered' in text:
            self.register()

    def should_handle(self, msg) -> bool:
        return bool(msg.prefix) \
                and bool(msg.prefix.nick) \
                and msg.prefix.nick.lower() == self.args['nickserv'].lower()

    def login(self):
        self.server.send_message(self.args['nickserv'],
                                 'identify {}'.format(self.args['password']))

    def register(self):
        self.server.send_message(self.args['nickserv'],
                                 'register {} {}'.format(self.args['password'], self.args['email']))


ModuleClass = Nickserv
