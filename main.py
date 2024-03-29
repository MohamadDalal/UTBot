import discord
import json
import argparse
import asyncio
import sys
#from discord import app_commands
from discord.ext import commands
from bot_commands import SlashCommandsCog
from roleMessage import roleMessage
from logger import Logger


class MyBot(commands.Bot):
    
    def __init__(self, testbot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isTest = testbot
        self.testGuilds = (discord.Object(id=1056227226338734201),)
        self.reactionMessages = {}
        self.reactionMessagesPath = "test_reactionMessages.json" if testbot else "reactionMessages.json"
        print(f"Is this the test bot?: {testbot}")
        with open(self.reactionMessagesPath, "r") as f:
            self.reactionMessages = json.load(f)

    def save_reactionMessage(self):
        with open(self.reactionMessagesPath, "w") as f:
            json.dump(self.reactionMessages, f, indent=2)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):

        if payload.user_id == self.application_id:
            return

        # Make sure the server we read the message from is registered under the rection messages dictionary
        guild = self.get_guild(payload.guild_id)
        guildReactionMessages = self.reactionMessages.get(str(payload.guild_id), None)
        if guildReactionMessages is None or guild is None:
            # Also checks if we're still in the guild and it's cached.
            return

        # Make sure that the message the user is reacting to is an event message.
        eventDict = guildReactionMessages.get(str(payload.message_id), None)
        if eventDict is None:
            return
        
        print(payload.emoji)

        if eventDict["Type"] == "Role Message":
            try:
                role_id = eventDict["Roles"][str(payload.emoji)]
            except KeyError:
                # If the emoji isn't the one we care about then exit as well.
                return
            print(role_id)
            role = guild.get_role(int(role_id))
            print(role)
            if role is None:
                # Make sure the role still exists and is valid.
                return

            try:
                # Finally, add the role.
                await payload.member.add_roles(role)
            except discord.HTTPException as e:
                # If we want to do something in case of errors we'd do it here.
                print("HTTP exception in reaction add callback")
                print(e)
                # Add a functionality where it pastes the error and its possible solution in a dedicated bot error channel
                # Will also need a command to assign a channel as dedicated bot error channel.
                pass

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):

        if payload.user_id == self.application_id:
            return
        
        # Make sure the server we read the message from is registered under the rection messages dictionary
        guild = self.get_guild(payload.guild_id)
        guildReactionMessages = self.reactionMessages.get(str(payload.guild_id), None)
        if guildReactionMessages is None or guild is None:
            # Also checks if we're still in the guild and it's cached.
            return
        
        # Make sure that the message the user is reacting to is an event message.
        eventDict = guildReactionMessages.get(str(payload.message_id), None)
        if eventDict is None:
            return

        print(payload.emoji)

        if eventDict["Type"] == "Role Message":
            try:
                role_id = eventDict["Roles"][str(payload.emoji)]
            except KeyError:
                # If the emoji isn't the one we care about then exit as well.
                return
            print(role_id)
            role = guild.get_role(int(role_id))
            print(role)
            if role is None:
                # Make sure the role still exists and is valid.
                return

            # The payload for `on_raw_reaction_remove` does not provide `.member`
            # so we must get the member ourselves from the payload's `.user_id`.
            print(payload.user_id)
            member = guild.get_member(payload.user_id)
            print(member)
            if member is None:
                # Make sure the member still exists and is valid.
                return

            try:
                # Finally, remove the role.
                await member.remove_roles(role)
            except discord.HTTPException as e:
                # If we want to do something in case of errors we'd do it here.
                print("HTTP exception in reaction add callback")
                print(e)
                pass

    async def on_ready(self):
        #await self.tree.sync()
        print(self.cogs)
        print(f'Logged in as {self.user.name} with id {self.application_id}')

    async def setup_hook(self) -> None:
        if self.isTest:
            await self.add_cog(SlashCommandsCog(bot), guilds=self.testGuilds)
            await self.add_cog(roleMessage(bot), guilds=self.testGuilds)
            for TG in self.testGuilds:
                self.tree.copy_global_to(guild=TG)
                await self.tree.sync(guild=TG)
            #await self.add_cog(SlashCommandsCog(bot))
            #await self.add_cog(roleMessage(bot))
            #await self.tree.sync()
        else:
            await self.add_cog(SlashCommandsCog(bot))
            await self.add_cog(roleMessage(bot))
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
    bot = MyBot(not args.use_main_bot, command_prefix='!', intents=intents)
    #asyncio.run(setup(bot))
    #bot.add_cog(SlashCommandsCog(bot))
    #print(bot.cogs)
    #cog = bot.get_cog('SlashCommandsCog')
    #cmds = cog.get_commands()
    #print([c.name for c in cmds])
    bot.run(settings["Token"])
