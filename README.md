# J.A.I.son
[Setup](#setup) | [Training voice](#training-voice) | [Running bot](#running-bot)

## Setup
This was made with Python v3.12.4. It was ran in WSL2 Ubuntu, running an RTX 3070 with the latest drivers installed.

**TO AVOID DEPENDENCY ISSUES FOR LOCAL MODELS, IT IS HIGHLY ADVISED YOU ALSO USED A LINUX BASED ENVIRONMENT**

### Step 1: Before starting
If you intend to run models locally, please ensure you are able to run [CUDA](https://developer.nvidia.com/cuda-toolkit) on you machine and have it installed (this should come with [NVidia drivers](https://www.nvidia.com/en-us/drivers/) by default).

If you don't have the means to run CUDA, then it is advised you use AI services such as [OpenAI](https://platform.openai.com/docs/overview).

### Step 2: Setting up voice
In order to make use of TTS in voice chat as well, you will firstly need something to generate speech.

The following is for old-school TTS generation, and is required whether or not you use it. In Windows, this is built-in with [SAPI5](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms723627(v=vs.85)). In Linux, you will need to install [eSpeak NG](https://github.com/espeak-ng/espeak-ng/blob/master/docs/guide.md).

The following is for AI TTS generation. It is recommended you use OpenAI services for this once again. This repo currently does not have an option for locally ran TTS AI options, however you may add them by implementing the TTS generation classes.

Lastly, **YOU WILL NEED THE [RVC-PROJECT](https://github.com/limitcantcode/Retrieval-based-Voice-Conversion-WebUI)**. Please refer to ["Training voice"](#training-voice) for more details.

### Step 3: Setting up this repo
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

## Training T2T
For more on running with custom AI T2T models, refer to the `README.md` in `/scripts` directory.

## Training voice
We don't train direct T2T AI models, but rather AI voice changers using the [RVC-PROJECT](https://github.com/limitcantcode/Retrieval-based-Voice-Conversion-WebUI). You can find a translation of their docs under the `/docs/` directory. Follow the instructions to setup the project, run the web UI, and train a model with you desired voice. **YOU WILL NEED TO BE ABLE TO RUN CUDA TO TRAIN A VOICE**. It is recommended you have a GPU with at least 8GB of dedicated VRAM (not shared or combined with system RAM). If you encounter `CUDA out of memory` errors or something similar, try training smaller models. An RTX 3070 with 8GB or VRAM could only train a v1 model with pitch at 40k sample rate, using both rvmpe_gpu and rvmpe, on a batch size of 1 with no caching. You want to just train a model (be patient after clicking the button, it can take a couple minutes to kick in) and you may ignore training a feature index. If you still have trouble training due to memory, you can swap the pretrained base models from `f0X40k.pth` to just `X40k.pth` where X is either `D` or `G` accordingly.

## Running bot
### Step 1: Prerequisites
If you followed ["Training voice"](#training-voice), you will have installed the [RVC-PROJECT](https://github.com/limitcantcode/Retrieval-based-Voice-Conversion-WebUI) and trained a voice model. In the same way you ran the web-UI to train, run the web-UI to start the voice-conversion server using `python ./infer-web.py`.

### Step 2: Setting up config
Change the values of the config under `./configs` to match your system. `example.json` briefly shows the values that should be there and `default.json` is what I personally used to run this project. Below is a description of the values:

- character_name: (str) Name of your bot and the name it will assume.
- prompt_filepath: (str) Filepath to the prompt text file you want to use. Some may be found under `./prompts`.
- t2t_host: (str) One of `local` or `openai` if you want to run an Unsloth model locally or use OpenAI services respectively.
- t2t_model: (str) Name of OpenAI (checkpoint) model you want to use or name of Unsloth model as you trained it.
- tts_host: (str) One of `old` or `openai` if you want to use old-school TTS synthesis like SAPI or espeak or if you want to use OpenAI's AI TTS service respectively.
- tts_output_filepath: (str) Filepath to where bot should output latest generated TTS. Will be used as intermediate to generate speech initially and then to convert into desired voice. Requires directory to exist (file doesn't have to exist yet).
- stt_output_filepath: (str) Filepath to most recent audio to be transcribed and sent to t2t.
- rvc_model: (str) Name of RVC voice model. Is the name you chose when training (so name without the `.pth`).
- rvc_url: (str) URL to your hosted RVC web UI. Typically http://localhost:7865
- server_id: (null or number) Discord server/guild id.

### Step 3: Start running

To run, simply use the following from the project root:
```bash
python ./src/main.py --config=path/to/config.json
```