# J.A.I.son
[Setup](#setup) | [Running bot](#running-bot)

## Setup
This was made with Python v3.12.4. It was ran in WSL2 Ubuntu, running an RTX 3070 with the latest drivers installed.

**TO AVOID DEPENDENCY ISSUES FOR LOCAL MODELS, IT IS HIGHLY ADVISED YOU ALSO USED A LINUX BASED ENVIRONMENT**

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

**IF YOU INSIST ON USING WINDOWS WITH A LOCAL AI,** you will likely need to manually install dependencies for Unsloth. Steps to do so casn be found in [this discussion](https://github.com/unslothai/unsloth/issues/210#issuecomment-1977988036) (the `Home.md` contains the exact instructions at the bottom. I could not get it to work for my hardware, but it may for yours).

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
python ./src/main.py --prompt_file=path/to/prompt.txt --name=J.A.I.son --t2t_ai=openai --model=gpt-3.5-turbo
```

Parameters:

- prompt_file: Filepath to you plaintext prompt.
- name: OPTIONAL. Name of your character you AI will be playing. Should be same as the name on Discord. Default is J.A.I.son
- t2t_ai: OPTIONAL. One of `openai` and `local` to use an OpenAI or local model respectively. Default is `openai`.
- model: OPTIONAL. Name of OpenAI or local (fine-tuned) model to use. Default is `gpt-3.5-turbo`.

For more on running with custom AI T2T models, refer to the `README.md` in `/scripts` directory.