import discord
import asyncio
import datetime
import cfg

from mod.data import MData
from mod.command import MCommand


class Server:
    def __init__(self, bot, server):
        self.bot = bot
        self.server = server
        self.init = False

        self.mdata = None
        self.mcommand = None

    async def ainit(self):
        print("SERVER " + str(self.server.name))

        self.mdata = MData(self.bot, self.server)
        await self.mdata.ainit()
        self.mcommand = MCommand(self.bot, self.server, self.mdata)
        await self.mcommand.ainit()

        self.init = True

    async def handle_message(self, message):
        if message.content.startswith(cfg.commandsymbol):
            await self.mcommand.handle_command(message)
        else:
            await self.mdata.handle_message(message)
            print("A message")

    async def handle_member_join(self, member):
        await self.mdata.handle_member_join(member)

    async def handle_member_remove(self, member):
        await self.mdata.handle_member_remove(member)
