import random
import time
from omnibot import Module, module_commands


fortunes = [
        'Reply hazy, try again',
        'Excellent Luck',
        'Good Luck',
        'Average Luck',
        'Bad Luck',
        'Good news will come to you by mail',
        '´_ゝ`',
        'ﾀ━━━━━━(ﾟ∀ﾟ)━━━━━━ !!!!',
        'You will meet a dark handsome stranger',
        'Better not tell you now',
        'Outlook good',
        'Very Bad Luck',
        'Godly Luck',
]


@module_commands('!fortune')
class Fortune(Module):
    default_args = {
        'timeout': 300,
    }

    async def on_load(self):
        self.timeouts = {}

    async def on_command(self, cmd, channel, who, text):
        if not channel:
            return
        if channel not in self.timeouts:
            self.timeouts[channel] = {}
        now = time.time()
        if who not in self.timeouts[channel]:
            self.timeouts[channel][who] = 0
        if now - self.timeouts[channel][who] < self.args['timeout']:
            return
        self.timeouts[channel][who] = now
        chosen = random.choice(fortunes)
        self.server.send_message(channel, "{}: {}".format(who, chosen))


ModuleClass = Fortune
