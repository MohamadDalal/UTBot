import discord
import json
import argparse
import asyncio
import sys
#from discord import app_commands
#from discord.ext import commands
from botFunctions import MyBotFunctions
#from bot_commands import SlashCommandsCog
from roleMessage import roleMessage
from messageCog import messageCog
from welcomeCog import welcomeCog
from logger import Logger

"""
    Needed permissions:
    - Manage Roles
    - Read Messages/View Channels
    - Send Messages
    - Manage Sessions
    - Read Message History
    - Use External Emojis
    - Add Reactions
"""


class MyBot(MyBotFunctions):
    
    def __init__(self, testbot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isTest = testbot
        self.testGuilds = (discord.Object(id=1056227226338734201),discord.Object(id=1223451123591942174),)
        self.reactionMessages = {}
        self.reactionMessagesPath = "test_reactionMessages.json" if testbot else "reactionMessages.json"
        self.welcomeSettings = {}
        self.welcomeSettingsPath = "test_welcomeSettings.json" if testbot else "welcomeSettings.json"
        print(f"Is this the test bot?: {testbot}")
        with open(self.reactionMessagesPath, "r") as f:
            self.reactionMessages = json.load(f)
        with open(self.welcomeSettingsPath, "r") as f:
            self.welcomeSettings = json.load(f)

    async def on_ready(self):
        #await self.tree.sync()
        print(self.cogs)
        print(f'Logged in as {self.user.name} with id {self.application_id}')

    async def setup_hook(self) -> None:
        if self.isTest:
            #await self.add_cog(SlashCommandsCog(bot), guilds=self.testGuilds)
            await self.add_cog(roleMessage(bot=self), guilds=self.testGuilds)
            await self.add_cog(messageCog(bot=self), guilds=self.testGuilds)
            await self.add_cog(welcomeCog(bot=self), guilds=self.testGuilds)
            for TG in self.testGuilds:
                self.tree.copy_global_to(guild=TG)
                await self.tree.sync(guild=TG)
            #await self.add_cog(SlashCommandsCog(bot))
            #await self.add_cog(roleMessage(bot))
            #await self.tree.sync()
        else:
            #await self.add_cog(SlashCommandsCog(bot))
            await self.add_cog(roleMessage(bot=self))
            await self.add_cog(messageCog(bot=self))
            #await self.add_cog(welcomeCog(bot=self))
            await self.tree.sync()


#async def setup(bot: commands.Bot) -> None:
    #await bot.add_cog(SlashCommandsCog(bot))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-main-bot", action="store_true", help="Only add if you want to run the main bot")
    args = parser.parse_args()
    settings = {}
    settingsPath = "settings.json" if args.use_main_bot else "tester_settings.json"
    with open(settingsPath, "r") as f:
        settings = json.load(f)
    # Configure logging
    logger = Logger(settings["LogPath"])
    sys.stdout = logger
    sys.stderr = logger
    print()
    print("----------------------------New Session----------------------------")
    logger.setPrintDateTime(True)
    
    print(getattr(discord.User, '__origin__', None))
    intents = discord.Intents.default()
    intents.messages = True
    intents.guilds = True
    intents.members = True
    intents.guild_scheduled_events = True
    bot = MyBot(not args.use_main_bot, command_prefix='!', intents=intents)
    #asyncio.run(setup(bot))
    #bot.add_cog(SlashCommandsCog(bot))
    #print(bot.cogs)
    #cog = bot.get_cog('SlashCommandsCog')
    #cmds = cog.get_commands()
    #print([c.name for c in cmds])
    bot.run(settings["Token"])
