from typing import Any, Coroutine, List
import traceback
import discord
import discord.ui as ui


# The view is not done. Intended to provide extra functionality, where the bot can send to multiple channels at once.
"""
class SendMessageButton(ui.Button):

    def __init__(self, *, label="Send message", style=discord.ButtonStyle.blurple, disabled=True):
        super().__init__(style=style, label=label, disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
        print(self.view.channel)
        modal = SendMessage(self.view.channel)
        await interaction.response.send_modal(modal)

class SendMessageSelect(ui.Select):

    def __init__(self):
        super().__init__(placeholder="Choose channels", min_values=1, max_values=25)
        ui.Select.add_option

class SendMessageView(ui.View):

    def __init__(self, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        #channel = ui.ChannelSelect(channel_types=[discord.ChannelType.text,], placeholder="Choose channel")
        #channel = ui.ChannelSelect()
        #self.add_item(channel)
        self.channel = None
        self.button = SendMessageButton()
        self.add_item(self.button)

    @ui.select(cls=ui.ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="Choose channel", max_values=25)
    async def selectMenu(self, interaction:discord.Interaction, menu:ui.ChannelSelect):
        print(f"Chosen channels are {menu.values}")
        print(menu._underlying.options)
        self.channel = menu.values
        self.button.disabled = False
        #print(self.button)
        #await interaction.response.defer()
        await interaction.response.edit_message(view=self)

    #@ui.button(label="Edit message", style=discord.ButtonStyle.grey, custom_id="WriteMessageButton", disabled=True)
    #async def buttonActivate(self, interaction:discord.Interaction, button:ui.Button):
    #    print("Button pressed")
    #    button.style = discord.ButtonStyle.green
    #    await interaction.response.send_modal(SendMessage(self.channel))
"""



class SendMessage(ui.Modal, title="Message Send"):

    #message = ui.TextInput(label="Message to send", style=discord.TextStyle.long, placeholder="Hello there.")

    def __init__(self, channels:discord.abc.GuildChannel) -> None:
        super().__init__()
        self.channels = channels
        self.message = ui.TextInput(label="Message to send", style=discord.TextStyle.long, required=True)
        self.add_item(self.message)
        

    async def on_submit(self, interaction: discord.Interaction) -> None:
        for c in self.channels:
            #print(c)
            if isinstance(c, discord.app_commands.AppCommandChannel):
                await c.resolve().send(self.message.value)
            else:
                await c.send(self.message.value)
        print(f"Messages sent:\n{self.message.value}")
        await interaction.response.send_message("Message sent", ephemeral=True)
    
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("An error occured. Check logs", ephemeral=True)
        raise error



class EditMessage(ui.Modal):

    def __init__(self, *, message:discord.Message) -> None:
        super().__init__(title="Message Edit")
        self.message = message
        self.oldMessage = self.message.content
        self.item = ui.TextInput(label="Edit message", default=self.oldMessage, style=discord.TextStyle.long, required=True)
        self.add_item(self.item)
        

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.message.edit(content=self.item.value)
        print(f"Message edited from:\n{self.oldMessage}\n\nto\n\n{self.item.value}")
        await interaction.response.send_message("Message edited", ephemeral=True)
    
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("An error occured. Check logs")
        raise error
    
class DeleteMessage(ui.Modal):

    def __init__(self):
        super().__init__(title="Confirm Deletion")
        self.item = ui.TextInput(label="Type DELETE to confirm message deletion", placeholder="RETAIN", style=discord.TextStyle.short, required=True, min_length=6, max_length=6)

    def on_submit(self, interaction: discord.Interaction) -> Coroutine[Any, Any, None]:
        pass
    

class DeleteMessageView(ui.View):

    def __init__(self):
        super().__init__(timeout=60)
        self.error = False
        self.confirm = False

    # Source https://stackoverflow.com/a/71693402
    @ui.button(label="NO!!", style=discord.ButtonStyle.red, emoji="⚠️")
    async def buttonDeny(self, interaction:discord.Interaction, button:ui.Button):
        #print(interaction)
        #print(interaction.message)
        #print(interaction.data)
        #print(self.interaction)
        self.confirm = False
        await interaction.response.edit_message(content="Done",view=None)
        self.stop()

    @ui.button(label="Yes", style=discord.ButtonStyle.green, emoji="✅")
    async def buttonConfirm(self, interaction:discord.Interaction, button:ui.Button):
        self.confirm = True
        await interaction.response.edit_message(content="Done",view=None)
        self.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: ui.Item[Any]) -> None:
        await interaction.response.edit_message(content="Error!",view=None)
        self.error = True
        print(traceback.format_exc())
        self.stop()

    