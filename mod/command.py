import cfg
import discord
from discord.ext import commands


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

    def split_line(text):

        # split the text
        words = text.split()

        # for each word in the line:
        for word in words:
            # print the word
            print(word)

    @commands.group(pass_context=True, no_pm=True)
    async def test(self, ctx):
        """This is the description of the """
        if ctx.invoked_subcommand is None:
            await self.client.send_message(
                ctx.message.author,
                "Invalid subcommand. ?help test for more information"
            )
            await self.client.delete_message(ctx.message)

    @test.command(pass_context=True, no_pm=True)
    async def c1(self, ctx, channel: str, theme: str, link: str):
        """
        {channel} {theme} {link} test test test
        :param channel: Name of the channel
        :type channel: str
        :param theme: A short description of the theme
        :type theme: str
        :param link: Link to an overview of the theme
        :type link: str
        """