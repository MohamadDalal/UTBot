import requests
import json
from time import perf_counter

class LiquipediaAPI():
    def __init__(self, testBot = False):
        self.session = requests.Session()
        self.base_url = "https://liquipedia.net/rocketleague/api.php?"
        self.headers = {"user-agent": "UTBot (mohammad.moddy@gmail.com)",
                        "accept-encoding": "gzip"}
        settingsPath = "tester_settings.json" if testBot else "settings.json"
        with open(settingsPath, "r") as file:
            self.settings = json.load(file)
        self.username = self.settings["LiquipediaUsername"]
        self.password = self.settings["LiquipediaPassword"]
        self.last_command_time = perf_counter()
        self.last_command_time_large = perf_counter()
        self.API_Cooldown = 5
        self.API_Cooldown_Large = 30

    def get_tokens(self, tokensType:list[str]):
        time_since_last = perf_counter() - self.last_command_time
        if time_since_last < self.API_Cooldown:
            return {"error": f"Please wait {self.API_Cooldown-time_since_last:.1f}s before using this command"}
        url = self.base_url
        tokensString = "|".join(tokensType)
        params = {"action": "query",
                  "format": "json",
                  "meta": "tokens",
                  "type": tokensString}
        response = self.session.get(url, params=params, headers=self.headers)
        print("Liquipedia get token:", response.json())
        self.last_command_time = perf_counter()
        if response.ok:
            return response.json()
        else:
            {f"error": "Token request failed. Response is {response}"}
    
    def get_user_info(self):
        time_since_last = perf_counter() - self.last_command_time
        if time_since_last < self.API_Cooldown:
            return {"error": f"Please wait {self.API_Cooldown-time_since_last:.1f}s before using this command"}
        url = self.base_url
        params = {"action": "query",
                  "format": "json",
                  "meta": "userinfo"}
        response = self.session.get(url, params=params, headers=self.headers)
        self.last_command_time = perf_counter()
        if response.ok:
            return response.json()
        else:
            {f"error": "Token request failed. Response is {response}"}

    def login(self):
        token_response = self.get_tokens(["login"])
        #if "error" in token_response.keys():
        if token_response.get("error", None) is not None:
            return token_response
        login_token = token_response["query"]["tokens"]["logintoken"]
        url = self.base_url
        params = {"action": "login",
                  "format": "json"}
        data = {"lgname": self.username,
                "lgpassword": self.password,
                "lgtoken": login_token}
        #print(login_token)
        response = self.session.post(url, data=data, params=params, headers=self.headers)
        #print("Liquipedia API login:")
        #print(response.json())
        result = response.json()["login"]["result"]
        if result == "Failed":
            return {"error": "Login failed. Check error logs"}
        elif result == "WrongToken":
            return {"error": "Login failed due to wrong token"}
        elif result == "Aborted":
            return {"error": "Login aborted. Probably because the bot is already logged in."}
        elif result == "Success":
            return response.json()
        elif not response.ok:
            {f"error": "Token request failed. Response is {response}"}
        else:
            return {"error": f"Unknown response: {response.json()}"}


    def logout(self):
        token_response = self.get_tokens(["csrf"])
        #if "error" in token_response.keys():
        if token_response.get("error", None) is not None:
            return token_response
        csrf_token = token_response["query"]["tokens"]["csrftoken"]
        if len(csrf_token) < 5:
            return {"error": "Failed to get CSRF token. Bot is probably not logged out of Liquipedia"}
        url = self.base_url
        params = {"action": "logout",
                  "format": "json"}
        data = {"token": csrf_token}
        response = self.session.post(url, data=data, params=params, headers=self.headers)
        print(response)
        print(response.json())
        #result = response.json()["login"]["result"]
        if response.ok:
            return response.json()
        else:
            {f"error": "Logout request failed. Response is {response}"}



    def get_page(self, pageID):
        time_since_last = perf_counter() - self.last_command_time
        if time_since_last < self.API_Cooldown_Large:
            return {"error": f"Please wait {self.API_Cooldown_Large-time_since_last:.1f}s before using this command"}
        url = self.base_url
        #params = bytes(f"action=query&format=json&prop=info|revisions&rvprop=content&rvslots=main&pageids={pageID}&rvsection={section}", "utf-8")
        params = {"action": "query",
                  "format": "json",
                  "prop": "revisions",
                  "rvprop": "content",
                  "rvslots": "main",
                  "pageids": pageID}
        response = requests.get(url, params=params, headers=self.headers)
        self.API_Cooldown_Large = perf_counter()
        if response.ok:
            return response.json()
        else:
            {f"error": "Getting Liquipedia page failed. Response is {response}"}

    def get_page_section(self, pageID, section):
        time_since_last = perf_counter() - self.last_command_time
        if time_since_last < self.API_Cooldown:
            return {"error": f"Please wait {self.API_Cooldown-time_since_last:.1f}s before using this command"}
        url = self.base_url
        #params = bytes(f"action=query&format=json&prop=info|revisions&rvprop=content&rvslots=main&pageids={pageID}&rvsection={section}", "utf-8")
        params = {"action": "query",
                  "format": "json",
                  "prop": "revisions",
                  "rvprop": "content|ids",
                  "rvslots": "main",
                  "pageids": pageID,
                  "rvsection": section}
        response = requests.get(url, params=params, headers=self.headers)
        self.last_command_time = perf_counter()
        if response.ok:
            return response.json()
        else:
            {f"error": "Getting Liquipedia page section failed. Response is {response}"}

    def edit_page_section(self, pageID, section, content, summary, baseRevID = None):
        #time_since_last = perf_counter() - self.last_command_time
        #if time_since_last < self.API_Cooldown:
        #    return {"error": f"Please wait {self.API_Cooldown-time_since_last:.1f}s before using this command"}
        token_response = self.get_tokens(["csrf"])
        csrf_token = token_response["query"]["tokens"]["csrftoken"]
        if len(csrf_token) < 5:
            return {"error": "Failed to get CSRF token. Bot is probably not logged into Liquipedia"}
        url = self.base_url
        params = {"action": "edit",
                  "format": "json"}
        data =   {"pageid": pageID,
                  "section": section,
                  "text": content,
                  "summary": summary,
                  "baserevid": baseRevID,
                  "bot": 1,
                  "token": csrf_token}
        response = self.session.post(url, data=data, params=params, headers=self.headers)
        #print(response)
        #print(response.headers)
        self.last_command_time = perf_counter()
        if response.ok:
            return response.json()
        else:
            {f"error": "Editing Liquipedia page failed. Response is {response}"}
        #return
    
    def refresh_session(self):
        self.session = requests.Session()
        self.last_command_time = perf_counter()
        self.last_command_time_large = perf_counter()
        return