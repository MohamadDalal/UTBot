import discord
import json
import os
from datetime import datetime
from pathlib import Path
from discord import app_commands
from discord.ext import commands

class TryoutCog(commands.GroupCog, name="tryout"):

    # TODO: See if we can somehow transfer functionality to another function. I think this is easily done by just returning the function call to that other function?

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()
        self.cog_version = "Beta 1"
        Path("tryoutData/logs").mkdir(parents=True, exist_ok=True)
        if not os.path.exists("tryoutData/tryoutRoles.json"):
            with open("tryoutData/tryoutRoles.json", "w+") as f:
                json.dump({"Guilds": {}}, f, indent=4)
        with open("tryoutData/tryoutRoles.json", "r") as f:
            self.logs = json.load(f)
        

    def check_permissions(self, interaction_user:discord.Member, guild_id:str):
        if interaction_user.guild_permissions.administrator:
            return True, True
        allowed = False
        admin = False
        discord_roles = interaction_user.roles
        discord_roles = [str(r.id) for r in discord_roles]
        manager_role = self.logs["Guilds"][guild_id]["Manager Role"]
        admin_roles = self.logs["Guilds"][guild_id]["Admin Roles"]
        if manager_role in discord_roles:
            allowed = True
        for r in admin_roles:
            if r in discord_roles:
                allowed = True
                admin = True
                break
        return allowed, admin
    
    async def no_guild_logs(self, interaction: discord.Interaction):
        self.logs["Guilds"][str(interaction.guild_id)] = {"Tryout Role": "", "Manager Role": "", "Admin Roles": [], "Tryouts": {}}
        Path(f"tryoutData/logs/{interaction.guild_id}").mkdir(parents=True, exist_ok=True)
        self.save_tryout_logs()
        print(f"Created tryout entry for guild {interaction.guild.name} with ID {interaction.guild_id}")
        await interaction.response.send_message("This is the first time a tryout command was used on this server. You will need to set tryout and manager roles to use tryout commands.", ephemeral=True)

    def sanity_check_roles(self, guild: discord.Guild):
        guild_logs = self.logs["Guilds"].get(str(guild.id))
        if guild_logs is None:
            return False, "This server has not been initialized."
        guild_roles = [str(r.id) for r in guild.roles]
        if not guild_logs["Tryout Role"] in guild_roles:
            return False, f"Tryout role <@&{guild_logs["Tryout Role"]}> is not one of the roles vailable in this guild. Please re-set tryout role."
        elif not guild_logs["Manager Role"] in guild_roles:
            return False, f"Manager role <@&{guild_logs["Manager Role"]}> is not one of the roles vailable in this guild. Please re-set manager role."
        else:
            return True, ""

    def write_log(self, log_file, message):
        with open(log_file, "a+") as f:
            f.write(f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {message}\n")

    def save_tryout_logs(self):
        with open("tryoutData/tryoutRoles.json", "w") as f:
            json.dump(self.logs, f, indent=4)

    @app_commands.command(name="assign_tryout", description="Assign tryout role to a user and set yourself as their manager.")
    @app_commands.describe(user="User you want to assignt tryout to")
    async def assign_tryout(self, interaction: discord.Interaction, user: discord.Member):
        print(f"Hello from assign-tryout, {interaction.user.name}, {user.name}")
        if not str(interaction.guild_id) in self.logs["Guilds"].keys(): 
            return await self.no_guild_logs(interaction)
        success, message = self.sanity_check_roles(interaction.guild)
        if not success:
            await interaction.response.send_message(message, ephemeral=True)
            return
        allowed, admin = self.check_permissions(interaction.user, str(interaction.guild_id))
        if not allowed:
            await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
            return
        guild_logs = self.logs["Guilds"][str(interaction.guild_id)]
        user_logs = guild_logs["Tryouts"].get(str(user.id), {})
        if user_logs.get("Tryout", False):
            await interaction.response.send_message(f"User {user.display_name} already has tryout assigned", ephemeral=True)
            return
        # if not admin:
        #     if interaction.user.id != user_logs["Manager"]:
        #         await interaction.response.send_message(f"User {user.display_name} is not under your name", ephemeral=True)
        #         return
        user_logs["Tryout"] = True
        user_logs["Manager"] = str(interaction.user.id)
        user_logs["Log"] = f"tryoutData/logs/{interaction.guild_id}/{user.id}.log"
        guild = self.bot.get_guild(interaction.guild_id)
        role = guild.get_role(int(guild_logs["Tryout Role"]))
        await user.add_roles(role)
        self.logs["Guilds"][str(interaction.guild_id)]["Tryouts"][str(user.id)] = user_logs
        self.save_tryout_logs()
        await interaction.response.send_message(f"User {user.display_name} has been given a tryout role", ephemeral=True)
        self.write_log(user_logs["Log"], f"Tryout role assigned to {user.name} by {interaction.user.name}")

    # def _unassign_tryout(self, interaction, user_logs, user, role_id):
    #     user_logs["Tryout"] = False
    #     user_logs["Manager"] = ""
    #     guild = self.bot.get_guild(interaction.guild_id)
    #     role = guild.get_role(int(self.tryout_role))
    #     await user.remove_roles(role)
    #     await interaction.response.send_message(f"User {user.display_name} has been given a tryout role", ephemeral=True)
    #     self.write_log(user_logs["Log"], f"Tryout role unassigned from {user.name} by {interaction.user.name}")
    #     self.logs["Guilds"][str(interaction.guild_id)]["Tryouts"][user.id] = user_logs
    #     self.save_tryout_logs()

    @app_commands.command(name="unassign_tryout", description="Unassign tryout role from a user you are the manager of.")
    @app_commands.describe(user="User you want to remove tryout from")
    async def unassign_tryout(self, interaction: discord.Interaction, user: discord.Member):
        print(f"Hello from unassign-tryout, {interaction.user.name}, {user.name}")
        if not str(interaction.guild_id) in self.logs["Guilds"].keys(): 
            return await self.no_guild_logs(interaction)
        success, message = self.sanity_check_roles(interaction.guild)
        if not success:
            await interaction.response.send_message(message, ephemeral=True)
            return
        allowed, admin = self.check_permissions(interaction.user, str(interaction.guild_id))
        if not allowed:
            await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
            return
        guild_logs = self.logs["Guilds"][str(interaction.guild_id)]
        user_logs = guild_logs["Tryouts"].get(str(user.id), {})
        if not user_logs.get("Tryout", False):
            await interaction.response.send_message(f"User {user.display_name} does not have tryout assigned", ephemeral=True)
            return
        if not admin:
            if str(interaction.user.id) != user_logs["Manager"]:
                await interaction.response.send_message(f"User {user.display_name} is not under your name, and therefore you cannot remove their tryout role", ephemeral=True)
                return
        user_logs["Tryout"] = False
        user_logs["Manager"] = ""
        guild = self.bot.get_guild(interaction.guild_id)
        role = guild.get_role(int(guild_logs["Tryout Role"]))
        await user.remove_roles(role)
        self.logs["Guilds"][str(interaction.guild_id)]["Tryouts"][str(user.id)] = user_logs
        self.save_tryout_logs()
        await interaction.response.send_message(f"Tryout role removed from user {user.display_name}", ephemeral=True)
        self.write_log(user_logs["Log"], f"Tryout role unassigned from {user.name} by {interaction.user.name}")

    @app_commands.command(name="list_tryouts", description="List all user you manage currently under tryout.")
    @app_commands.describe(only_active="Only list tryouts you manage (Only affects admins, as it lists all tryouts by default)")
    @app_commands.describe(only_active="Only list active tryout users (Only affects admins)")
    async def list_tryouts(self, interaction: discord.Interaction, only_mine: bool = False, only_active: bool = True):
        print(f"Hello from list-tryouts, {interaction.user.name}")
        if not str(interaction.guild_id) in self.logs["Guilds"].keys(): 
            return await self.no_guild_logs(interaction)
        success, message = self.sanity_check_roles(interaction.guild)
        if not success:
            await interaction.response.send_message(message, ephemeral=True)
            return
        allowed, admin = self.check_permissions(interaction.user, str(interaction.guild_id))
        if not allowed:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild_logs = self.logs["Guilds"][str(interaction.guild_id)]
        return_message = "Your tryouts:\n" if not admin else "All tryouts:\n"
        for k,v in guild_logs["Tryouts"].items():
            if admin and not only_mine:
                if only_active:
                    if v["Tryout"]:
                        return_message += f"- Player: <@{k}>, Manager: <@{v["Manager"]}>, Active: {v["Tryout"]}\n"
                else:
                    return_message += f"- Player: <@{k}>, Manager: <@{v["Manager"]}>, Active: {v["Tryout"]}\n"
            else:
                if str(interaction.user.id) == v["Manager"]:
                    return_message += f"- <@{k}>\n"
        await interaction.followup.send(return_message, ephemeral=True)

    @app_commands.command(name="transfer_tryout", description="Transfer tryout to another manager.")
    @app_commands.describe(user="User you want to transfer manager of")
    @app_commands.describe(manager="Manager you want to transfer the user to")
    async def transfer_tryout(self, interaction: discord.Interaction, user: discord.Member, manager: discord.Member):
        print(f"Hello from transfer-tryout, {interaction.user.name}, {user.name}, {manager.name}")
        if not str(interaction.guild_id) in self.logs["Guilds"].keys(): 
            return await self.no_guild_logs(interaction)
        success, message = self.sanity_check_roles(interaction.guild)
        if not success:
            await interaction.response.send_message(message, ephemeral=True)
            return
        allowed, admin = self.check_permissions(interaction.user, str(interaction.guild_id))
        if not allowed:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        guild_logs = self.logs["Guilds"][str(interaction.guild_id)]
        user_logs = guild_logs["Tryouts"].get(str(user.id), {})
        if not user_logs.get("Tryout", False):
            await interaction.response.send_message(f"User <@{user.id}> does not have a tryout active. The new manager can assign tryout to them.", ephemeral=True)
            return
        manager_allowed, _ =self.check_permissions(manager, str(interaction.guild_id))
        if not manager_allowed:
            await interaction.response.send_message(f"<@{manager.id}> is not assigned as a manager. Ask an admin to give them the manager role first", ephemeral=True)
            return
        old_manager = user_logs["Manager"]
        old_manager_member = interaction.guild.get_member(old_manager)
        user_logs["Manager"] = str(manager.id)
        self.logs["Guilds"][str(interaction.guild_id)]["Tryouts"][str(user.id)] = user_logs
        self.save_tryout_logs()
        await interaction.response.send_message(f"Tryout of user {user.display_name} has been transferred to manager {manager.display_name}", ephemeral=True)
        if old_manager_member is None:
            self.write_log(user_logs["Log"], f"Tryout of {user.name} ({user.id}) transferred from {old_manager} to {manager.name} ({manager.id}) by {interaction.user.name} ({interaction.user.id})")
        else:
            self.write_log(user_logs["Log"], f"Tryout of {user.name} ({user.id}) transferred from {old_manager_member.name} ({old_manager}) to {manager.name} ({manager.id}) by {interaction.user.name} ({interaction.user.id})")


    @app_commands.command(name="inquire_tryout", description="Get info about a user with a tryout role.")
    @app_commands.describe(user="User to get information about")
    @app_commands.describe(get_full_logs="Get the log file containing a user's tryout history (admin only)")
    async def inquire_tryout(self, interaction: discord.Interaction, user: discord.Member, get_full_logs: bool = False):
        print(f"Hello from inquire-tryout, {interaction.user.name}, {user.name}, Get Full Logs: {get_full_logs}")
        if not str(interaction.guild_id) in self.logs["Guilds"].keys(): 
            return await self.no_guild_logs(interaction)
        success, message = self.sanity_check_roles(interaction.guild)
        if not success:
            await interaction.response.send_message(message, ephemeral=True)
            return
        allowed, admin = self.check_permissions(interaction.user, str(interaction.guild_id))
        if not allowed:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        #await interaction.response.defer(ephemeral=True, thinking=True)
        guild_logs = self.logs["Guilds"][str(interaction.guild_id)]
        tryout_member_info = guild_logs["Tryouts"].get(str(user.id))
        if tryout_member_info is None:
            await interaction.response.send_message(f"User <@{user.id}> has never been assigned as tryout.", ephemeral=True)
            return
        if admin:
            return_message = f"Active tryout: {tryout_member_info["Tryout"]}\nManager: <@{tryout_member_info["Manager"]}>"
            if get_full_logs:
                return_message += "\nLog file sending is currently not implemented. I need to learn how to properly send a file in a direct message"
            await interaction.response.send_message(return_message, ephemeral=True)
            return
        else:
            if tryout_member_info.get("Tryout", False):
                await interaction.response.send_message(f"User <@{user.id}> is not currently a tryout.", ephemeral=True)
                return
            else:
                await interaction.response.send_message(f"User <@{user.id}> is currently a tryout.", ephemeral=True)
                return

    @app_commands.command(name="end_tryouts", description="Unassign all tryouts under your name")
    @app_commands.describe(confirm="Confirmation check. Use list tryouts to see who is getting removed.")
    async def end_tryouts(self, interaction: discord.Interaction, confirm:bool = False):
        print(f"Hello from end-tryouts, {interaction.user.name}, Confirmation: {confirm}")
        if not str(interaction.guild_id) in self.logs["Guilds"].keys(): 
            return await self.no_guild_logs(interaction)
        success, message = self.sanity_check_roles(interaction.guild)
        if not success:
            await interaction.response.send_message(message, ephemeral=True)
            return
        allowed, admin = self.check_permissions(interaction.user, str(interaction.guild_id))
        if not allowed:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        if not confirm:
            await interaction.response.send_message("Confirmation not checked. Use list tryouts to see who is getting removed.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild_logs = self.logs["Guilds"][str(interaction.guild_id)]
        guild = self.bot.get_guild(interaction.guild_id)
        role = guild.get_role(int(guild_logs["Tryout Role"]))
        removed_users = []
        for k,v in guild_logs["Tryouts"].items():
            if str(interaction.user.id) == v["Manager"]:
                v["Tryout"] = False
                v["Manager"] = ""
                user = guild.get_member(int(k))
                if not user is None:
                    await user.remove_roles(role)
                removed_users.append(k)
                self.write_log(v["Log"], f"Tryout role unassigned from {user.name} by {interaction.user.name}")
                self.logs["Guilds"][str(interaction.guild_id)]["Tryouts"][k] = v
        if len(removed_users) == 0:
            await interaction.followup.send("No tryouts have been ended. Are you sure you are managing any tryouts?", ephemeral=True)
            return
        else:
            self.save_tryout_logs()
            return_message = "Removed tryouts for users:\n"
            for i in removed_users:
                return_message += f"- <@{i}>\n"
            await interaction.followup.send(return_message, ephemeral=True)
            return

    @app_commands.command(name="set_tryout_role", description="Set tryout role")
    @app_commands.describe(role="Tryout role to assign to users")
    async def set_tryout_role(self, interaction: discord.Interaction, role: discord.Role):
        print(f"Hello from set-tryout-role, {interaction.user.name}, {role.name}, {role.id}")
        if not str(interaction.guild_id) in self.logs["Guilds"].keys(): 
            return await self.no_guild_logs(interaction)
        # success, message = self.sanity_check_roles(interaction.guild)
        # if not success:
        #     await interaction.response.send_message(message, ephemeral=True)
        #     return
        allowed, admin = self.check_permissions(interaction.user, str(interaction.guild_id))
        if not admin:
            await interaction.response.send_message("You do not have permission to use this command. Only admins can use it", ephemeral=True)
            return
        self.logs["Guilds"][str(interaction.guild_id)]["Tryout Role"] = str(role.id)
        self.save_tryout_logs()
        await interaction.response.send_message(f"Tryout role changed to <@&{role.id}>", ephemeral=True)

    @app_commands.command(name="set_manager_role", description="Set team manager role")
    @app_commands.describe(role="Role held by team managers who can manage tryouts")
    async def set_manager_role(self, interaction: discord.Interaction, role: discord.Role):
        print(f"Hello from set-manager-role, {interaction.user.name}, {role.name}, {role.id}")
        if not str(interaction.guild_id) in self.logs["Guilds"].keys(): 
            return await self.no_guild_logs(interaction)
        # success, message = self.sanity_check_roles(interaction.guild)
        # if not success:
        #     await interaction.response.send_message(message, ephemeral=True)
        #     return
        allowed, admin = self.check_permissions(interaction.user, str(interaction.guild_id))
        if not admin:
            await interaction.response.send_message("You do not have permission to use this command. Only admins can use it", ephemeral=True)
            return
        self.logs["Guilds"][str(interaction.guild_id)]["Manager Role"] = str(role.id)
        self.save_tryout_logs()
        await interaction.response.send_message(f"Manager role changed to <@&{role.id}>", ephemeral=True)

    @app_commands.command(name="add_admin_role", description="Add a role to the list of admin roles")
    @app_commands.describe(role="Role to add to admin list")
    async def add_admin_role(self, interaction: discord.Interaction, role: discord.Role):
        print(f"Hello from add-admin-role, {interaction.user.name}, {role.name}, {role.id}")
        if not str(interaction.guild_id) in self.logs["Guilds"].keys(): 
            return await self.no_guild_logs(interaction)
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command. Only adminstrators can use it", ephemeral=True)
            return
        if str(role.id) in self.logs["Guilds"][str(interaction.guild_id)]["Admin Roles"]:
            await interaction.response.send_message(f"Role <@&{role.id}> is already in list of admins", ephemeral=True)
            return
        else:
            self.logs["Guilds"][str(interaction.guild_id)]["Admin Roles"].append(str(role.id))
            self.save_tryout_logs()
            await interaction.response.send_message(f"Role <@&{role.id}> added to list of admins", ephemeral=True)

    @app_commands.command(name="remove_admin_role", description="Add a role to the list of admin roles")
    @app_commands.describe(role="Role to remove from")
    async def remove_admin_role(self, interaction: discord.Interaction, role: discord.Role):
        print(f"Hello from remove-admin-role, {interaction.user.name}, {role.name}, {role.id}")
        if not str(interaction.guild_id) in self.logs["Guilds"].keys(): 
            return await self.no_guild_logs(interaction)
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command. Only adminstrators can use it", ephemeral=True)
            return
        if str(role.id) not in self.logs["Guilds"][str(interaction.guild_id)]["Admin Roles"]:
            await interaction.response.send_message(f"Role <@&{role.id}> not on list of admins", ephemeral=True)
            return
        else:
            self.logs["Guilds"][str(interaction.guild_id)]["Admin Roles"].remove(str(role.id))
            self.save_tryout_logs()
            await interaction.response.send_message(f"Role <@&{role.id}> removed from list of admins", ephemeral=True)

    @app_commands.command(name="view_settings", description="View your permissions and all saved settings belonging to this server")
    async def view_settings(self, interaction: discord.Interaction):
        print(f"Hello from view-settings, {interaction.user.name}")
        if not str(interaction.guild_id) in self.logs["Guilds"].keys(): 
            return await self.no_guild_logs(interaction)
        success, message = self.sanity_check_roles(interaction.guild)
        if not success:
            await interaction.response.send_message(message, ephemeral=True)
            return
        allowed, admin = self.check_permissions(interaction.user, str(interaction.guild_id))
        if not allowed:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        return_message = "Your permissions:\n"
        if allowed: return_message += "- Manager\n"
        if admin: return_message += "- Admin\n"
        if interaction.user.guild_permissions.administrator: return_message += "- Adminstrator\n"
        guild_logs = self.logs["Guilds"][str(interaction.guild_id)]
        return_message += "Roles:\n"
        return_message += f"- Tryout Role: <@&{guild_logs["Tryout Role"]}>\n"
        return_message += f"- Manager Role: <@&{guild_logs["Manager Role"]}>\n"
        if admin:
            return_message += f"- Admin Roles:\n"
            for r in guild_logs["Admin Roles"]:
                return_message += f"\t- <@&{r}>\n"
        #tryouts_list = []
        return_message += "Your tryouts:\n" if not admin else "All active tryouts:\n"
        for k,v in guild_logs["Tryouts"].items():
            if admin:
                if v["Tryout"]:
                    return_message += f"- Player: <@{k}>, Manager: <@{v["Manager"]}>, Active: {v["Tryout"]}\n"
            else:
                if str(interaction.user.id) == v["Manager"]:
                    return_message += f"- <@{k}>\n"
        await interaction.followup.send(return_message, ephemeral=True)
    

    @app_commands.command(name="help", description="View help message for this command module")
    async def help(self, interaction: discord.Interaction):
        return_message = f"Welcome to the tryout module version <{self.cog_version}>. You can use this module to manage tryouts in your server.\n\n"
        return_message += f"The module works in three permission levels, which are the following:\n"
        return_message += f"- Adminstrator: An adminstrator following the server settings. It is the highest permission level, and only one who can assign admin roles\n"
        return_message += f"- Admin: The roles assigned admin status on this module. Can assign and remove managers, and view all logs and settings.\n"
        return_message += f"- Manager: Users who have the manager role assigned to this module. Can assign tryouts to any user, but can only remove tryouts from users they manage.\n\n"
        return_message += f"See the command descriptions for what they each do. As this is still in beta, some problems are to be expected. Please report any problems to <@{310153696044515349}>. Enjoy"
        await interaction.response.send_message(return_message, ephemeral=True)
