import discord
import json
from discord import app_commands
from discord.ext import commands
import challonge
import wikitextparser as wtp
import re
from liquipedia.api import LiquipediaAPI
from time import perf_counter
from requests.exceptions import HTTPError
from math import log2

class ChallongeCog(commands.GroupCog, name="challonge"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()  # this is now required for GroupCog.
        self.challonge_ID = None
        self.challonge_participants = {None: "TBD"}
        self.tournament = None
        self.tournament_type = ""
        self.liquipedia_API = LiquipediaAPI(testBot=self.bot.isTest)
        self.liquipedia_API.last_command_time -= 5
        print("Challong cog attempting to log into Liquipedia")
        login_result = self.liquipedia_API.login()
        print("Attempt results:", login_result)
        #self.liquipedia_pageID = "153516"
        self.liquipedia_pageID = "154026"
        self.liquipedia_section = 6
        self.match_mappings = None
        self.last_command_time = perf_counter()
        self.last_command_time_large = perf_counter()
        self.API_Cooldown = 5
        self.API_Cooldown_Large = 60
        with open("challongeData/team_templates.json", "r") as f:
            self.team_templates = json.load(f)
        self.allowed_users = [310153696044515349, # go_away_77
                              457141417014460416, # headstart96
                              349879697330536448] # longey
    
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
            for p in challonge.participants.index(self.challonge_ID):
                self.challonge_participants[p["id"]] = p["name"]
        except HTTPError as e:
            await interaction.response.send_message(f"There is an error with the ID. Please double check it.", ephemeral=True)
            raise e
        self.tournament = challonge.tournaments.show(self.challonge_ID)
        self.tournament_type = self.tournament["tournament_type"]
        await interaction.response.send_message(f"Challonge tournament with ID {self.challonge_ID} and name {self.tournament["name"]} has been assigned for tracking", ephemeral=True)
        self.last_command_time = perf_counter()
        self.get_match_pairings()
        #print(self.match_mappings)
    
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

    @app_commands.command(name="sync-liquipedia-bracket", description="Sync the liquipedia bracket with the assigned Challonge tournament")
    async def sync_liquipedia_bracket(self, interaction: discord.Interaction):
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
        if time_since_last < self.API_Cooldown:
            await interaction.response.send_message(f"Please wait {self.API_Cooldown-time_since_last:.1f}s before using this command again", ephemeral=True)
            return
        if self.tournament["split_participants"]:
            await interaction.response.send_message(f"Split tournaments are not supported yet", ephemeral=True)
            return
        elif not (self.tournament_type in ["single elimination", "double elimination"]):
            await interaction.response.send_message(f"{self.tournament_type} tournaments are not supported yet", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        challonge_matches = challonge.matches.index(self.challonge_ID)
        self.last_command_time = perf_counter()
        liquipedia_bracket = self.liquipedia_API.get_page_section(self.liquipedia_pageID, self.liquipedia_section)
        if liquipedia_bracket.get("error", None) is not None:
            await interaction.followup.send(liquipedia_bracket["error"], ephemeral=True)
            return
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
                return
            elif parsed_bracket.get("error", None) is not None:
                await interaction.followup.send(parsed_bracket["error"], ephemeral=True)
                return
        for t in parsed_bracket.templates:
            if t.name == "Bracket":
                for m in challonge_matches:
                    liquipedia_indicator = self.match_mappings[m["identifier"]]
                    match_arg = t.get_arg(liquipedia_indicator)
                    if match_arg is None:
                        continue
                    team1 = self.team_templates.get(self.challonge_participants[m["player1_id"]], self.challonge_participants[m["player1_id"]]).lower()
                    team2 = self.team_templates.get(self.challonge_participants[m["player2_id"]], self.challonge_participants[m["player2_id"]]).lower()
                    state = m["state"]
                    if state == "complete":
                        score = m["scores_csv"].split("-")
                        winner = self.team_templates.get(self.challonge_participants[m["winner_id"]], self.challonge_participants[m["winner_id"]])
                    for t2 in match_arg.templates:
                        if re.match("^Match", t2.name):
                            if state == "complete":
                                opp1 = "{{TeamOpponent|" + team1 + "|score=" + score[0] + "}}"
                                opp2 = "{{TeamOpponent|" + team2 + "|score=" + score[1] + "}}"
                                t2.set_arg("finished", "true\n\t")
                            else:
                                opp1 = "" if m["player1_id"] is None else "{{TeamOpponent|" + team1 + "|score=0}}"
                                opp2 = "" if m["player2_id"] is None else "{{TeamOpponent|" + team2 + "|score=0}}"
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
        with open("challongeData/result_bracket.txt", "w") as f:
            f.write(parsed_bracket.__str__())
        self.liquipedia_API.last_command_time -= 5
        edit_result = self.liquipedia_API.edit_page_section(self.liquipedia_pageID, self.liquipedia_section, parsed_bracket.__str__(), "Bot automated bracket sync with challonge bracket.", revID)
        if edit_result.get("error", None) is not None:
            await interaction.followup.send(edit_result["error"], ephemeral=True)
            return
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
                if t.name == "Bracket":
                    self.liquipedia_section = i
                    has_bracket = True
                    break
        return page_sections[self.liquipedia_section] if has_bracket else None

    def get_match_pairings(self):
        if self.tournament_type == "double elimination":
            # After testing it looks like challonge does make the matches even though it skips them
            grand_final_no_reset = False # self.tournament["grand_finals_modifier"] == "single match"
            grand_final_skipped = False # self.tournament["grand_finals_modifier"] == "skip"
            num_participants = len(self.challonge_participants)-1
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
                while (i+1)//base > 0:
                    letter_indices.insert(0,(i//base) % 26)
                    base *= 26
                letter = ""
                for j in letter_indices:
                    letter += chr(65+j)
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
                            match_mappings[challonge_identifiers[j+1]] = f"R{num_rounds}M1"
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
            self.match_mappings = match_mappings
        elif self.tournament_type == "single elimination":
            num_participants = len(self.challonge_participants)-1
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