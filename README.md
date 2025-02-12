# J.A.I.son

[Setup](#setup) | [Linking Twitch](#linking-twitch) | [Customizing responses](#customizing-t2t) | [Customizing voice](#customizing-voice) | [Configuration](#configuration) | [Running bot](#running-bot)

## Setup
This was made with Python v3.12.18. It was ran in WSL2 Ubuntu and Windows, running an Intel CPU with an RTX 4070 with the latest drivers installed. This is unlikely to be runnable for non-Nvidia systems without stripping code in its current state.

### Step 1: Before starting

**TO AVOID DEPENDENCY ISSUES, IT IS HIGHLY ADVISED TO USE CONDA FOR YOUR VIRTUAL ENVIRONMENT**
1. Install [CUDA](https://developer.nvidia.com/cuda-toolkit)
2. Install [conda](https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html) for managing virtual environment (Miniconda is recommended)

### Step 2: Setting up plugins
You can find plugins for components (things that generate responses) and applications (things that use Project J.A.I.son) in the [Discord](https://discord.gg/Z8yyEzHsYM) or on my GitHub. These are community projects, so anyone can make and upload their own plugins. Each one has their own setup guide, so follow that.

To link this project to components, list the available components in your plugins config (`./configs/plugins/example.yaml` by default). Endpoint is for if you deploy the plugin prior to running this project (saves development time, deploy on another machine, and doesn't shut down when this project terminates), or you can specify the path to the directory (this project will automatically boot it up for you, but it takes some time and can only be deployed on the same machine).

You will need STT, T2T, TTSG, and TTSC components for this project to work currently. Here are some that I've made:

- [STT Local OpenAI Whisper](https://github.com/limitcantcode/stt-openai-whisper-lcc-comp) (Recommended for setup)
- [T2T OpenAI API](https://github.com/limitcantcode/t2t-openai-lcc-comp) (Recommended for setup)
- [T2T Local Unsloth](https://github.com/limitcantcode/t2t-unsloth-lcc-comp)
- [TTSG OpenAI API](https://github.com/limitcantcode/ttsg-openai-lcc-comp) (Recommended for setup)
- [TTSG Speech Synthesis](https://github.com/limitcantcode/ttsg-pytts-lcc-comp)
- [TTSC RVC Project](https://github.com/limitcantcode/ttsc-rvc-proj-lcc-comp)
- [TTSC No Changer](https://github.com/limitcantcode/ttsc-no-changer-lcc-comp) (Recommended for setup)

To link this project to applications, simply run those applications separately after jaison-core is running. jaison-core does not manage those applications as of writing. Here are some that I've made:

- [Discord Bot](https://github.com/limitcantcode/app-jaison-discord-lcc)
- [Twitch Events and Chat](https://github.com/limitcantcode/app-jaison-twitch-lcc)
- [VTube Studio Animation Hotkeyer](https://github.com/limitcantcode/app-jaison-vts-hotkeys-lcc)

## Step 3:Configuration
You can find jaison-core config files under `./configs/jaison`. Below is a description of the values:

- prompt_default_file: (str) A prompt filename within `./prompts/production`. Must be in this file and is just the file name.
- prompt_params: (dict) Map of variables in a prompt to their actual value (look at a prompt file to see what variables exist)
- prompt_name_translation_file: (str) A name translation filename within `./configs/translations`. Must be in this file and is just the file name.
- prompt_convo_retention_length: (int) Length of main conversation history to keep for generating T2T responses
- plugins_config_file: (str) File name under `./configs/plugins`. Must be in this file and is just the file name.
- active_plugins: (List[str]) List of component plugins to use. Can only have 1 of each type as of writing. Should be the id as found in that component's `metadata.yaml`.
- web_port: (int) Port to serve as application API and websocket server

You can also add name aliases (replacing usernames with an actual name) by adding to the config in `./configs/translations`

### Step 4: Setting up environment
It is recommended to work from within a conda virtual environment. Assuming you are using conda:

Create and activate environement. Install dependencies in this order. You will need your machine-specific command to install pytorch from [here](https://pytorch.org/get-started/locally/).
```bash
conda create -n jaison-core python=3.12 ffmpeg cudatoolkit -c pytorch -y
conda activate jaison-core
pip install -r requirements.txt
```

## Running bot
### Step 1: Ensure dependency apps are running
1. Ensure any plugins specified as endpoints are up and running

### Step 2: Ensure your using the right environment
Ensure you are using the right environment:
```bash
conda activate jaison-core
```

### Step 3: Start running
To run, simply use the following from the project root:
```bash
python ./src/main.py --config=config.json
```

To get a full list of options, run:
```bash
python ./src/main.py --help
```

## Logging
Logs are stored in `./logs` by default. Changing the log directory (an option when starting the project) requires the new directory to subfolders `sys`, `dialog`, and `response`.

`sys` contains system logs for each of the main application, VTube studio plugins, and the Discord bot. Only certain logs are sent to the console as well, but all logs are sent to files (except for those generated by dependencies such as Discord.py).

`dialog` contains the entire conversation history in the same format used for generating T2T responses. This is useful for creating new datasets and monitoring conversations.

`response` contains entries immediately usable to train T2T AI models. These contain the time, system prompt, user prompt, and generated response for every response made by the T2T model in use. This is useful for cherrypicking favorable responses to retrain the model on.