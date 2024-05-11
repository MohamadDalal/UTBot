import discord
import json
from discord import EntityType
from discord.ext import commands

class MyBotFunctions(commands.Bot):

    welcomeSettingsPath = ""
    welcomeSettings = {}
    reactionMessagesPath = ""
    reactionMessages = {}

    def save_reactionMessage(self):
        with open(self.reactionMessagesPath, "w") as f:
            json.dump(self.reactionMessages, f, indent=2)
    
    def save_welcomeSettings(self):
        with open(self.welcomeSettingsPath, "w") as f:
            json.dump(self.welcomeSettings, f, indent=2)

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
        
        print("Hello from raw reaction add")
        print(f"Reaction:\t{payload.emoji}")

        if eventDict["Type"] == "Role Message":
            try:
                role_id = eventDict["Roles"][str(payload.emoji)]
            except KeyError:
                channel = self.get_partial_messageable(eventDict["Channel"])
                message = await channel.fetch_message(payload.message_id)
                print(f"User {payload.member} reacted with {payload.emoji}, which is not a role reaction.")
                print("Removing reaction")
                await message.remove_reaction(payload.emoji, payload.member)
                # If the emoji isn't the one we care about then exit as well.
                return
            print(f"Role ID:\t{role_id}")
            role = guild.get_role(int(role_id))
            print(f"Role:\t{role}")
            if role is None:
                # Make sure the role still exists and is valid.
                return
            print(f"User ID:\t{payload.user_id}")
            print(f"Username:\t{payload.member}")
            try:
                # Finally, add the role.
                await payload.member.add_roles(role)
            except discord.HTTPException as e:
                # If we want to do something in case of errors we'd do it here.
                print("HTTP exception in reaction add callback")
                print(e)
                #raise e
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

        print("Hello from raw reaction remove")
        print(f"Reaction:\t{payload.emoji}")

        if eventDict["Type"] == "Role Message":
            try:
                role_id = eventDict["Roles"][str(payload.emoji)]
            except KeyError:
                # If the emoji isn't the one we care about then exit as well.
                return
            print(f"Role ID:\t{role_id}")
            role = guild.get_role(int(role_id))
            print(f"Role:\t{role}")
            if role is None:
                # Make sure the role still exists and is valid.
                return

            # The payload for `on_raw_reaction_remove` does not provide `.member`
            # so we must get the member ourselves from the payload's `.user_id`.
            print(f"User ID:\t{payload.user_id}")
            member = guild.get_member(payload.user_id)
            print(f"Username:\t{member}")
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

    async def on_member_join(self, member:discord.Member):
        # Make sure the server we read the message from is registered under the reaction messages dictionary
        guild = member.guild
        guildWelcomeSettings = self.welcomeSettings.get(str(guild.id), None)
        if guildWelcomeSettings is None or guild is None:
            # Also checks if we're still in the guild and it's cached.
            return
        if guildWelcomeSettings["Enabled"]:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False, send_messages=False),
                member: discord.PermissionOverwrite(read_messages=True, read_message_history=True, view_channel=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, read_message_history=True, view_channel=True, send_messages=True)
            }
            createdChannel = await guild.create_text_channel(f"welcome-{member.name}", overwrites=overwrites,
                                                             category=guild.get_channel(int(guildWelcomeSettings["Category"])), 
                                                             reason=f"Welcome channel for {member.name}")
            message = f"Hello <@{member.id}>\n\n{guildWelcomeSettings['Message']}"
            await createdChannel.send(message)
        else:
            return
    
    async def on_scheduled_event_create(self, event:discord.ScheduledEvent):
        print("Hello from scheduled event create")
        #print(event)
        #print(event.guild)
        #print(event.channel)
        #print(event.entity_type)
        #print(event.start_time)
        #print(event.end_time)
        #print(event.url)
        if event.entity_type == EntityType.voice:
            request = {"key": "1234", "type": "event", "action": "create", 
                       "location_type": "channel", "data": {"name": event.name,
                                                            "description": event.description,
                                                            "start_time": event.start_time,
                                                            "channel_name": event.channel.name,
                                                            "channel_link": event.channel.jump_url,
                                                            "url": event.url}}
        elif event.entity_type == EntityType.external:
            request = {"key": "1234", "type": "event", "action": "create", 
                       "location_type": "external", "data": {"name": event.name,
                                                            "description": event.description,
                                                            "start_time": event.start_time,
                                                            "end_time": event.end_time,
                                                            "location": event.location,
                                                            "url": event.url}}
        print(f"Sending request:\n\t{request}")

    async def on_scheduled_event_delete(self, event:discord.ScheduledEvent):
        print("Hello from scheduled event delete")
        print(event)
        if event.entity_type == EntityType.voice:
            request = {"key": "1234", "type": "event", "action": "delete", 
                       "location_type": "channel", "data": {"name": event.name,
                                                            "description": event.description,
                                                            "start_time": event.start_time,
                                                            "channel_name": event.channel.name,
                                                            "channel_link": event.channel.jump_url,
                                                            "url": event.url}}
        elif event.entity_type == EntityType.external:
            request = {"key": "1234", "type": "event", "action": "delete", 
                       "location_type": "external", "data": {"name": event.name,
                                                            "description": event.description,
                                                            "start_time": event.start_time,
                                                            "end_time": event.end_time,
                                                            "location": event.location,
                                                            "url": event.url}}
        print(f"Sending request:\n\t{request}")

    async def on_scheduled_event_update(self, old_event:discord.ScheduledEvent, event:discord.ScheduledEvent):
        print("Hello from scheduled event update")
        print(old_event)
        print(event)
        if event.entity_type == EntityType.voice:
            request = {"key": "1234", "type": "event", "action": "update", 
                       "location_type": "channel", "data": {"name": event.name,
                                                            "description": event.description,
                                                            "start_time": event.start_time,
                                                            "channel_name": event.channel.name,
                                                            "channel_link": event.channel.jump_url,
                                                            "url": event.url}}
        elif event.entity_type == EntityType.external:
            request = {"key": "1234", "type": "event", "action": "update", 
                       "location_type": "external", "data": {"name": event.name,
                                                            "description": event.description,
                                                            "start_time": event.start_time,
                                                            "end_time": event.end_time,
                                                            "location": event.location,
                                                            "url": event.url}}
        print(f"Sending request:\n\t{request}")