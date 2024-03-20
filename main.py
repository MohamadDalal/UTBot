import discord
import json
import asyncio
#from discord import app_commands
from discord.ext import commands
from bot_commands import SlashCommandsCog
from roleMessage import roleMessage


class MyBot(commands.Bot):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.testGuild = discord.Object(id=1056227226338734201)
        self.reactionMessages = {}
        with open("test_reactionMessages.json", "r") as f:
            self.reactionMessages = json.load(f)

    def save_reactionMessage(self):
        with open("test_reactionMessages.json", "w") as f:
            json.dump(self.reactionMessages, f)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):

        if payload.user_id == self.application_id:
            return

        # Make sure that the message the user is reacting to is an event message.
        eventDict = self.reactionMessages.get(str(payload.message_id), None)
        if eventDict is None:
            return
        
        guild = self.get_guild(payload.guild_id)
        if guild is None:
            # Check if we're still in the guild and it's cached.
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
                pass

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):

        if payload.user_id == self.application_id:
            return
        
        # Make sure that the message the user is reacting to is an event message.
        eventDict = self.reactionMessages.get(str(payload.message_id), None)
        if eventDict is None:
            return
        
        guild = self.get_guild(payload.guild_id)
        if guild is None:
            # Check if we're still in the guild and it's cached.
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
        await self.add_cog(SlashCommandsCog(bot), guild=self.testGuild)
        await self.add_cog(roleMessage(bot), guild=self.testGuild)
        self.tree.copy_global_to(guild=self.testGuild)
        await self.tree.sync(guild=self.testGuild)
        #await self.tree.sync()


#async def setup(bot: commands.Bot) -> None:
    #await bot.add_cog(SlashCommandsCog(bot))

if __name__ == "__main__":
    settings = {}
    with open("settings.json", "r") as f:
        settings = json.load(f)
    print(getattr(discord.User, '__origin__', None))
    intents = discord.Intents.default()
    intents.messages = True
    intents.guilds = True
    intents.members = True
    bot = MyBot(command_prefix='!', intents=intents)
    #asyncio.run(setup(bot))
    #bot.add_cog(SlashCommandsCog(bot))
    #print(bot.cogs)
    #cog = bot.get_cog('SlashCommandsCog')
    #cmds = cog.get_commands()
    #print([c.name for c in cmds])
    bot.run(settings["Token"])