# J.A.I.son
[Setup](#setup) | [Running bot](#running-bot)

## Setup
This was made with Python v3.12.4.

It is recommended to work from within a virtual python environment. Create one using `python3 -m venv venv` or `python -m venv venv`.
Activate this virtual environment.
```bash
# Windows:
./venv/Scripts/activate
# Linux:
source venv/bin/activate
```

Install the required dependencies.
```bash
pip install -r requirements.txt
```

Create a `.env` file at the root of this project based on `.env-template`.
You can find you OpenAI API token [here](https://platform.openai.com/api-keys) as shown below:

<img src="./assets/openai_1.png" alt="openai api token location 1" height="200"/>
<img src="./assets/openai_2.png" alt="openai api token location 2" height="200"/>

You can find you Discord Bot token from the [dashboard](https://discord.com/developers/applications) after creating a bot as shown below:

<img src="./assets/discord_1.png" alt="discord bot token location" height="200"/>

Ensure your bot has the right OAuth2 permissions when it joins your server (Scope -> Bot, Bot Permissions -> Administrator if unsure).

## Running bot

To run, simply use the following from the project root:
```bash
python ./src/main.py
```

https://github.com/unslothai/unsloth/issues/210