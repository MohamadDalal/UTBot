import discord
from discord import app_commands
from discord.ext import commands

class roleMessage(commands.GroupCog, name="roles"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()  # this is now required for GroupCog.
    
    @app_commands.command(name="assign-message", description="Assign a message as role picker message")
    @app_commands.describe(message_url="The link to the message")
    #@commands.has_guild_permissions(manage_roles=True, ban_members=True, administrator=True) # Check not working
    async def assign_message(self, interaction: discord.Interaction, message_url:str) -> None:
        print(f"Hello from assign-message, {message_url}")
        # https://stackoverflow.com/a/48613050 source for this if statement
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(f"Cannot assign message as role message. User <@{interaction.user.id}> does not have permission to manage roles.", ephemeral=True)
            return
        urlElements = message_url.split("/")
        print(urlElements)
        #message = interaction.channel.fetch_message(int(message_id))
        try:
            channel = self.bot.get_partial_messageable(urlElements[-2])
            message = await channel.fetch_message(urlElements[-1])
            print(channel)
            print(message)
            if str(message.id) in self.bot.reactionMessages.keys():
                await interaction.response.send_message(f"Message {message_url} already assigned as a reaction message of type {self.bot.reactionMessages[str(message.id)]['Type']}.", ephemeral=True)
            else:
                self.bot.reactionMessages[str(message.id)] = {"Type": "Role Message", "Roles": {}}
                self.bot.save_reactionMessage()
                await interaction.response.send_message(f"Assigned message {message_url} as role message", ephemeral=True)
        except discord.errors.Forbidden as e:
            print(e)
            await interaction.response.send_message(f"I have no access to this message {message_url}", ephemeral=True)
        except Exception as e:
            print(e)
            await interaction.response.send_message(f"Message with link {message_url} not found or is not a message", ephemeral=True)

    # https://stackoverflow.com/a/48613050 for error management and permission checking
    #@assign_message.error
    #async def assing_message_error(self, interaction:discord.Interaction, error):
    #    if isinstance(error, commands.MissingPermissions):
    #        print(error)
    #        text = "Sorry {}, you do not have permissions to do that!".format(interaction.message.author)
    #        await interaction.response(text, ephemeral=True)

    @app_commands.command(name="unassign-message", description="Remove assignment a message as role picker message. THIS CANNOT BE UNDONE")
    @app_commands.describe(message_url="The link to the message")
    async def unassign_message(self, interaction: discord.Interaction, message_url:str) -> None:
        print(f"Hello from unassign-message, {message_url}")
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(f"Cannot unassign message from being a role message. User <@{interaction.user.id}> does not have permission to manage roles.", ephemeral=True)
            return
        urlElements = message_url.split("/")
        print(urlElements)
        try:
            channel = self.bot.get_partial_messageable(urlElements[-2])
            message = await channel.fetch_message(urlElements[-1])
            print(channel)
            print(message)
            if str(message.id) not in self.bot.reactionMessages.keys():
                await interaction.response.send_message(f"Message {message_url} is not assigned as a reaction message.", ephemeral=True)
            elif self.bot.reactionMessages[str(message.id)]["Type"] != "Role Message":
                await interaction.response.send_message(f"Message {message_url} is assigned as a {self.bot.reactionMessages[str(message.id)]['Type']}. You need to unassign it using its respective command.", ephemeral=True)
            else:
                del self.bot.reactionMessages[str(message.id)]
                self.bot.save_reactionMessage()
                await interaction.response.send_message(f"Removed assignment of message {message_url} as role message", ephemeral=True)
        except discord.errors.Forbidden as e:
            print(e)
            await interaction.response.send_message(f"I have no access to this message {message_url}", ephemeral=True)
        except Exception as e:
            print(e)
            await interaction.response.send_message(f"Message with link {message_url} not found or is not a message", ephemeral=True)

        
    
    @app_commands.command(name="add-role", description="Make a reaction assign a role on a message.")
    @app_commands.describe(message_url="The link to the message")
    @app_commands.describe(reaction="The reaction to assign a role to")
    @app_commands.describe(role_id="The ID of the role to be assigned")
    async def add_role(self, interaction: discord.Interaction, message_url:str, reaction:str, role_id:str) -> None:
        print(f"Hello from add-role, {message_url}, {reaction}, {role_id}")
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(f"Cannot add role to a role message. User <@{interaction.user.id}> does not have permission to manage roles.", ephemeral=True)
            return
        urlElements = message_url.split("/")
        print(urlElements)
        #message = interaction.channel.fetch_message(int(message_id))
        try:
            channel = self.bot.get_partial_messageable(urlElements[-2])
            message = await channel.fetch_message(urlElements[-1])
            print(channel)
            print(message)
            if str(message.id) not in self.bot.reactionMessages.keys():
                await interaction.response.send_message(f"Message {message_url} is not assigned as a reaction message. Use assign-message command first.", ephemeral=True)
            elif self.bot.reactionMessages[str(message.id)]["Type"] != "Role Message":
                await interaction.response.send_message(f"Message {message_url} is assigned as a {self.bot.reactionMessages[str(message.id)]['Type']}. You need to unassign at and then reassign it as a role message.", ephemeral=True)
            else:
                # Check if role_ID is made of numbers only later
                self.bot.reactionMessages[str(message.id)]["Roles"][reaction] = role_id
                self.bot.save_reactionMessage()
                await message.add_reaction(reaction)
                await interaction.response.send_message(f"Assigning {reaction} to the role <@&{role_id}>", ephemeral=True)
        except discord.errors.Forbidden as e:
            print(e)
            await interaction.response.send_message(f"I have no access to this message {message_url}", ephemeral=True)
        except Exception as e:
            print(e)
            await interaction.response.send_message(f"Message with link {message_url} not found or is not a message", ephemeral=True)
        
    @app_commands.command(name="remove-role", description="Make a reaction stop giving roles on a certain message.")
    @app_commands.describe(message_url="The link to the message")
    @app_commands.describe(reaction="The reaction to remove assignment from")
    async def remove_role(self, interaction: discord.Interaction, message_url:str, reaction:str) -> None:
        print(f"Hello from remove-role, {message_url}, {reaction}")
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(f"Cannot remove role reaction as role message. User <@{interaction.user.id}> does not have permission to manage roles.", ephemeral=True)
            return
        urlElements = message_url.split("/")
        print(urlElements)
        #message = interaction.channel.fetch_message(int(message_id))
        try:
            channel = self.bot.get_partial_messageable(urlElements[-2])
            message = await channel.fetch_message(urlElements[-1])
            print(channel)
            print(message)
            if str(message.id) not in self.bot.reactionMessages.keys():
                await interaction.response.send_message(f"Message {message_url} is not assigned as a reaction message. Use assign-message command first.", ephemeral=True)
            elif self.bot.reactionMessages[str(message.id)]["Type"] != "Role Message":
                await interaction.response.send_message(f"Message {message_url} is assigned as a {self.bot.reactionMessages[str(message.id)]['Type']}. You need to unassign at and then reassign it as a role message.", ephemeral=True)
            elif reaction not in self.bot.reactionMessages[str(message.id)]["Roles"].keys():
                await interaction.response.send_message(f"Message {message_url} doesn't have {reaction} assigned to any roles.", ephemeral=True)
            else:
                # Check if role_ID is made of numbers only later
                oldRole = self.bot.reactionMessages[str(message.id)]["Roles"][reaction]
                self.bot.save_reactionMessage()
                del self.bot.reactionMessages[str(message.id)]["Roles"][reaction]
                await message.remove_reaction(reaction, interaction.guild.get_member(self.bot.application_id))
                await interaction.response.send_message(f"Removed assignment of {reaction} to its role <@&{oldRole}>", ephemeral=True)
        except discord.errors.Forbidden as e:
            print(e)
            await interaction.response.send_message(f"I have no access to this message {message_url}", ephemeral=True)
        except Exception as e:
            print(e)
            await interaction.response.send_message(f"Message with link {message_url} not found or is not a message", ephemeral=True)
