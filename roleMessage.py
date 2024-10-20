import discord
from discord import app_commands
from discord.ext import commands

class RoleMessage(commands.GroupCog, name="roles"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()  # this is now required for GroupCog.
    
    def _printDecodedURL(self, originGuild, urlGuild, channel, message):
        print(f"Origin guild:\t{originGuild}")
        print(f"Message guild:\t{urlGuild}")
        print(f"Message channel:\t{channel}")
        print(f"Message:\t\t{message}")
    
    @app_commands.command(name="assign-message", description="Assign a message as role picker message")
    @app_commands.describe(message_url="The link to the message")
    #@commands.has_guild_permissions(manage_roles=True, ban_members=True, administrator=True) # Check not working
    async def assign_message(self, interaction: discord.Interaction, message_url:str) -> None:
        print(f"Hello from assign-message, {message_url}")
        # https://stackoverflow.com/a/48613050 source for this if statement
        #if not interaction.user.guild_permissions.manage_roles:
        #    await interaction.response.send_message(f"Cannot assign message as role message. User <@{interaction.user.id}> does not have permission to manage roles.", ephemeral=True)
        #    return
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"Cannot assign message as role message. User <@{interaction.user.id}> is not adminstrator.", ephemeral=True)
            return
        urlElements = message_url.split("/")
        print("Extracted URL elements: ", urlElements)
        #message = interaction.channel.fetch_message(int(message_id))
        try:
            urlGuild = self.bot.get_guild(int(urlElements[-3]))
            channel = self.bot.get_partial_messageable(urlElements[-2])
            message = await channel.fetch_message(urlElements[-1])
            self._printDecodedURL(interaction.guild, urlGuild, channel, message)
            
            if interaction.guild != urlGuild:
                await interaction.response.send_message(f"Cannot assign a message from another server", ephemeral=True)
            elif str(message.id) in self.bot.reactionMessages.get(str(interaction.guild_id), {}).keys():
                await interaction.response.send_message(f"Message {message_url} already assigned as a reaction message of type {self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]['Type']}.", ephemeral=True)
            else:
                if self.bot.reactionMessages.get(str(interaction.guild_id), None) is None:
                    self.bot.reactionMessages[str(interaction.guild_id)] = {}
                self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)] = {"Type": "Role Message", "Channel": urlElements[-2], "Roles": {}}
                self.bot.save_reactionMessage()
                await interaction.response.send_message(f"Assigned message {message_url} as role message", ephemeral=True)
        except discord.errors.Forbidden as e:
            print(e)
            await interaction.response.send_message(f"I have no access to this message {message_url}", ephemeral=True)
        except Exception as e:
            #print(e)
            await interaction.response.send_message(f"Message with link {message_url} not found or is not a message", ephemeral=True)
            raise e

    # https://stackoverflow.com/a/48613050 for error management and permission checking
    #@assign_message.error
    #async def assing_message_error(self, interaction:discord.Interaction, error):
    #    if isinstance(error, commands.MissingPermissions):
    #        print(error)
    #        text = "Sorry {}, you do not have permissions to do that!".format(interaction.message.author)
    #        await interaction.response(text, ephemeral=True)

    @app_commands.command(name="unassign-message", description="Remove assignment a message as role picker message. ASSIGNED ROLE REACTIONS CANNOT BE RESTORED!!!")
    @app_commands.describe(message_url="The link to the message")
    @app_commands.describe(confirm="Choose True to confirm your choice. Here to avoid accidents")
    async def unassign_message(self, interaction: discord.Interaction, message_url:str, confirm:bool = False) -> None:
        print(f"Hello from unassign-message, {message_url}, {confirm}")
        #if not interaction.user.guild_permissions.manage_roles:
        #    await interaction.response.send_message(f"Cannot unassign message from being a role message. User <@{interaction.user.id}> does not have permission to manage roles.", ephemeral=True)
        #    return
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"Cannot unassign message from being a role message. User <@{interaction.user.id}> is not adminstrator.", ephemeral=True)
            return
        elif not confirm:
            await interaction.response.send_message(f"The confirm option was not set to true. Are you sure you wanted to unassign message from being a role message?", ephemeral=True)
            return
        urlElements = message_url.split("/")
        print("Extracted URL elements: ", urlElements)
        try:
            urlGuild = self.bot.get_guild(int(urlElements[-3]))
            channel = self.bot.get_partial_messageable(urlElements[-2])
            message = await channel.fetch_message(urlElements[-1])
            self._printDecodedURL(interaction.guild, urlGuild, channel, message)
            if interaction.guild != urlGuild:
                await interaction.response.send_message(f"Cannot unassign a message from another server", ephemeral=True)
            elif str(interaction.guild_id) not in self.bot.reactionMessages.keys():
                await interaction.response.send_message(f"Current server does not have any messages assigned as a reaction message. Please use /roles assign-message first.", ephemeral=True)
            elif str(message.id) not in self.bot.reactionMessages[str(interaction.guild_id)].keys():
                await interaction.response.send_message(f"Message {message_url} is not assigned as a reaction message.", ephemeral=True)
            elif self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]["Type"] != "Role Message":
                await interaction.response.send_message(f"Message {message_url} is assigned as a {self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]['Type']}. You need to unassign it using its respective command.", ephemeral=True)
            else:
                del self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]
                self.bot.save_reactionMessage()
                await interaction.response.send_message(f"Removed assignment of message {message_url} as role message", ephemeral=True)
        except discord.errors.Forbidden as e:
            print(e)
            await interaction.response.send_message(f"I have no access to this message {message_url}", ephemeral=True)
        except Exception as e:
            #print(e)
            await interaction.response.send_message(f"Message with link {message_url} not found or is not a message", ephemeral=True)
            raise e

        
    
    @app_commands.command(name="add-role", description="Make a reaction assign a role on a message.")
    @app_commands.describe(message_url="The link to the message")
    @app_commands.describe(reaction="The reaction to assign a role to")
    @app_commands.describe(role_id="The ID of the role to be assigned")
    async def add_role(self, interaction: discord.Interaction, message_url:str, reaction:str, role_id:str) -> None:
        print(f"Hello from add-role, {message_url}, {reaction}, {role_id}")
        #if not interaction.user.guild_permissions.manage_roles:
        #    await interaction.response.send_message(f"Cannot add role to a role message. User <@{interaction.user.id}> does not have permission to manage roles.", ephemeral=True)
        #    return
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"Cannot add role to role message. User <@{interaction.user.id}> is not adminstrator.", ephemeral=True)
            return
        urlElements = message_url.split("/")
        print("Extracted URL elements: ", urlElements)
        #message = interaction.channel.fetch_message(int(message_id))
        try:
            urlGuild = self.bot.get_guild(int(urlElements[-3]))
            channel = self.bot.get_partial_messageable(urlElements[-2])
            message = await channel.fetch_message(urlElements[-1])
            self._printDecodedURL(interaction.guild, urlGuild, channel, message)
            if interaction.guild != urlGuild:
                await interaction.response.send_message(f"Cannot add a role reaction to a message from another server", ephemeral=True)
            elif str(interaction.guild_id) not in self.bot.reactionMessages.keys():
                await interaction.response.send_message(f"Current server does not have any messages assigned as a reaction message. Please use /roles assign-message first.", ephemeral=True)
            elif str(message.id) not in self.bot.reactionMessages[str(interaction.guild_id)].keys():
                await interaction.response.send_message(f"Message {message_url} is not assigned as a reaction message. Please use /roles assign-message first.", ephemeral=True)
            elif self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]["Type"] != "Role Message":
                await interaction.response.send_message(f"Message {message_url} is assigned as a {self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]['Type']}. You need to unassign at and then reassign it as a role message.", ephemeral=True)
            else:
                # Check if role_ID is made of numbers only (Valid role ID) later
                self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]["Roles"][reaction] = role_id
                self.bot.save_reactionMessage()
                await message.add_reaction(reaction)
                await interaction.response.send_message(f"Assigning {reaction} to the role <@&{role_id}> on message {message_url}", ephemeral=True)
        except discord.errors.Forbidden as e:
            print(e)
            await interaction.response.send_message(f"I have no access to this message {message_url}", ephemeral=True)
        except Exception as e:
            #print(e)
            await interaction.response.send_message(f"Message with link {message_url} not found or is not a message", ephemeral=True)
            raise e
        
    @app_commands.command(name="remove-role", description="Make a reaction stop giving roles on a certain message.")
    @app_commands.describe(message_url="The link to the message")
    @app_commands.describe(reaction="The reaction to remove assignment from")
    async def remove_role(self, interaction: discord.Interaction, message_url:str, reaction:str) -> None:
        print(f"Hello from remove-role, {message_url}, {reaction}")
        #if not interaction.user.guild_permissions.manage_roles:
        #    await interaction.response.send_message(f"Cannot remove role reaction as role message. User <@{interaction.user.id}> does not have permission to manage roles.", ephemeral=True)
        #    return
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"Cannot remove role reaction as role message. User <@{interaction.user.id}> is not adminstrator.", ephemeral=True)
            return
        urlElements = message_url.split("/")
        print("Extracted URL elements: ", urlElements)
        #message = interaction.channel.fetch_message(int(message_id))
        try:
            urlGuild = self.bot.get_guild(int(urlElements[-3]))
            channel = self.bot.get_partial_messageable(urlElements[-2])
            message = await channel.fetch_message(urlElements[-1])
            self._printDecodedURL(interaction.guild, urlGuild, channel, message)
            if interaction.guild != urlGuild:
                await interaction.response.send_message(f"Cannot remove role reaction from a message not in this server", ephemeral=True)
            elif str(interaction.guild_id) not in self.bot.reactionMessages.keys():
                await interaction.response.send_message(f"Current server does not have any messages assigned as a reaction message. Please use /roles assign-message first.", ephemeral=True)
            elif str(message.id) not in self.bot.reactionMessages[str(interaction.guild_id)].keys():
                await interaction.response.send_message(f"Message {message_url} is not assigned as a reaction message. Use assign-message command first.", ephemeral=True)
            elif self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]["Type"] != "Role Message":
                await interaction.response.send_message(f"Message {message_url} is assigned as a {self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]['Type']}. You need to unassign at and then reassign it as a role message.", ephemeral=True)
            elif reaction not in self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]["Roles"].keys():
                await interaction.response.send_message(f"Message {message_url} doesn't have {reaction} assigned to any roles.", ephemeral=True)
            else:
                # Check if role_ID is made of numbers only later
                oldRole = self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]["Roles"][reaction]
                del self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]["Roles"][reaction]
                self.bot.save_reactionMessage()
                await message.remove_reaction(reaction, interaction.guild.get_member(self.bot.application_id))
                await interaction.response.send_message(f"Removed assignment of {reaction} to its role <@&{oldRole}> on message {message_url}", ephemeral=True)
        except discord.errors.Forbidden as e:
            print(e)
            await interaction.response.send_message(f"I have no access to this message {message_url}", ephemeral=True)
        except Exception as e:
            #print(repr(e))
            await interaction.response.send_message(f"Message with link {message_url} not found or is not a message", ephemeral=True)
            raise e

    
    @app_commands.command(name="list-messages", description="List all messages assigned as role reaction messages in this server")
    async def list_messages(self, interaction: discord.Interaction) -> None:
        print(f"Hello from list-messages")
        #if not interaction.user.guild_permissions.manage_roles:
        #    await interaction.response.send_message(f"Cannot list role reaction messages. User <@{interaction.user.id}> does not have permission to manage roles.", ephemeral=True)
        #    return
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"Cannot list role reaction messages. User <@{interaction.user.id}> is not adminstrator.", ephemeral=True)
            return
        elif str(interaction.guild_id) not in self.bot.reactionMessages.keys():
            await interaction.response.send_message(f"Current server does not have any messages assigned as a reaction message. Please use /roles assign-message first.", ephemeral=True)
            return
        else:
            reactionMessages = self.bot.reactionMessages[str(interaction.guild_id)]
            urlList = []
            for val in reactionMessages.keys():
                if reactionMessages[val]["Type"] == "Role Message":
                    urlList.append(f'https://discord.com/channels/{interaction.guild_id}/{reactionMessages[val]["Channel"]}/{val}')
            if len(urlList) == 0:
                returnMD = "Server has no reaction role messages currently"
            else:
                returnMD = "The following messages are reaction messages:\n"
                for i in urlList:
                    returnMD += f"- {i}\n"
            await interaction.response.send_message(returnMD, ephemeral=True)

    @app_commands.command(name="list-roles", description="List all messages assigned as role reaction messages in this server")
    async def list_roles(self, interaction: discord.Interaction, message_url:str) -> None:
        print(f"Hello from list-roles, {message_url}")
        #if not interaction.user.guild_permissions.manage_roles:
        #    await interaction.response.send_message(f"Cannot list role reaction messages. User <@{interaction.user.id}> does not have permission to manage roles.", ephemeral=True)
        #    return
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"Cannot display role reactions on {message_url}. User <@{interaction.user.id}> is not adminstrator.", ephemeral=True)
            return
        urlElements = message_url.split("/")
        print("Extracted URL elements: ", urlElements)
        try:
            urlGuild = self.bot.get_guild(int(urlElements[-3]))
            channel = self.bot.get_partial_messageable(urlElements[-2])
            message = await channel.fetch_message(urlElements[-1])
            self._printDecodedURL(interaction.guild, urlGuild, channel, message)
            if str(interaction.guild_id) not in self.bot.reactionMessages.keys():
                await interaction.response.send_message(f"Current server does not have any messages assigned as a reaction message. Please use /roles assign-message first.", ephemeral=True)
                return
            elif str(message.id) not in self.bot.reactionMessages[str(interaction.guild_id)].keys():
                await interaction.response.send_message(f"Message {message_url} is not assigned as a reaction message.", ephemeral=True)
            elif self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]["Type"] != "Role Message":
                await interaction.response.send_message(f"Message {message_url} is assigned as a {self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]['Type']} and not as a Role Message.", ephemeral=True)
            else:
                rolesInMessage = self.bot.reactionMessages[str(interaction.guild_id)][str(message.id)]["Roles"]
                if len(rolesInMessage.keys()) == 0:
                    returnMD = f"{message_url} does not have any reactions assigned to any roles."
                else:
                    returnMD = f"The following are the reaction and role pairs on {message_url} :\n"
                    for i in rolesInMessage.keys():
                        returnMD += f"- {i}: <@{rolesInMessage[i]}>\n"
                await interaction.response.send_message(returnMD, ephemeral=True)
        except discord.errors.Forbidden as e:
            print(e)
            await interaction.response.send_message(f"I have no access to this message {message_url}", ephemeral=True)
        except Exception as e:
            #print(e)
            await interaction.response.send_message(f"Message with link {message_url} not found or is not a message", ephemeral=True)
            raise e

        
