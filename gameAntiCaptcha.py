from typing import Any, Coroutine, List
import traceback
import discord
import os
import discord.ui as ui
import numpy as np
import matplotlib.pyplot as plt
from discord import app_commands
from discord.ext import commands
from pathlib import Path

# TODO: Put a grid that shows X=0 and Y=0 in case the plot goes into the minus
# TODO: Not everyone knows what a slope and an intercept is. Explain in embed.

class RegressionView(ui.View):

    class ClassModal(ui.Modal, title="Message Send"):

        #message = ui.TextInput(label="Message to send", style=discord.TextStyle.long, placeholder="Hello there.")

        def __init__(self, x, y) -> None:
            super().__init__()
            self.slope = ui.TextInput(label="Estimated slope", style=discord.TextStyle.short, required=True)
            self.intercept = ui.TextInput(label="Estimated Y-intercept", style=discord.TextStyle.short, required=True)
            self.add_item(self.slope)
            self.add_item(self.intercept)
            self.x = x
            self.y = y
            self.databaseFolder = "databaseAntiCaptcha"
        
        # Source https://stackoverflow.com/a/6148315
        def resultPlot(self, x, y, predCoef, userID):
            coef = np.polyfit(x,y,1)
            poly1d_fn = np.poly1d(coef)
            poly1d_fn2 = np.poly1d(predCoef)
            Fig, ax = plt.subplots()
            ax.scatter(x, y)
            if coef[0] == 0:
                points = np.linspace(0,10)
            else:
                points = np.linspace(min(0, np.min(x)),max((max(10, np.max(x))-coef[1])/coef[0], (min(0, np.min(x))-coef[1])/coef[0]))
            if predCoef[0] == 0:
                points2 = np.linspace(0, 10)
            else:
                points2 = np.linspace(min(0, np.min(x)),max((max(10, np.max(x))-predCoef[1])/predCoef[0], (min(0, np.min(x))-predCoef[1])/predCoef[0]))
            ax.plot(points, poly1d_fn(points), linestyle="--", color="k", label="Robot Prediction")
            ax.plot(points2, poly1d_fn2(points2), linestyle="--", color="tab:green", label="Your Prediction")
            ax.set_title(f"Your function: {predCoef[0]:.3f}x+{predCoef[1]:.3f}\nRobot's function: {coef[0]:.3f}x+{coef[1]:.3f}")
            ax.set_xlim(min(0, np.min(x)), max(10, np.max(x)))
            ax.set_ylim(min(0, np.min(x)), max(10, np.max(x)))
            ax.legend()
            Fig.savefig(f"{self.databaseFolder}/tempPlot{userID}.png", bbox_inches="tight", dpi=300)
            robotError = np.sqrt(np.sum((y-poly1d_fn(x))**2))
            userError = np.sqrt(np.sum((y-poly1d_fn2(x))**2))
            return robotError, userError, coef

        async def on_submit(self, interaction: discord.Interaction) -> None:
            print(f"Submitted results:\n\tSlope: {self.slope}\n\tIntercept: {self.intercept}")
            robotError, userError, correctCoef = self.resultPlot(self.x, self.y, (float(self.slope.value), float(self.intercept.value)), interaction.user.id)
            plotFilename = f"{self.databaseFolder}/tempPlot{interaction.user.id}.png"
            plot = discord.File(plotFilename, filename=f"tempPlot{interaction.user.id}.png")
            embed = discord.Embed(title="Anti-Captcha Regression", description=f"<@{interaction.user.id}> was {userError-robotError:.3f} MSE off the robot prediction!")
            embed.set_image(url=f"attachment://tempPlot{interaction.user.id}.png")
            await interaction.response.send_message(embed=embed, file=plot, ephemeral=False)
            if os.path.exists(plotFilename):
                os.remove(plotFilename)
            #await interaction.response.send_message("Message sent", ephemeral=True)
        
        async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
            if isinstance(error, ValueError):
                print("Value error in anti-captcha regression modal.")
                await interaction.response.send_message("Please enter a number")
            else:
                await interaction.response.send_message("An error occured. Check logs")
                raise error

    def __init__(self, x, y):
        super().__init__(timeout=180)
        self.error = False
        self.modal = self.ClassModal(x, y)

    # Source https://stackoverflow.com/a/71693402
    @ui.button(label="Submit", style=discord.ButtonStyle.green)
    async def buttonConfirm(self, interaction:discord.Interaction, button:ui.Button):
        self.confirm = True
        
        await interaction.response.send_modal(self.modal)
        #await interaction.response.edit_message(content="Done",view=None)
        await self.modal.wait()
        self.stop()


    async def on_error(self, interaction: discord.Interaction, error: Exception, item: ui.Item[Any]) -> None:
        await interaction.response.edit_message(content="Error!",view=None)
        self.error = True
        print(traceback.format_exc())
        self.stop()

class antiCaptchaCog(commands.GroupCog, name="anti-captcha"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.databaseFolder = "databaseAntiCaptcha"
        Path(self.databaseFolder).mkdir(parents=True, exist_ok=True)
        super().__init__()  # this is now required for GroupCog.
    
    def createPlot(self, userID, difficulty):
        RNG = np.random.default_rng()
        numPoints = 28 - 3*difficulty
        slope = RNG.uniform(-difficulty, difficulty)
        intercept = RNG.uniform(0, 5) + np.abs(slope)
        print(f"Slope: {slope}")
        print(f"Intercept: {intercept}")
        x = RNG.uniform(0, 10, numPoints)
        if slope>0:
            maxAllowedX = (10 - intercept)/slope
        elif slope<0:
            maxAllowedX = 0-intercept/slope
        else:
            maxAllowedX = 10
        x = x*maxAllowedX/10
        y = slope*x + intercept
        tildeX = x + RNG.uniform(-0.6*difficulty, 0.6*difficulty, numPoints)
        Fig, ax = plt.subplots()
        ax.scatter(tildeX,y)
        ax.set_xlim(min(0, np.min(tildeX)), max(10, np.max(tildeX)))
        ax.set_ylim(min(0, np.min(tildeX)), max(10, np.max(tildeX)))
        Fig.savefig(f"{self.databaseFolder}/tempPlot{userID}.png", bbox_inches="tight", dpi=300)
        return tildeX, y

    @app_commands.command(name="play", description="Play the Anti-Captcha game")
    @app_commands.describe(difficulty="The link to the message")
    @app_commands.choices(difficulty=[app_commands.Choice(name=f"{i}", value=i) for i in range(6)])
    #@commands.has_guild_permissions(manage_roles=True, ban_members=True, administrator=True) # Check not working
    async def play(self, interaction: discord.Interaction, difficulty:int) -> None:
        print(f"Welcome from anti-captcha play. Difficulty: {difficulty}")
        print(f"User: {interaction.user}")
        x, y = self.createPlot(interaction.user.id, difficulty=difficulty)
        # Source https://stackoverflow.com/a/65527000
        plotFilename = f"{self.databaseFolder}/tempPlot{interaction.user.id}.png"
        plot = discord.File(plotFilename, filename=f"tempPlot{interaction.user.id}.png")
        view = RegressionView(x, y)
        embed = discord.Embed(title="Anti-Captcha", description="Are you a robot? Please prove it!!!\nEstimate the function of the straight line by entering the slope of the line and its Y-intercept.")
        embed.set_image(url=f"attachment://tempPlot{interaction.user.id}.png")
        await interaction.response.send_message(file=plot,embed=embed, view=view, ephemeral=True)
        if os.path.exists(plotFilename):
            os.remove(plotFilename)
        # Source https://stackoverflow.com/a/71693402
        timedOut = await view.wait()
        if timedOut:
            await interaction.followup.send(f"Command timed out. Message will not be deleted.", ephemeral=True)
            return
        elif view.error:
            await interaction.followup.send(f"An error occured in the interactive element. Check error logs.", ephemeral=True)
            return