# UTBot
Discord bot for the [UTB server](https://discord.com/invite/ztGNe8HJYC). Although it can technically be used anywhere else.

Current functionalities includes:
- Writing, editing and deleting its own messages
- Reaction role message support
- Ability to sync a Liquipedia bracket with a Challonge Bracket

## Setup
1. Clone this repository
2. Create a virtual environment using ```python -m venv venv```
3. Activate virtual environment using ```venv/scripts/activate``` for Windows or ```source venv/bin/activate``` for Linux.
4. Run ```pip install -r requirements.txt``` to install required Python libraries

## Running the bot
1. Copy the settings_template.json and rename it into settings.json
2. Fill the required tokens, usernames and passwords in settings.json or tester_settings.json
3. Activate virtual environment, if not already activated, using ```venv/scripts/activate``` for Windows or ```source venv/bin/activate``` for Linux.
4. Run the bot with ```python main.py --use-main-bot```

## Running a test instance of the bot
1. Copy the settings_template.json and rename it into tester_settings.json
2. Fill the required tokens, usernames and passwords in settings.json or tester_settings.json
3. In main.py find self.testGuilds and add the IDs of the servers you are planning to test the bot in
4. Activate virtual environment, if not already activated, using ```venv/scripts/activate``` for Windows or ```source venv/bin/activate``` for Linux.
5. Run the bot with ```python main.py```

## Enabling and disabling functionalities
If you do not want to use all the commands that come with the bot, then you can enable and disable certain functionalities by finding the setup_hook function in main.py and commenting out the commands that you do not want.