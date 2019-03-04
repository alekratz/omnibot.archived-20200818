import random
import re
from omnibot import Module, module_commands


rtd_re = re.compile(r'(\d+)?d(\d+)')


@module_commands('!rtd', '!d20')
class Rtd(Module):
    @staticmethod
    def default_args():
        return {
            'max_sides': 100,
            'max_dice': 100,
        }

    async def on_command(self, cmd, channel, who, text):
        parts = text.split()
        reply = None
        if cmd == '!rtd':
            reply = self.rtd(parts)
        elif cmd == '!d20':
            reply = self.d20(parts)
        if reply is None:
            return
        if channel is None:
            self.server.send_message(who, reply)
        else:
            self.server.send_message(channel, "{}: {}".format(who, reply))

    def rtd(self, parts):
        if len(parts) < 2:
            return None
        match = rtd_re.match(parts[1])
        if not match:
            return None
        count_match = match.groups(1)
        if count_match:
            count = int(count_match[0])
        else:
            count = 1
        sides = int(match.groups(2)[0])
        if count > self.args['max_dice'] or sides > self.args['max_sides'] or 0 in (count, sides):
            return None

        rolls = [random.randint(1, sides) for _ in range(count)]
        if count == 1:
            return str(rolls[0])
        else:
            return "{} = {}".format(' + '.join(map(str, rolls)), sum(rolls))

    def d20(self, parts):
        roll = random.randint(1, 20)
        if len(parts) == 1:
            return str(roll)
        check = ' '.join(parts[1:])
        reply = "{} to {}".format(roll, check)
        if roll == 20:
            reply += ' -- critical success!'
        elif roll == 1:
            reply += ' -- critical failure!'
        return reply


ModuleClass = Rtd
