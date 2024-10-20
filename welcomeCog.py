import discord
from discord import app_commands
from discord.ext import commands

class WelcomeCog(commands.GroupCog, name="welcome"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()  # this is now required for GroupCog.

    @app_commands.command(name="set-category", description="Sets the category to create welcome channels under")
    @app_commands.describe(category_id="The category to make welcome channels in")
    async def set_category(self, interaction: discord.Interaction, category_id: str):
        print(f"Hello from set-category, {category_id}")
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"Cannot set welcome category. User <@{interaction.user.id}> is not adminstrator.", ephemeral=True)
            return
        try:
            # Make guild entry if it is not registered in the welcome settings dictionary
            guildWelcomeSettings = self.bot.welcomeSettings.get(str(interaction.guild_id), None)
            if not int(category_id) in [i.id for i in interaction.guild.categories]:
                await interaction.response.send_message("The provided category id is not for a category in this server", ephemeral=True)
                return
            elif guildWelcomeSettings is None:
                # Also checks if we're still in the guild and it's cached.
                self.bot.welcomeSettings[str(interaction.guild_id)] = {}
                guildWelcomeSettings = self.bot.welcomeSettings.get(str(interaction.guild_id), None)
                guildWelcomeSettings["Enabled"] = True
                guildWelcomeSettings["Message"] = ""
            guildWelcomeSettings["Category"] = category_id
            self.bot.save_welcomeSettings()
            await interaction.response.send_message(f"Category {interaction.guild.get_channel(int(category_id))} has been set as welcome category", ephemeral=True)
        except ValueError as e:
            await interaction.response.send_message(f"Passed category ID is of wrong format. Did you make sure to pass an ID?", ephemeral=True)
            raise e
        except Exception as e:
            #print(e)
            await interaction.response.send_message(f"Some other error happened. Check error logs.", ephemeral=True)
            raise e
        
    @app_commands.command(name="set-message", description="Set the welcome message to be sent in welcome channels")
    @app_commands.describe(message="Message to be sent")
    async def set_message(self, interaction: discord.Interaction, message: str):
        print(f"Hello from set-message, {message}")
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"Cannot set welcome message. User <@{interaction.user.id}> is not adminstrator.", ephemeral=True)
            return
        try:
            # Make guild entry if it is not registered in the welcome settings dictionary
            guildWelcomeSettings = self.bot.welcomeSettings.get(str(interaction.guild_id), None)
            if guildWelcomeSettings is None:
                await interaction.response.send_message("Server doesn't have a welcome category set yet. Use welcom set-category command first.")
            else:
                guildWelcomeSettings["Message"] = message
                self.bot.save_welcomeSettings()
                await interaction.response.send_message(f"Welcome message has been set to:\n\n\"{message}\"", ephemeral=True)
        except Exception as e:
            #print(e)
            await interaction.response.send_message(f"Some other error happened. Check error logs.", ephemeral=True)
            raise e
        
    #@app_commands.command(name="print-categories", description="Print list of categories in tty")
    #async def print_categories(self, interaction: discord.Interaction):
    #    print("Hello from print-categories")
    #    print(interaction.guild.categories)
    #    #for i in interaction.guild.categories:
    #    #    print(i)
    #    print([i.id for i in interaction.guild.categories])
    #    print(type(interaction.guild.categories[0].id))
    #    await interaction.response.send_message("Check output in terminal", ephemeral=True)