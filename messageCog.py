import discord
from discord import app_commands
from discord.ext import commands
from messageAssets import *

class MessageCog(commands.GroupCog, name="message"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()  # this is now required for GroupCog.

    def _printDecodedURL(self, originGuild, urlGuild, channel, message):
        print(f"Origin guild:\t{originGuild}")
        print(f"Message guild:\t{urlGuild}")
        print(f"Message channel:\t{channel}")
        print(f"Message:\t\t{message}")

    @app_commands.command(name="send", description="Sends a message in the current channel")
    async def send_message(self, interaction: discord.Interaction):
        print(f"Hello from send-message")
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"Cannot send message. User <@{interaction.user.id}> is not adminstrator.", ephemeral=True)
            return
        try:
            channel = interaction.channel
            modal = SendMessage(channels=[channel,])
            await interaction.response.send_modal(modal)
            #view = SendMessageView()
            #await interaction.response.send_message("Test message", view=view, ephemeral=True)
        except discord.errors.Forbidden as e:
            print(e)
            await interaction.response.send_message(f"I do not have permission. Check error logs", ephemeral=True)
        except Exception as e:
            #print(e)
            await interaction.response.send_message(f"Some other error happened. Check error logs.", ephemeral=True)
            raise e
        
    @app_commands.command(name="edit", description="Edits a message sent by the bot.")
    @app_commands.describe(message_url="The link to the message")
    async def edit_message(self, interaction: discord.Interaction, message_url:str):
        print(f"Hello from edit-message, {message_url}")
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"Cannot edit message. User <@{interaction.user.id}> is not adminstrator.", ephemeral=True)
            return
        urlElements = message_url.split("/")
        print("Extracted URL elements: ", urlElements)
        try:
            urlGuild = self.bot.get_guild(int(urlElements[-3]))
            channel = self.bot.get_partial_messageable(urlElements[-2])
            message = await channel.fetch_message(urlElements[-1])
            self._printDecodedURL(interaction.guild, urlGuild, channel, message)
            if interaction.guild != urlGuild:
                await interaction.response.send_message(f"Cannot edit a message not in this server", ephemeral=True)
            elif message.author.id != self.bot.application_id:
                await interaction.response.send_message(f"Cannot edit a message not sent by the bot itself", ephemeral=True)
            else:
                modal = EditMessage(message=message)
                await interaction.response.send_modal(modal)
        except discord.errors.Forbidden as e:
            print(e)
            await interaction.response.send_message(f"I have no access to this message", ephemeral=True)
        except Exception as e:
            #print(e)
            await interaction.response.send_message(f"Some other error happened. Check error logs.", ephemeral=True)
            raise e
        
    

    @app_commands.command(name="delete", description="Deletes a message sent by the bot. CANNOT BE UNDONE")
    @app_commands.describe(message_url="The link to the message")
    async def delete_message(self, interaction: discord.Interaction, message_url:str):
        print(f"Hello from delete-message, {message_url}")
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"Cannot delete message. User <@{interaction.user.id}> is not adminstrator.", ephemeral=True)
            return
        view = DeleteMessageView()
        await interaction.response.send_message("Are you sure you want to delete the message? All message attributes will be deleted with it", view=view, ephemeral=True)
        # Source https://stackoverflow.com/a/71693402
        timedOut = await view.wait()
        if timedOut:
            await interaction.followup.send(f"Command timed out. Message will not be deleted.", ephemeral=True)
            return
        elif view.error:
            await interaction.followup.send(f"An error occured in the interactive element. Check error logs.", ephemeral=True)
            return
        elif not view.confirm:
            await interaction.followup.send(f"Message will not be deleted.", ephemeral=True)
            return
        urlElements = message_url.split("/")
        print("Extracted URL elements: ", urlElements)
        try:
            urlGuild = self.bot.get_guild(int(urlElements[-3]))
            channel = self.bot.get_partial_messageable(urlElements[-2])
            message = await channel.fetch_message(urlElements[-1])
            self._printDecodedURL(interaction.guild, urlGuild, channel, message)
            if interaction.guild != urlGuild:
                await interaction.followup.send(f"Cannot delete a message not in this server", ephemeral=True)
            elif message.author.id != self.bot.application_id:
                await interaction.followup.send(f"Cannot delete a message not sent by the bot itself", ephemeral=True)
            else:
                if str(interaction.guild_id) not in self.bot.reactionMessages.keys():
                    print("Delete message: Guild has no reaction messages. No need to update reaction messages dictionary")
                elif str(message.id) not in self.bot.reactionMessages[str(interaction.guild_id)].keys():
                    print("Delete message: Message is not a reaction message. No need to update reaction messages dictionary")
                else:
                    print(f"Reaction message entry {urlElements[-1]}:{self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]} has been removed")
                    del self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]
                    self.bot.save_reactionMessage()
                await message.delete()
                await interaction.followup.send(f"Deleted {message_url}", ephemeral=True)
        except discord.errors.Forbidden as e:
            print(e)
            await interaction.followup.send(f"I have no access to this message", ephemeral=True)
        except Exception as e:
            #print(e)
            await interaction.followup.send(f"Some other error happened. Check error logs.", ephemeral=True)
            raise e