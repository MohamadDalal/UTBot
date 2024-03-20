import discord
from discord import app_commands
from discord.ext import commands

class SlashCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_echo(intercation:discord.Interaction):
        print("Check works")
        return False

    @app_commands.command(description="Repeats what you say")
    #@commands.has_permissions(administrator=True)
    @commands.check(check_echo)
    async def echo(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message)

    @app_commands.command(description="Adds two numbers")
    async def add(self, interaction: discord.Interaction, first_value: float, second_value: float):
        result = first_value + second_value
        await interaction.response.send_message(f"The sum of {first_value} and {second_value} is {result}")

    @app_commands.command(description="Subtracts two numbers")
    async def subtract(self, interaction: discord.Interaction, num1: float, num2: float):
        result = num1 - num2
        await interaction.response.send_message(f"The difference of {num1} and {num2} is {result}")

    @app_commands.command(description="Multiplies two numbers")
    async def multiply(self, interaction: discord.Interaction, num1: float, num2: float):
        result = num1 * num2
        await interaction.response.send_message(f"The product of {num1} and {num2} is {result}")

    @app_commands.command(description="Divides two numbers")
    async def divide(self, interaction: discord.Interaction, num1: float, num2: float):
        if num2 == 0:
            await interaction.response.send_message("Cannot divide by zero")
            return
        result = num1 / num2
        await interaction.response.send_message(f"The division of {num1} by {num2} is {result}")

    @app_commands.command(name="message-react", description="React to a message. Made for testing.")
    @app_commands.describe(message_url="The ID of the message")
    @app_commands.describe(reaction="The reaction to react with")
    async def message_react(self, interaction: discord.Interaction, message_url:str, reaction:str) -> None:
        print(f"Hello from message_react, {message_url}, {reaction}")
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"This puny <@{interaction.user.id}> really thought he could make my bot react. ", ephemeral=True)
            return
        urlElements = message_url.split("/")
        print(urlElements)
        #message = interaction.channel.fetch_message(int(message_id))
        channel = self.bot.get_partial_messageable(urlElements[-2])
        message = await channel.fetch_message(urlElements[-1])
        print(channel)
        print(message)
        await message.add_reaction(reaction)
        await interaction.response.send_message(f"Reacted to {message_url} with {reaction}", ephemeral=True)
    
    @app_commands.command(name="message-unreact", description="Unreact to a message. Made for testing.")
    @app_commands.describe(message_url="The ID of the message")
    @app_commands.describe(reaction="The reaction to remove")
    async def message_unreact(self, interaction: discord.Interaction, message_url:str, reaction:str) -> None:
        print(f"Hello from message_unreact, {message_url}, {reaction}")
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"This puny <@{interaction.user.id}> really thought he could make my bot remove a reaction. ", ephemeral=True)
            return
        urlElements = message_url.split("/")
        print(urlElements)
        #message = interaction.channel.fetch_message(int(message_id))
        channel = self.bot.get_partial_messageable(urlElements[-2])
        message = await channel.fetch_message(urlElements[-1])
        print(channel)
        print(message)
        await message.remove_reaction(reaction, interaction.guild.get_member(self.bot.application_id))
        await interaction.response.send_message(f"Removed reaction {reaction} from {message_url}", ephemeral=True)