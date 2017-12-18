import cfg
import discord


class MCommand:
    def __init__(self, bot, server, mdata):
        self.bot = bot
        self.server = server
        self.mdata = mdata
        self.init = False

    async def ainit(self):
        self.init = True

    async def handle_command(self, message):
        print(message.content)
