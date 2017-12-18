
import discord
from discord.ext import commands
import cfg
from server import Server
import atexit

import traceback
import logging
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename='data/discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

bot = commands.Bot(command_prefix='?') #discord.Client()
servers = {}


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------------')

    game = discord.Game(name='Robot laeb...',url='https://www.politsei.ee/', type=1)
    await bot.change_presence(game=game)

    for server in bot.servers:
        n = Server(bot, server)
        servers[hash(server)] = n
        await n.ainit()


@bot.event
async def on_server_join(server):
    n = Server(bot, server)
    servers[hash(server)] = n
    await n.ainit()


@bot.event
async def on_server_remove(server):
    del servers[hash(server)]


@bot.event
async def on_message(message):
    if message.channel.type == discord.ChannelType.text:
        key = hash(message.server)

        if servers[key].init:
            await servers[key].handle_message(message)

@bot.event
async def on_member_join(member):
    key = hash(member.server)

    if servers[key].init:
        await servers[key].handle_member_join(member)


@bot.event
async def on_member_remove(member):
    key = hash(member.server)

    if servers[key].init:
        await servers[key].handle_member_remove(member)

@bot.event
async def on_error(event, *args, **kwargs):
    message = args[0]
    logging.warning(traceback.format_exc())

bot.run(cfg.token)

