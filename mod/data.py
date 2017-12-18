import cfg
import discord
import os
import datetime
import sqlite3
import pickle


class MData:
    def __init__(self, bot, server):
        self.bot = bot
        self.server = server
        self.init = False

        self.users = {}

        for member in server.members:
            self.users[member.id] = self.User(member)

        self.roles = {}

        for role in server.roles:
            self.roles[role.name] = role


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

        print("MDATA: Loading data for " + 'data/' + str(id) + '.db')

        if os.path.isfile('data/' + str(id) + '.db'):
            conn = sqlite3.connect('data/' + str(id) + '.db')
            c = conn.cursor()

            c.execute('''SELECT id, mcount, ccount, qmcount, qccount FROM users''')
            all_rows = c.fetchall()
            for row in all_rows:
                _id = str(row[0])
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
        else:
            print("MDATA: no database found - " + 'data/' + str(id) + '.db')

        await self.update_stats(utctime)

    def save_data(self):
        if self.init:
            id = self.server.id

            print("MDATA: Saving")
            if os.path.isfile('data/' + str(id) + '.db'):
                os.remove('data/' + str(id) + '.db')

            conn = sqlite3.connect('data/' + str(id) + '.db')
            c = conn.cursor()

            # Create tables
            c.execute('''
                            CREATE TABLE IF NOT EXISTS users
                            (id BIGINT, mcount INT, ccount BIGINT, qmcount INT, qccount BIGINT, name TEXT)
                            ''')
            c.execute('''
                                    CREATE TABLE IF NOT EXISTS metadata
                                    (time TEXT)
                                    ''')

            # Insert user data
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
                            if len(msg.content) > 20:
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
        if str(message.channel) in cfg.qualityc and len(message.content) > 20:
            self.users[id].qmcount += 1
            self.users[id].qccount += len(message.content)

        new_role = await self.users[id].update_role(self.bot)

        if new_role is not None:
            embed = discord.Embed(title="Tubli töö, goi", description="Sa oled nüüd tase " + str(new_role.name) + "", color=0x00ff00, url='https://kapo.ee/')
            embed.set_author(name=message.author.name)
            embed.set_image(url=message.author.avatar_url)
            if self.users[id].qmcount:
                embed.add_field(name="Väärt sõnumeid",
                                value=str(round(self.users[id].qmcount/self.users[id].mcount*100))+"% ("+str(self.users[id].qmcount)+")",inline=True)
                embed.add_field(name="Kõik sõnumid",
                                value=str(self.users[id].mcount), inline=True)
                embed.add_field(name="Keskmine tähtede arv",
                                value=str(round(self.users[id].qccount/self.users[id].qmcount)), inline=True)

            if self.roles['lennu'] in self.users[id].member.roles:
                embed.set_footer(text='Lennu', icon_url='https://i.imgur.com/wni7YGI.png')
            elif self.roles['saabas'] in self.users[id].member.roles:
                embed.set_footer(text='Saabas', icon_url='https://i.imgur.com/gSayA5K.png')
            elif self.roles['mard'] in self.users[id].member.roles:
                embed.set_footer(text='Mard', icon_url='https://i.imgur.com/1Zy1CvG.png')
            elif self.roles['volga'] in self.users[id].member.roles:
                embed.set_footer(text='Volga', icon_url='https://i.imgur.com/RdHx5qT.png')

            await self.bot.send_message(message.channel, embed=embed)

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
            highest_role = None
            is_role_fix  = False

            for level in cfg.threshold:
                role_to = None
                for r in self.member.server.roles:
                    if r.name.startswith(level['name']):
                        role_to = r
                        break

                is_role = (role_to in self.member.roles)

                if is_role and highest_role is None:
                    is_role_fix = True

                if level['role'] is None or level['role'] in [y.name for y in self.member.roles]:
                    if not is_role:
                        if self.qmcount >= level['count']:
                            await bot.add_roles(self.member, role_to)
                            print("MDATA: Added role '" + str(role_to.name) + "' to user '" + str(self.member.name) + "' - " + str(self.qmcount))

                            if highest_role is None:
                                highest_role = role_to

                            continue
                    else:
                        continue

                if is_role:
                    await bot.remove_roles(self.member, role_to)
                    print("MDATA: Removed role '" + str(role_to.name) + "' from user '" + str(self.member.name) + "' - " + str(self.qmcount))

            if not is_role_fix:
                return highest_role
            else:
                return None