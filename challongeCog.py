import discord
import json
from discord import app_commands
from discord.ext import commands
import challonge
import wikitextparser as wtp
import re
from liquipedia.api import LiquipediaAPI
from time import perf_counter, sleep
from requests.exceptions import HTTPError
from math import log2

# TODO: Make it so that you use a discord command that updates both challonge and liquipedia at the same time. Because why not?

class ChallongeCog(commands.GroupCog, name="challonge"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()  # this is now required for GroupCog.
        self.challonge_ID = None
        self.challonge_participants = {None: "TBD"}
        self.tournament = None
        self.tournament_type = ""
        self.current_tournament_state = ""
        self.group_stage = False
        self.group_IDs = {}
        self.group_winners = 2  # hard coded cause Challonge does not supply anything to indicate it before knockouts start
        self.group_seperate_rounds = False  # For now hard coded, but can eventually be inferred from Liquipedia data
        self.liquipedia_API = LiquipediaAPI(testBot=self.bot.isTest)
        self.liquipedia_API.last_command_time -= 5
        print("Challonge cog attempting to log into Liquipedia")
        login_result = self.liquipedia_API.login()
        print("Attempt results:", login_result)
        #self.liquipedia_pageID = "153516"      # https://liquipedia.net/rocketleague/UTB_Invitational/Oct_2024
        #self.liquipedia_pageID = "154026"      # https://liquipedia.net/rocketleague/index.php?title=User:GO_AWAY_77/test_tourney
        #self.liquipedia_pageID = "155193"      # https://liquipedia.net/rocketleague/UTB_Invitational/Dec_2024
        #self.liquipedia_pageID = "155317"      # https://liquipedia.net/rocketleague/index.php?title=User:GO_AWAY_77/test_tourney2
        #self.liquipedia_pageID = "157880"      # https://liquipedia.net/rocketleague/UTB_Invitational/Feb_2025
        #self.liquipedia_pageID = "158354"      # https://liquipedia.net/rocketleague/index.php?title=User:GO_AWAY_77/test_tourney3
        #self.liquipedia_pageID = "159564"      # https://liquipedia.net/rocketleague/User:GO_AWAY_77/test_tourney4
        #self.liquipedia_pageID = "159223"      # https://liquipedia.net/rocketleague/UTB_Invitational/Apr_2025
        #self.liquipedia_pageID = "161574"       # https://liquipedia.net/rocketleague/UTB_Invitational/Jun_2025
        #self.liquipedia_pageID = "162094"       # https://liquipedia.net/rocketleague/User:GO_AWAY_77/test_tourney5
        #self.liquipedia_pageID = "164586"       # https://liquipedia.net/rocketleague/User:GO_AWAY_77/test_tourney6
        self.liquipedia_pageID = "164618"       # https://liquipedia.net/rocketleague/User:GO_AWAY_77/test_tourney7
        #self.liquipedia_pageID = "162438"       # https://liquipedia.net/rocketleague/UTB_Invitational/Sep_2025
        self.liquipedia_group_section = 8   # Points to the section number of the first group
        self.liquipedia_section = 12
        self.match_mappings = {}
        self.last_command_time = perf_counter()
        self.last_command_time_large = perf_counter()
        self.API_Cooldown = 5
        self.API_Cooldown_Large = 20
        with open("challongeData/team_templates.json", "r") as f:
            self.team_templates = json.load(f)
        self.allowed_users = [310153696044515349, # go_away_77
                              349879697330536448, # longey
                              405653221604851732] # Kuro
    
    """
    Needed commands:
    - List challonge tournaments
    - Assign tournament to track
    - Assign liquipedia tournament page (Might wanna hard code this so that it cannot be abused)
    - Sync liquipedia    
    """

    @app_commands.command(name="list-tourneys", description="List all the tournaments made by the UTB challonge account")
    async def list_tourneys(self, interaction: discord.Interaction):
        print(f"Hello from list-tourneys, {interaction.user.name}")
        if not interaction.user.id in self.allowed_users:
            await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
            return
        time_since_last = perf_counter() - self.last_command_time
        if time_since_last < self.API_Cooldown:
            await interaction.response.send_message(f"Please wait {self.API_Cooldown-time_since_last:.1f}s before using this command again", ephemeral=True)
            return
        return_message = ""
        for t in challonge.tournaments.index():
            return_message += f"{t['name']}:\n\tID: {t['id']}\n\tURL: {t['full_challonge_url']}\n\tGame: {t['game_name']}\n\tType: {t['tournament_type']}\n\tState: {t['state']}\n\tParticipants count: {t['participants_count']}\n"
        await interaction.response.send_message(return_message, ephemeral=True)
        self.last_command_time = perf_counter()

    @app_commands.command(name="assign-challonge-tourney", description="Assign the Challonge tournament to track")
    @app_commands.describe(challonge_id="The ID of the Challonge tournament to track")
    async def assign_challonge_tourney(self, interaction: discord.Interaction, challonge_id: int):
        print(f"Hello from assign-challonge-tourney, {challonge_id}, {interaction.user.name}")
        if not interaction.user.id in self.allowed_users:
            await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
            return
        time_since_last = perf_counter() - self.last_command_time
        if time_since_last < self.API_Cooldown:
            await interaction.response.send_message(f"Please wait {self.API_Cooldown-time_since_last:.1f}s before using this command again", ephemeral=True)
            return
        self.challonge_ID = challonge_id
        try:
            self.tournament = challonge.tournaments.show(self.challonge_ID)
            if self.tournament['state'] == 'pending':
                await interaction.response.send_message(f"Challonge tournament is not started yet. Cannot assign this tournament")
                return
            else:
                self.current_tournament_state = self.tournament['state']
            await interaction.response.defer(ephemeral=True, thinking=True)
            self.tournament_type = self.tournament["tournament_type"]
            print("Group stages enabled?", self.tournament["group_stages_enabled"])
            self.group_stage = self.tournament["group_stages_enabled"]

            self.challonge_participants = {None: "TBD"}
            self.challonge_participants_group_ID = {None: "TBD"}
            self.challonge_participants_groups = {None: "None"}
            for p in challonge.participants.index(self.challonge_ID):
                self.challonge_participants[p["id"]] = p["name"]
                if self.group_stage:
                    self.challonge_participants_group_ID[p["group_player_ids"][0]] = p["name"]
                    self.challonge_participants_groups[p["id"]] = p["group_id"]
                    if p['group_id'] in self.group_IDs.keys():
                        self.group_IDs[p['group_id']] += 1
                    else:
                        self.group_IDs[p['group_id']] = 1

        except HTTPError as e:
            await interaction.response.send_message(f"There is an error with the ID. Please double check it.", ephemeral=True)
            raise e
        result = self.determine_liquipedia_group_format()
        if not result is None:
            await interaction.followup.send(result, ephemeral=True)  
        result = self.get_match_pairings()
        if not result is None:
            await interaction.followup.send(result, ephemeral=True)  
        await interaction.followup.send(f"Challonge tournament with ID {self.challonge_ID} and name {self.tournament["name"]} has been assigned for tracking", ephemeral=True)
        self.last_command_time = perf_counter()
        print("Match mappings:",self.match_mappings)
        print("Seperate group rounds:",self.group_seperate_rounds)
    
    @app_commands.command(name="list-matches", description="List all matches in the assigned Challonge tournament")
    async def list_matches(self, interaction: discord.Interaction):
        print(f"Hello from list-matches, {interaction.user.name}")
        if not interaction.user.id in self.allowed_users:
            await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
            return
        if not interaction.user.id in self.allowed_users:
            await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
            return
        if self.challonge_ID is None:
            await interaction.response.send_message("No Challonge tournament has been assigned for tracking yet", ephemeral=True)
            return
        time_since_last = perf_counter() - self.last_command_time
        if time_since_last < self.API_Cooldown:
            await interaction.response.send_message(f"Please wait {self.API_Cooldown-time_since_last:.1f}s before using this command again", ephemeral=True)
            return
        return_message = ""
        for m in challonge.matches.index(self.challonge_ID):
            p1ID = m["player1_id"]
            p2ID = m["player2_id"]
            if p1ID is None and p2ID is None:
                continue
            else:
                match_round = m["round"]
                state = m["state"]
                return_message += f"{m['id']}:\n\t{self.challonge_participants[p1ID]} ({p1ID}) vs {self.challonge_participants[p2ID]} ({p2ID})\n"
                if match_round < 0:
                    return_message += f"\tRound: Lower {abs(match_round)}\n"
                else:
                    return_message += f"\tRound: Upper {match_round}\n"
                return_message += f"\tState: {state}\n"
                if state == "complete":
                    return_message += f"\tScore: {m['scores_csv']}\n\tWinner: {self.challonge_participants[m['winner_id']]} ({m["winner_id"]}))\n"
        if len(return_message) == 0: return_message = "No matches with teams found."
        await interaction.response.send_message(return_message, ephemeral=True)
        self.last_command_time = perf_counter()

    async def sync_liquipedia_groups(self, interaction: discord.Interaction, challonge_matches):
        for G_ind, G_ID in enumerate(sorted(self.group_IDs.keys())):
            self.liquipedia_API.last_command_time -= 5
            liquipedia_group = self.liquipedia_API.get_page_section(self.liquipedia_pageID, self.liquipedia_group_section+G_ind)
            if liquipedia_group.get("error", None) is not None:
                await interaction.followup.send(liquipedia_group["error"], ephemeral=True)
                return False
            revID = liquipedia_group["query"]["pages"][self.liquipedia_pageID]["revisions"][0]["revid"]
            text = liquipedia_group["query"]["pages"][self.liquipedia_pageID]["revisions"][0]["slots"]["main"]["*"]
            parsed_group = wtp.parse(text)
            is_group_section = False
            for t in parsed_group.templates:
                if t.name == "GroupTableLeague":
                    is_group_section = True
                    break
            if not is_group_section:
                await interaction.followup.send(f"Cannot find group table. Currently looking at section {self.liquipedia_group_section+G_ind}", ephemeral=True)
                return False
            match_lists = []
            group_table = None
            for t in parsed_group.templates:
                if t.name == "GroupTableLeague":
                    group_table = t
                if t.name.lower() == "matchlist":
                    match_lists.append(t)
            for m in challonge_matches:
                match_group_id = "None" if m["group_id"] is None else m["group_id"]
                if match_group_id != G_ID:
                    continue
                liquipedia_indicator = self.match_mappings[match_group_id][m["identifier"]]
                if "R" in liquipedia_indicator:
                    match_list_ind = int(liquipedia_indicator[1])-1
                else:
                    match_list_ind = 0
                try:
                    t = match_lists[match_list_ind]
                except IndexError:
                    await interaction.followup.send(f"Tried to fill round {match_list_ind+1} in group {G_ind}, but did not find it in Liquipedia", ephemeral=True)
                    return False
                match_arg = t.get_arg(liquipedia_indicator[-2:])
                #print(liquipedia_indicator, match_arg)
                if match_arg is None:
                    continue
                team1 = self.team_templates.get(self.challonge_participants_group_ID[m["player1_id"]], self.challonge_participants_group_ID[m["player1_id"]]).lower()
                team2 = self.team_templates.get(self.challonge_participants_group_ID[m["player2_id"]], self.challonge_participants_group_ID[m["player2_id"]]).lower()
                state = m["state"]
                if "-" in m["scores_csv"]:
                    score = m["scores_csv"].split("-")
                else:
                    score = ["0", "0"]
                if state == "complete":
                    #score = m["scores_csv"].split("-")
                    winner = self.team_templates.get(self.challonge_participants_group_ID[m["winner_id"]], self.challonge_participants_group_ID[m["winner_id"]])
                for t2 in match_arg.templates:
                    if re.match("^Match", t2.name):
                        #if state == "complete":
                        #if True:
                        opp1 = "\n" if team1 == "tbd" else "{{TeamOpponent|" + team1 + "|score=" + score[0] + "}}\n"
                        opp2 = "\n" if team2 == "tbd" else "{{TeamOpponent|" + team2 + "|score=" + score[1] + "}}\n"
                        if state == "complete":
                            t2.set_arg("finished", "true\n")
                        else:
                            t2.set_arg("finished", "false\n")
                        #else:
                        #    opp1 = "" if m["player1_id"] is None else "{{TeamOpponent|" + team1 + "|score=0}}"
                        #    opp2 = "" if m["player2_id"] is None else "{{TeamOpponent|" + team2 + "|score=0}}"
                        if t2.has_arg("opponent1"):
                            t2.set_arg("opponent1", opp1)
                        elif t2.has_arg("opponent1literal"):
                            t2.set_arg("opponent1", opp1, before="opponent1literal")
                        else:
                            t2.set_arg("opponent1", opp1, before="map1")
                        if t2.has_arg("opponent2"):
                            t2.set_arg("opponent2", opp2)
                        elif t2.has_arg("opponent2literal"):
                            t2.set_arg("opponent2", opp2, before="opponent2literal")
                        else:
                            t2.set_arg("opponent2", opp2, after="opponent1")
                        break
            with open("challongeData/ignore_result_groups.txt", "w") as f:
                f.write(parsed_group.__str__())
            self.liquipedia_API.last_command_time -= 5
            edit_result = self.liquipedia_API.edit_page_section(self.liquipedia_pageID, self.liquipedia_group_section+G_ind, parsed_group.__str__(), "Bot automated bracket sync with challonge bracket.", revID)
            print(f"Group {G_ind} edit result:", edit_result)
            if edit_result.get("error", None) is not None:
                await interaction.followup.send(edit_result["error"], ephemeral=True)
                return False
        return True
        
    async def sync_liquipedia_knockout(self, interaction: discord.Interaction, challonge_matches):
        self.liquipedia_API.last_command_time -= 5
        liquipedia_bracket = self.liquipedia_API.get_page_section(self.liquipedia_pageID, self.liquipedia_section)
        if liquipedia_bracket.get("error", None) is not None:
            await interaction.followup.send(liquipedia_bracket["error"], ephemeral=True)
            return False
        revID = liquipedia_bracket["query"]["pages"][self.liquipedia_pageID]["revisions"][0]["revid"]
        text = liquipedia_bracket["query"]["pages"][self.liquipedia_pageID]["revisions"][0]["slots"]["main"]["*"]
        parsed_bracket = wtp.parse(text)
        is_bracket_section = False
        for t in parsed_bracket.templates:
            if t.name == "Bracket":
                is_bracket_section = True
                break
        if not is_bracket_section:
            parsed_bracket = self.update_liquipedia_section()
            if parsed_bracket is None:
                await interaction.followup.send("No bracket found in the liquipedia page", ephemeral=True)
                return False
            elif parsed_bracket.get("error", None) is not None:
                await interaction.followup.send(parsed_bracket["error"], ephemeral=True)
                return False
        for t in parsed_bracket.templates:
            if t.name == "Bracket":
                for m in challonge_matches:
                    if m["group_id"] is not None:
                        continue
                    liquipedia_indicator = self.match_mappings["None"][m["identifier"]]
                    match_arg = t.get_arg(liquipedia_indicator)
                    if match_arg is None:
                        continue
                    team1 = self.team_templates.get(self.challonge_participants[m["player1_id"]], self.challonge_participants[m["player1_id"]]).lower()
                    team2 = self.team_templates.get(self.challonge_participants[m["player2_id"]], self.challonge_participants[m["player2_id"]]).lower()
                    state = m["state"]
                    if "-" in m["scores_csv"]:
                        score = m["scores_csv"].split("-")
                    else:
                        score = ["0", "0"]
                    if state == "complete":
                        #score = m["scores_csv"].split("-")
                        winner = self.team_templates.get(self.challonge_participants[m["winner_id"]], self.challonge_participants[m["winner_id"]])
                    for t2 in match_arg.templates:
                        if re.match("^Match", t2.name):
                            #if state == "complete":
                            #if True:
                            # Challonge flips team in bracker reset. So I hard-coded it to unflip them for Liquipedia
                            if liquipedia_indicator == "RxMBR":
                                opp2 = "\n\t" if team1 == "tbd" else "{{TeamOpponent|" + team1 + "|score=" + score[0] + "}}\n\t"
                                opp1 = "\n\t" if team2 == "tbd" else "{{TeamOpponent|" + team2 + "|score=" + score[1] + "}}\n\t"
                            else:
                                opp1 = "\n\t" if team1 == "tbd" else "{{TeamOpponent|" + team1 + "|score=" + score[0] + "}}\n\t"
                                opp2 = "\n\t" if team2 == "tbd" else "{{TeamOpponent|" + team2 + "|score=" + score[1] + "}}\n\t"
                            if state == "complete":
                                t2.set_arg("finished", "true\n\t")
                            else:
                                t2.set_arg("finished", "false\n\t")
                            #else:
                            #    opp1 = "" if m["player1_id"] is None else "{{TeamOpponent|" + team1 + "|score=0}}"
                            #    opp2 = "" if m["player2_id"] is None else "{{TeamOpponent|" + team2 + "|score=0}}"
                            if t2.has_arg("opponent1"):
                                t2.set_arg("opponent1", opp1)
                            elif t2.has_arg("opponent1literal"):
                                t2.set_arg("opponent1", opp1, before="opponent1literal")
                            else:
                                t2.set_arg("opponent1", opp1, before="map1")
                            if t2.has_arg("opponent2"):
                                t2.set_arg("opponent2", opp2)
                            elif t2.has_arg("opponent2literal"):
                                t2.set_arg("opponent2", opp2, before="opponent2literal")
                            else:
                                t2.set_arg("opponent2", opp2, after="opponent1")
                            break
                break
        #print(parsed_bracket)
        with open("challongeData/ignore_result_bracket.txt", "w") as f:
            f.write(parsed_bracket.__str__())
        self.liquipedia_API.last_command_time -= 5
        edit_result = self.liquipedia_API.edit_page_section(self.liquipedia_pageID, self.liquipedia_section, parsed_bracket.__str__(), "Bot automated bracket sync with challonge bracket.", revID)
        print(f"Knockout bracket edit result:", edit_result)
        if edit_result.get("error", None) is not None:
            await interaction.followup.send(edit_result["error"], ephemeral=True)
            return False
        return True

    @app_commands.command(name="sync-liquipedia-bracket", description="Sync the liquipedia bracket with the assigned Challonge tournament")
    @app_commands.describe(force_full_update="Bot does not sync group matches once knockout stage starts. Set true to force full sync.")
    async def sync_liquipedia_bracket(self, interaction: discord.Interaction, force_full_update:bool = False):
        print(f"Hello from sync-liquipedia-bracket, {interaction.user.name}")
        if not interaction.user.id in self.allowed_users:
            await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
            return
        if self.challonge_ID is None:
            await interaction.response.send_message("No Challonge tournament has been assigned for tracking yet", ephemeral=True)
            return
        elif self.liquipedia_pageID is None:
            await interaction.response.send_message("No liquipedia page has been assigned for syncing yet", ephemeral=True)
            return
        elif log2(len(self.challonge_participants)-1) % 1 != 0:
            await interaction.response.send_message("The number of participants in the Challonge tournament is not a power of 2. Odd shaped brackets are not supported yet.", ephemeral=True)
            return
        time_since_last = perf_counter() - self.last_command_time
        if time_since_last < self.API_Cooldown_Large:
            await interaction.response.send_message(f"Please wait {self.API_Cooldown_Large-time_since_last:.1f}s before using this command again", ephemeral=True)
            return
        try:
            self.tournament = challonge.tournaments.show(self.challonge_ID)
        except HTTPError as e:
            await interaction.response.send_message(f"There is an error with the ID. Please double check it.", ephemeral=True)
            raise e
        if self.tournament["split_participants"]:
            await interaction.response.send_message(f"Split tournaments are not supported yet", ephemeral=True)
            return
        elif not (self.tournament_type in ["single elimination", "double elimination"]):
            await interaction.response.send_message(f"{self.tournament_type} tournaments are not supported yet", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        challonge_matches = challonge.matches.index(self.challonge_ID)
        self.last_command_time = perf_counter()
        # Only sync needed parts
        if force_full_update:
            group_success = await self.sync_liquipedia_groups(interaction, challonge_matches)
            if not group_success: return
            knockout_success = await self.sync_liquipedia_knockout(interaction, challonge_matches)
            if not knockout_success: return
        elif self.tournament["state"] == "group_stages_underway" or self.tournament["state"] == "group_stages_finalized":
            group_success = await self.sync_liquipedia_groups(interaction, challonge_matches)
            if not group_success: return
        else:
            knockout_success = await self.sync_liquipedia_knockout(interaction, challonge_matches)
            if not knockout_success: return
        await interaction.followup.send("Bracket has been synced", ephemeral=True)
        return
            

    @app_commands.command(name="liquipedia-login", description="Login to liquipedia in case the bot got logged out")
    async def liquipedia_login(self, interaction: discord.Interaction):
        print(f"Hello from liquipedia-login, {interaction.user.name}")
        if not interaction.user.id in self.allowed_users:
            await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
            return
        result = self.liquipedia_API.login()
        #if "error" in result.keys():
        if result.get("error", None) is not None:
            await interaction.response.send_message(result["error"], ephemeral=True)
        else:
            await interaction.response.send_message(f"Bot has logged into Liquipedia as {result["login"]["lgusername"]}", ephemeral=True)

    @app_commands.command(name="liquipedia-logout", description="Try and logout the bot from liquipedia")
    async def liquipedia_logout(self, interaction: discord.Interaction):
        print(f"Hello from liquipedia-logout, {interaction.user.name}")
        if not interaction.user.id in self.allowed_users:
            await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
            return
        result = self.liquipedia_API.logout()
        #if "error" in result.keys():
        if result.get("error", None) is not None:
            await interaction.response.send_message(result["error"], ephemeral=True)
        else:
            await interaction.response.send_message(f"Bot has been logged out of Liquipedia", ephemeral=True)

    @app_commands.command(name="edit-team-template", description="Create/edit the Liquipedia team template of a Challonge team")
    @app_commands.describe(challonge_name="The name of the team in Challonge", liquipedia_template="The name of the team template in Liquipedia")
    async def edit_team_template(self, interaction: discord.Interaction, challonge_name:str, liquipedia_template:str):
        print(f"Hello from edit-team-template, {challonge_name}, {liquipedia_template}, {interaction.user.name}")
        if not interaction.user.id in self.allowed_users:
            await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
            return
        self.team_templates[challonge_name] = liquipedia_template.lower()
        with open("challongeData/team_templates.json", "w") as f:
            json.dump(self.team_templates, f, indent=2)
        await interaction.response.send_message(f"Template for {challonge_name} has been updated to {liquipedia_template}", ephemeral=True)

    @app_commands.command(name="find-team-template", description="Show team template. Leave both options empty to list all templates")
    async def find_team_templates(self, interaction: discord.Interaction, challonge_name:str = None, liquipedia_template:str = None):
        print(f"Hello from find-team-template, {challonge_name}, {liquipedia_template}, {interaction.user.name}")
        if not interaction.user.id in self.allowed_users:
            await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
            return
        if challonge_name is None and liquipedia_template is None:
            return_message = "{\n"
            for k,v in self.team_templates.items():
                return_message += f"\t{k}: {v}\n"
            return_message += "}"
        elif challonge_name is None:
            for k,v in self.team_templates.items():
                if v == liquipedia_template:
                    return_message = "{" + f"{k}: {v}" + "}"
                else:
                    return_message = "No team found with this template.  You can create one using edit_team_template."
        else:
            team_template = self.team_templates.get(challonge_name, None)
            if team_template is None:
                return_message = "No template found for this team. You can create one using edit_team_template."
            else:
                return_message = f"Template for {challonge_name} is {team_template}"
        await interaction.response.send_message(return_message, ephemeral=True)

    # TODO: Give error if num_winners results in a number of bracket participants that is not divisble by 2 as that is not supported yet
    # @app_commands.command(name="edit-group-winners", description="Change number of teams that advance in a group stage tournament. Default=2")
    # @app_commands.describe(num_winners="The number of teams that advance in each group.")
    # async def edit_group_winners(self, interaction: discord.Interaction, num_winners:int):
    #     print(f"Hello from edit-team-template, {num_winners}, {interaction.user.name}")
    #     if not interaction.user.id in self.allowed_users:
    #         await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
    #         return
    #     elif not self.group_stage:
    #         await interaction.response.send_message("Currently assigned tournament does not have a group stage.")
    #         return
    #     elif num_winners < 1:
    #         await interaction.response.send_message("Number of winners cannot be less than 1.")
    #         return
    #     elif num_winners > ceil(len(self.challonge_participants.keys())/len(self.group_IDs)):
    #         await interaction.response.send_message(f"Number of winners cannot be more than maximum number of teams per group {ceil(len(self.challonge_participants.keys())/len(self.group_IDs))}.")
    #         return
    #     self.group_winners = int(num_winners)
    #     await interaction.response.send_message(f"Number of teams advancing a group has been updated to {num_winners}.", ephemeral=True)  
    #     result = self.get_match_pairings()
    #     print("Match mappings:",self.match_mappings)


    def update_liquipedia_section(self):
        page = self.liquipedia_API.get_page(self.liquipedia_pageID)
        if page.get("error", None) is not None:
            return page
        text = page["query"]["pages"][self.liquipedia_pageID]["revisions"][0]["slots"]["main"]["*"]
        parsed_page = wtp.parse(text)
        page_sections = parsed_page.get_sections()
        has_bracket = False
        for i,s in enumerate(page_sections):
            for t in s.templates:
                if t.name == "Results":
                    self.liquipedia_section = i
                    has_bracket = True
                    break
        return page_sections[self.liquipedia_section] if has_bracket else None

    # Looks to see if the groups in Liquipedia are seperated by rounds, or are all in one round
    def determine_liquipedia_group_format(self):
        liquipedia_group = self.liquipedia_API.get_page_section(self.liquipedia_pageID, self.liquipedia_group_section)
        if liquipedia_group.get("error", None) is not None:
            print("Error when determining liquipedia group format:",liquipedia_group["error"])
            return liquipedia_group["error"]
        text = liquipedia_group["query"]["pages"][self.liquipedia_pageID]["revisions"][0]["slots"]["main"]["*"]
        parsed_group = wtp.parse(text)
        is_group_section = False
        for t in parsed_group.templates:
            if t.name == "GroupTableLeague":
                is_group_section = True
                break
        if not is_group_section:
            print(f"Cannot find group table. Currently looking at section {self.liquipedia_group_section}", ephemeral=True)
            return f"Cannot find group table. Currently looking at section {self.liquipedia_group_section}"
        match_lists = []
        for t in parsed_group.templates:
            if t.name.lower() == "matchlist":
                match_lists.append(t)
        if len(match_lists) > 1:
            self.group_seperate_rounds = True
        else:
            self.group_seperate_rounds = False
        return

    def get_match_pairings_knockout(self, num_participants):
        if self.tournament_type == "double elimination":
            # After testing it looks like challonge does make the matches even though it skips them
            grand_final_no_reset = False # self.tournament["grand_finals_modifier"] == "single match"
            grand_final_skipped = False # self.tournament["grand_finals_modifier"] == "skip"
            num_rounds = 2*int(log2(num_participants))-1*grand_final_no_reset-2*grand_final_skipped
            num_matches = 2*num_participants-1-1*grand_final_no_reset-1*grand_final_skipped             # Each team can lose twice except winner who can lose once or twice
            num_upper_matches = num_participants+1*(not grand_final_no_reset)-1*grand_final_skipped
            #print("Num rounds:", num_rounds)
            #print("Num matches:", num_matches)
            #print("Num upper matches:", num_upper_matches)
            num_lower_matches = num_matches - num_upper_matches
            challonge_identifiers = ["" for _ in range(num_matches)]
            for i in range(num_matches):
                base = 1
                letter_indices = []
                if i==0:
                    letter_indices.insert(0, 0)
                else:
                    while i//base > 0:
                        letter_indices.insert(0,(i//base) % 26)
                        base *= 26
                letter = ""
                for n, j in enumerate(letter_indices):
                    letter += chr(65+j-(n==0 and len(letter_indices)>1))
                challonge_identifiers[i] += letter
            match_mappings = {}
            upper_round = 1
            upper_match = 1
            match_limit = num_participants//2
            match_limit2 = num_participants//2
            for j in range(num_upper_matches):
                if j < match_limit:
                    match_mappings[challonge_identifiers[j]] = f"R{upper_round}M{upper_match}"
                    upper_match += 1
                else:
                    if j+1 > num_participants-1:
                        if grand_final_no_reset:
                            assert j+1 == num_upper_matches
                            match_mappings[challonge_identifiers[j]] = f"R{num_rounds}M1"
                        else:
                            assert j+1 == num_upper_matches-1
                            #print(num_rounds)
                            match_mappings[challonge_identifiers[j]] = f"R{num_rounds-1}M1"
                            #print(f"{challonge_identifiers[j]}: R{num_rounds-1}M1")
                            # Turns out that the bracket reset is assigned to RxMBR and not R6M1
                            #match_mappings[challonge_identifiers[j+1]] = f"R{num_rounds}M1"
                            match_mappings[challonge_identifiers[j+1]] = f"RxMBR"
                            #print(f"{challonge_identifiers[j]}: R{num_rounds-1}M1")
                        break
                    elif upper_round == 1:
                        upper_round += 1
                    else:
                        upper_round += 2
                    match_limit += match_limit2//2
                    match_limit2 = match_limit2//2
                    #print(j, upper_round, match_limit2, num_participants-1)
                    assert match_limit2 > 0
                    upper_match = 1
                    match_mappings[challonge_identifiers[j]] = f"R{upper_round}M{upper_match}"
                    upper_match += 1
            lower_round = 1
            lower_match = 1
            match_limit = num_upper_matches+num_participants//4
            match_limit2 = num_participants//4
            highest_upper = 0
            for v in list(match_mappings.values()):
                #if v[1] == f"R{lower_round}":
                if re.match(f"^R{lower_round}", v):
                    highest_upper = max(highest_upper, int(v.split("M")[1]))
            for j in range(num_upper_matches, num_matches):
                if j < match_limit:
                    match_mappings[challonge_identifiers[j]] = f"R{lower_round}M{lower_match+highest_upper}"
                    lower_match += 1
                else:
                    if (lower_round % 2) == 0:
                        match_limit += match_limit2//2
                        match_limit2 = match_limit2//2
                    else:
                        match_limit += match_limit2
                    lower_round += 1
                    highest_upper = 0
                    for v in list(match_mappings.values()):
                        if re.match(f"^R{lower_round}", v):
                            highest_upper = max(highest_upper, int(v.split("M")[1]))
                    lower_match = 1
                    match_mappings[challonge_identifiers[j]] = f"R{lower_round}M{lower_match+highest_upper}"
                    lower_match += 1
        elif self.tournament_type == "single elimination":
            num_rounds = int(log2(num_participants))
            num_matches = num_participants-1
            challonge_identifiers = ["" for _ in range(num_matches)]
            for i in range(num_matches):
                letter = chr(65+(i % 26))
                challonge_identifiers[i] += letter
            match_mappings = {}
            for j in range(num_upper_matches):
                if j < match_limit:
                    match_mappings[challonge_identifiers[j]] = f"R{upper_round}M{upper_match}"
                    upper_match += 1
                else:
                    upper_round += 1
                    match_limit += match_limit2//2
                    match_limit2 = match_limit2//2
                    assert match_limit2 > 0
                    upper_match = 1
                    match_mappings[challonge_identifiers[j]] = f"R{upper_round}M{upper_match}"
                    upper_match += 1
        return match_mappings

    def get_match_pairings_group(self, group_ID, num_participants, challonge_matches = None):
        if challonge_matches is None:
            challonge_matches = challonge.matches.index(self.challonge_ID)
            sleep(10)
        match_mapping = {}
        match_num = 0
        if self.group_seperate_rounds:
            round_num = 0
            for m in challonge_matches:
                if m["group_id"] == group_ID:
                    if round_num != m["round"]: match_num = 0
                    round_num = m["round"] 
                    match_num += 1
                    match_mapping[m["identifier"]] = f"R{round_num}M{match_num}"
        else:
            for m in challonge_matches:
                if m["group_id"] == group_ID:
                    match_num += 1
                    match_mapping[m["identifier"]] = f"M{match_num}"
        return match_mapping

    def get_match_pairings(self):
        if self.group_stage:
            challonge_matches = challonge.matches.index(self.challonge_ID)
            for group_ID, num_participants in sorted(self.group_IDs.items()):
                self.match_mappings[group_ID] = self.get_match_pairings_group(group_ID, num_participants, challonge_matches)
            num_participants = int(len(self.group_IDs)*self.group_winners)
        else:
            num_participants = len(self.challonge_participants)-1           # -1 for None user assigned by default
        print("Amount of bracket participants:", num_participants)
        self.match_mappings["None"] = self.get_match_pairings_knockout(num_participants)