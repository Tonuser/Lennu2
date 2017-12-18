import cfg
import discord
import os
import datetime
import sqlite3


class MData:
    def __init__(self, bot, server):
        self.bot = bot
        self.server = server
        self.init = False

        self.users = {}

        for member in server.members:
            self.users[member.id] = self.User(member)

    async def ainit(self):
        await self.load_data()

        self.init = True

    def __del__(self):
        if self.init:
            self.save_data()
        else:
            print("MDATA: Couldn't save, program wasn't initialised")

    async def load_data(self):
        utctime = None
        id = self.server.id

        if os.path.isfile('data/' + str(id) + '.db'):
            conn = sqlite3.connect('data/' + str(id) + '.db')
            c = conn.cursor()

            c.execute('''SELECT id, mcount, ccount, qmcount, qccount FROM users''')
            all_rows = c.fetchall()
            for row in all_rows:
                _id = row[0]
                _mcount = row[1]
                _ccount = row[2]
                _qmcount = row[3]
                _qccount = row[4]

                if _id in self.users:
                    self.users[_id].mcount = _mcount
                    self.users[_id].ccount = _ccount
                    self.users[_id].qmcount = _qmcount
                    self.users[_id].qccount = _qccount

            c.execute('''SELECT time FROM metadata''')
            metadata = c.fetchone()
            utctime = metadata[0]

            conn.close()

        await self.update_stats(utctime)

    def save_data(self):
        if self.init:
            id = self.server.id

            print("MDATA: Saving")
            if os.path.isfile('data/' + str(id) + '.db'):
                os.remove('data/' + str(id) + '.db')

            conn = sqlite3.connect('data/' + str(id) + '.db')
            c = conn.cursor()

            # Create a table
            c.execute('''
                            CREATE TABLE IF NOT EXISTS users
                            (id BIGINT, mcount INT, ccount BIGINT, qmcount INT, qccount BIGINT, name TEXT)
                            ''')
            c.execute('''DELETE FROM users''')
            c.execute('''
                                    CREATE TABLE IF NOT EXISTS metadata
                                    (time TEXT)
                                    ''')
            c.execute('''DELETE FROM metadata''')

            # Insert a row of data
            to_insert = set()
            for key in self.users:
                member = self.users[key]
                to_insert.add((str(member.id), str(member.mcount),
                               str(member.ccount), str(member.qmcount),
                               str(member.qccount), str(member.member.name),))
            c.executemany("INSERT INTO users (id, mcount, ccount, qmcount, qccount, name)"
                          "VALUES (?,?,?,?,?,?)", to_insert)

            # Insert metadata
            params = (str(datetime.datetime.utcnow()),)
            c.execute("INSERT INTO metadata (time) VALUES (?)", params)

            # Save
            conn.commit()

            conn.close()

            print("MDATA: Saved")
        else:
            raise Exception("Tried to save data without initialising server")

    async def update_stats(self, time):
        print("MDATA: Updating hierarchy - from: " + str(time))

        channels = self.bot.get_all_channels()
        members = self.bot.get_all_members()

        if time is None:
            for member in members:
                self.users[member.id].mcount = 0
                self.users[member.id].ccount = 0

        n = 0
        for channel in channels:
            if channel.type == discord.ChannelType.text and channel.permissions_for(self.server.me).read_message_history:
                n += 1
                print(str(channel) + " - " + str(n))
                if str(channel) in cfg.qualityc:
                    async for msg in self.bot.logs_from(channel, limit=1000000, after=time):
                        id = msg.author.id
                        if id in self.users:
                            self.users[id].qmcount += 1
                            self.users[id].qccount += len(msg.content)
                            self.users[id].mcount += 1
                            self.users[id].ccount += len(msg.content)
                else:
                    async for msg in self.bot.logs_from(channel, limit=1000000, after=time):
                        id = msg.author.id
                        if id in self.users:
                            self.users[id].mcount += 1
                            self.users[id].ccount += len(msg.content)

        print("MDATA: Updated hierarchy")
        print('------------')

    async def handle_message(self, message):
        id = message.author.id

        self.users[id].mcount += 1
        self.users[id].ccount += len(message.content)
        if str(message.channel) in cfg.qualityc:
            self.users[id].qmcount += 1
            self.users[id].qccount += len(message.content)

        await self.users[id].update_role(self.bot)

    async def handle_member_join(self, member):
        id = member.id

        self.users[id] = self.User(member)
        print("MDATA: New user " + str(member.name))

    async def handle_member_remove(self, member):
        id = member.id

        del self.users[id]
        print("MDATA: User left " + str(member.name))

    class User:
        def __init__(self, member):
            self.member = member
            self.id = member.id
            self.qmcount = 0  # Quality message count
            self.qccount = 0  # Quality character count
            self.mcount  = 0  # Total message count
            self.ccount  = 0  # Total character count

        async def update_role(self, bot):
            for level in cfg.threshold:
                role_to = None
                for r in self.member.server.roles:
                    if r.name.startswith(level['name']):
                        role_to = r
                        break

                if level['role'] is None or level['role'] in [y.name for y in self.member.roles]:
                    if self.qmcount >= level['count']:
                        await bot.add_roles(self.member, role_to)
                        print("MDATA: Added role '" + str(role_to.name) + "' to user '" + str(self.member.name) + "'")
                        continue

                if role_to in self.member.roles:
                    await bot.remove_roles(self.member, role_to)
                    print("MDATA: Removed role '" + str(role_to.name) + "' from user '" + str(self.member.name) + "'")
