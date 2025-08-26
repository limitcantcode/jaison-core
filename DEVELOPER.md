# Developer Guide

## Table of contents

- [Community](#community)
- [Configuration](#configuration)
    - [Misc](#misc)
    - [Operations](#operations)
        - [STT](#stt)
        - [T2T](#t2t)
        - [TTS](#tts)
        - [FILTER_AUDIO](#filter_audio)
        - [FILTER_TEXT](#filter_text)
        - [EMBEDDING](#embedding)
- [REST API Spec](#rest-api)
- [Websocket Events](#websocket-events)
    - [Shared](#shared)
    - [Job-Specific](#job-specific)
- [Creating Custom Integrations](#creating-custom-integrations)
    - [Some Definitions](#some-definitions)
    - [Making Operations](#making-operations)
    - [Adding Managed Processes](#adding-managed-processes)
    - [Making Applications](#making-applications)
    - [Extending Configuration](#extending-configuration)
    - [Extending API](#extending-rest-api)
- [Known Issues](#known-issues)

## Community

**Join the [Discord](https://discord.gg/Z8yyEzHsYM) for discussions related to this project!**

## Configuration

[Take me to the top!](#developer-guide)

An [example configuration](configs/example.yaml) is provided. Example prompts can be found under [`prompts`](prompts) Depending on which integrations are configured for use, additional setup is required.

### Misc

[Take me to the top!](#developer-guide)

#### Prompting

Find prompt files for personality and scenario under `prompts/characters` and `prompts/scenes` respectively. There are also general instructions, but you shouldn't need to edit this. Place your prompt text files in these directories.

For the configuration file:

- `instruction_prompt_filename`: (str) Filename of prompt under `prompts/instructions` (excluding `.txt`)
- `character_prompt_filename`: (str) Filename of prompt under `prompts/characters` (excluding `.txt`)
- `scene_prompt_filename`: (str) Filename of prompt under `prompts/scenes` (excluding `.txt`)
- `character_name`: (str) Name of character
- `history_length`: (int) Number of lines in script to retain

There is also `name_translations` for translating a user to another name.
```yaml
name_translations:
    old-name: new-name
```

### Operations

[Take me to the top!](#developer-guide)

- [Setup](#setup)
    - [Azure](#azure)
    - [Fish](#fish)
    - [Kobold](#kobold)
    - [OpenAI](#openai)
    - [RVC](#rvc)

- [stt](#stt)
    - [azure](#azure-1)
    - [fish](#fish-1)
    - [kobold](#kobold-1)
    - [openai](#openai-1)
- [t2t](#t2t)
    - [kobold](#kobold-2)
    - [openai](#openai-2)
- [tts/mcp](#tts/mcp)
    - [azure](#azure-2)
    - [fish](#fish-2)
    - [kobold](#kobold-3)
    - [melo](#melo)
    - [openai](#openai-3)
    - [pytts](#pytts)
- [filter_audio](#filter_audio)
    - [pitch](#pitch)
    - [rvc](#rvc-1)
- [filter_text](#filter_text)
    - [chunker_sentence](#chunker_sentence)
    - [filter_clean](#filter_clean)
    - [emotion_roberta](#emotion_roberta)
    - [mod_koala](#mod_koala)
- [embedding](#embedding)
    - [openai](#openai-4)

Operations listed in config are loaded by default when starting `jaison-core`. Enabled operations are listed under property `operations`. For example:

```yaml
operations: 
- role: stt
  id: fish
- role: t2t
  id: openai
- role: filter_text
  id: filter_clean
- role: filter_text
  id: chunker_sentence
- role: tts
  id: azure
```

This loads `fish` for `STT`, `openai` for `T2T`, all of `filter_clean` and `chunker_sentence` for `filter_text`, and `azure` for `TTS`. These are loaded in order. Filters are applied in the order they were loaded, with the earliest applying first before the rest. For non-filter operations, only one can be specified, otherwise older ones are overwritten.

Each operation may have its own configuration depending on the specific operation. For example:

```yaml
operations: 
- type: tts
  id: azure
  azure_ttsg_voice: "en-US-AshleyNeural"
```

Below is a list of all available operations and their respective configuration for each type. There are also common setup guides for specific platforms.

#### Setup

[Take me to the top!](#developer-guide)

##### Azure

To use Azure Speech Services, you will need an API key and know your region.

1. Go to [Azure](https://azure.microsoft.com/en-ca)
2. Make an account or sign in
3. Search for ["Resource groups"](https://portal.azure.com/#browse/resourcegroups)
4. Create a new one
    - Default subscription tier for new accounts is free. No need to change
    - Pick a region close to you
5. Open the resource group
6. Click `Create` and search for "SpeechServices"
7. Create a new [Speech service](https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/CognitiveServicesHub/~/SpeechServices)
    - Select the resource group you just made
    - Pick a region close to you
    - Pick "Standard S0" for free tier pricing
8. Open newly created Speech service
9. Scroll to bottom of overview and copy any `KEY` and the `Location/Region`
10. In the main project, copy `.env-template` or one created prior
11. Paste what you just copied into `AZURE_API_KEY` and `AZURE_REGION` respectively after the "="

##### Fish

To use Fish Audio, you will need an API key. Premium tier **IS NOT** necessary, however you will still need to pay for what you use.

1. Go to [Fish Audio](https://fish.audio/auth/)
2. Make an account or sign in
3. Navigate to "API" tab
4. Get API credits if you don't have any 
5. Go to API Keys
6. Click "Create Secret Key"
    - Set a long expiry date or have it never expires. When it expires, you will need to replace the old key with a new one
7. Copy the "Secret Key" you just generated from the "API List"
8. In the main project, copy `.env-template` or one created prior
9. Paste what you just copied into `FISH_API_KEY` after the "="

##### Kobold

To use Kobold CPP, You will need the application and set it up.

1. Download [KoboldCPP](https://github.com/LostRuins/koboldcpp/releases)
    - Get the right one for your system
    - Windows users will want one that ends in `.exe`
    - If you have an NVidia GPU, get one with CUDA (`cu12`, `cuda1150`, `cuda1210`)
2. Move the downloaded application to this project under `models/kobold`
3. Run this application to bring up its setup interface
4. Download the model(s) you want to use as detailed [here](https://github.com/LostRuins/koboldcpp?tab=readme-ov-file#Obtaining-a-GGUF-model)
    - For STT, download any of the `.bin` [here](https://huggingface.co/koboldcpp/whisper/tree/main) Generally, `base` and `small` are good enough
5. Move the downloaded model(s) into the same `models/kobold` folder
6. Configure your KoboldCPP through the interface
    - Select a fitting preset (CuBLAS for NVidia GPUs. Vulkan is good for most)
    - Setup T2T model in "Model Files" if applicable
    - Setup STT and TTS model in "Audio" if applicable
    - Everything doesn't need to be adjusted
7. Click "Save" and save to same `models/kobold` folder using any name
8. Update this project's configuration file
    - `kobold_filepath` with full filepath to Kobold application
    - `kcpps_filepath` with full filepath to saved Kobold config file
    - If on windows, make sure each `\` is `\\` in the path as shown in `example.yaml`

##### OpenAI

To use OpenAI (not some other OpenAI-like API), you will need an API key. If you want to use another OpenAI-like API, see the statement after the main set of steps here.

1. Go to [OpenAI Dashboard](https://platform.openai.com/)
2. Make an account or sign in
3. Navigate to "Profile" then "Secrets"
6. Create and copy the key
8. In the main project, copy `.env-template` or one created prior
9. Paste what you just copied into `OPENAI_API_KEY` after the "="

For other OpenAI-like APIs, they generally have their own setup instructions. Usually this involves replacing the API key above with theirs. You will additionally need to update the base URL inside this project's configuration file. These are listed as `openai_t2t_base_url` for example. Each of `STT`, `T2T`, and `TTS` have separately configurable base URLs.

##### RVC

To use RVC, you will need the download all necessary assets and create (or find) a voice model.

1. Ensure you have Git and GitLFS on your system
2. Clone the [RVC Project](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) with `git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git`
3. Inside the project you just cloned, run the command `python tools/download_models.py`
4. Confirm you have downloaded the models by looking in `assets/hubert` and see if you have a file `hubert_base.pt` (**NOT** `hubert_inputs.pth`)
5. If downloaded, copy all the contents from that project's `assets` folder into this projects `assets/rvc`
6. Train or find an RVC voice model. Training is recommended only if you have a GPU with at least 8GB of VRAM. NVidia GPUs are easier to setup for training. You may the project you took the `assets` file of to train a model using their web UI. Setup for that project can be found [here](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/main/docs/en/README.en.md)
7. Copy the model into this project
    - `.pth` into `assets/rvc/weights`. If trained, this can be found under `assets/weights` of the other project
    - index folder containing a `.index` file into `models/rvc`. If trained, this can be found under `logs` of the other project. If you only have the `.index` file and not a folder, make a folder with the same name as your `.pth` file
8. In the main project, copy `.env-template` or one created prior, and ensure it has the section for RVC. **DO NOT MODIFY THESE**

#### stt

[Take me to the top!](#developer-guide)

##### azure

- **compatibility** -> all
- **paid** -> no

Use [Azure Speech Services](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/index-speech-to-text) for speech-input.

Configuration:
- `language` (str) Input speech [language](azure_stt_language)

##### fish

- **compatibility** -> all
- **paid** -> yes

Use [Fish Audio](https://fish.audio/) for speech-input.

No additional configuration

##### kobold

- **compatibility** -> all
- **paid** -> no

Use [KoboldCPP](https://github.com/LostRuins/koboldcpp) for speech-input.

Additional configuration
- `suppress_non_speech` (bool) for skipping non-speech sounds
- `langcode` (str) for code of input language

##### openai

- **compatibility** -> depends
- **paid** -> depends

Default to use [OpenAI's service](https://platform.openai.com/docs/overview), which is compatible with all but paid. Can also be used with applications/services that have OpenAI-like API such as Ollama.

Configuration:
- `base_url` (str) for specifying endpoint (OpenAI or some other application/service)
- `model` (str) model to use
- `language` (str) [language](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py)

#### t2t/mcp

[Take me to the top!](#developer-guide)

##### kobold

- **compatibility** -> limited
- **paid** -> no

Direct support for models on [KoboldCPP](https://github.com/LostRuins/koboldcpp). More flexible samplers than OpenAI-like APIs.

Configuration:
- `max_context_length` (int) max context length of model
- `max_length` (int) max length allowable for model
- `quiet` (bool) quiet output
- `rep_pen` (float) sampler
- `rep_pen_range` (int) sampler
- `rep_pen_slope` (int) sampler
- `temperature` (float) sampler
- `tfs` (int) sampler
- `top_a` (int) sampler
- `top_k` (int) sampler
- `top_p` (float) sampler
- `typical` (int) sampler

##### openai

- **compatibility** -> depends
- **paid** -> depends

Default to use [OpenAI's service](https://platform.openai.com/docs/overview), which is compatible with all but paid. Can also be used with applications/services that have OpenAI-like API such as Ollama.

Configuration:
- `base_url` (str) for specifying endpoint (OpenAI or some other application/service)
- `model` (str) for model ID
- `temperature` (float) for adjusting temperature
- `top_p` (float) for adjusting top P
- `presence_penalty` (float) for adjusting presence penalty
- `frequency_penalty` (float) for adjusting frequency penalty

#### tts

[Take me to the top!](#developer-guide)

##### azure

- **compatibility** -> all
- **paid** -> no

Use [Azure Speech Services](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/index-text-to-speech) for natural sounding synthesized speech.

Configuration:
- `voice` (str) ID of void from [voice gallery](https://speech.microsoft.com/portal/voicegallery) (ID used in their sample code for `speech_synthesis_voice_name`)

##### fish

- **compatibility** -> all
- **paid** -> yes

Use [Fish Audio](https://fish.audio/) for voice-cloned text-to-speech.

Configuration:
- `model_id` (str) for voice model ID
- `backend` (str) for model to use
- `normalize` (bool) for normalizing input message for clearer pronunciation
- `latency` (str) one of "normal" (stable) or "balanced" (faster but choppy)

##### kobold

- **compatibility** -> limited
- **paid** -> no

Use [KoboldCPP](https://github.com/LostRuins/koboldcpp) for TTS. Mostly for completion sake, and not recommended for use.

Configuration:
- `voice` (str) voice to use

##### melo

- **compatibility** -> all
- **paid** -> no

Use [MeloTTS](https://github.com/myshell-ai/MeloTTS) for local AI TTS. This is recommended choice for fast, consistent latency and control over the voice if you know what your doing.

Configuration:
- `config_filepath` (str) Filepath to model config
- `model_filepath` (str) Filepath to model
- `speaker_id` (str) Name of speaker in model
- `device` (str) Pytorch device (cpu or cuda)
- `language` (str) Language code
- `sdp_ratio` (float) Ratio for expressiveness
- `noise_scale` (float) Noise seeding input
- `noise_scale_w` (float) Noise width seeding input
- `speed` (float) Speed of final speech

##### openai

- **compatibility** -> depends
- **paid** -> depends

Default to use [OpenAI's service](https://platform.openai.com/docs/overview), which is compatible with all but paid. Can also be used with applications/services that have OpenAI-like API.

Configuration:
- `base_url` (str) for specifying endpoint (OpenAI or some other application/service)
- `voice` (str) for voice name
- `model` (str) for voice model

##### pytts

- **compatibility** -> all
- **paid** -> no

Use system's speech synthesizer (SAPI for Windows, ESpeak for Linux) to generate speech.

Configuration:
- `voice` (str) for voice ID (a list of these is printed on start when configured to be used)
- `gender` (str) for voice gender if applicable

#### filter_audio

[Take me to the top!](#developer-guide)

##### pitch

- **compatibility** -> all
- **paid** -> no

Pitch generated audio up and down a number of semi-tones

Configuration:
- `pitch_amount` (int) pitch shift in semi-tones

##### rvc

- **compatibility** -> limited
- **paid** -> no

Use voice changers trained using [RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI).

Configuration:
- `voice` (str) for model name
- `f0_up_key` (int) for changing voice pitch
- `f0_method` (str) for generation method
- `f0_file` (str) for frequency filepath
- `index_file` (str) for index filepath
- `index_rate` (float) for index rate
- `filter_radius` (int) 
- `resample_sr` (int) for resampling audio to another sample rate
- `rms_mix_rate` (int)
- `protect` (float)

#### filter_text

[Take me to the top!](#developer-guide)

##### chunker_sentence

- **compatibility** -> all
- **paid** -> no

Accumulate output from T2T model into sentences before passing them down the pipeline.

No additional configuration

##### emotion_roberta

- **compatibility** -> all
- **paid** -> no

Use [SamLowe/roberta-base-go_emotions](https://huggingface.co/SamLowe/roberta-base-go_emotions) to castegorize response into an emotion.

No additional configuration

##### filter_clean

- **compatibility** -> all
- **paid** -> no

Accumulate output from T2T model into sentences before passing them down the pipeline.

No additional configuration

##### mod_koala

- **compatibility** -> limited
- **paid** -> no

Use [Koala/Text-Moderation](https://huggingface.co/KoalaAI/Text-Moderation) to categorize and filter offensive responses.

No additional configuration

#### embedding

[Take me to the top!](#developer-guide)

##### openai

- **compatibility** -> all
- **paid** -> yes

Generate embeddings using OpenAI embedding models

Configuration:
- `base_url` (str) URL to openai-compatible API endpoint
- `model` (str) Name of model to use



## REST API

[Take me to the top!](#developer-guide)

API spec is made with OpenAPI 3.1.0 standard and can be found [`api.yaml`](api.yaml).

Please read the description of the endpoint you are interested in. If it specifies use of websockets to communicate status or results, you will need to setup a websocket for updates on your request. Using such REST API endpoints are successful when they successfully queue a job and doesn't mean the job itself was successful.

Please see [Websocket Events](#websocket-events) for websocket messages related to each job.

## Websocket Events

[Take me to the top!](#developer-guide)

Websockets are used for several reasons

- Ensure all applications are notified of changes even if they didn't request it
- Enable long-lived requests such as responses which may take a few seconds to finish
- Real-time feedback and streaming of responses to reduce latency
- Allow predictable, sequential behavior and locking state during response generation

While each job is unique, they follow similar patterns in terms of generated events. The following are generated in order

1. Job start
2. Job-specific events (as many as it needs)
...
3. One of 2 events
    - Job finish
    - Job cancelled

Each job is ran sequentially in the order they were queued. Events are also sent in order they were generated. You can expect to receive all events in this predictable order and process 1 job's events at a time. 

These events are detailed in the following sections.

### Shared

[Take me to the top!](#developer-guide)

#### Some Common Enums and Definitions

##### Job Types

- `response`: `POST /api/response`
- `context_clear`: `DELETE /api/context`
- `context_request_add`: `POST /api/context/request`
- `context_conversation_add_text`: `POST /api/context/conversation/text`
- `context_conversation_add_audio`: `POST /api/context/conversation/audio`
- `context_custom_register`: `POST /api/context/custom`
- `context_custom_remove`: `DELETE /api/context/custom`
- `context_custom_add`: `PUT /api/context/custom`
- `operation_load`: `POST /api/operations/load`
- `operation_reload_from_config`: `POST /api/operations/reload`
- `operation_unload`: `POST /api/operations/unload`
- `operation_use`: `POST /api/operations/use`
- `config_load`: `PUT /api/config/load`
- `config_update`: `PUT /api/config/update`
- `config_save`: `POST /api/config/save`

##### Error Types
- `operation_unknown_type`: Specified an unknown operation type
- `operation_unknown_id`: Specified an unknown operation ID for that type
- `operation_duplicate`: Tried loading a filter that's already loaded
- `operation_unloaded`: Tried using a filter that's not loaded
- `operation_active`: Tried activating an operation that's already active (should never occur, lmk if it does)
- `operation_inactive`: Tried deactivating an operation that's already inactive, or using an inactive operation (should never occur, lmk if it does)
- `config_unknown_field`: Tried updating or loading a configuration with an invalid field
- `config_unknown_file`: Tried loading a configuration file that doesn't exist
- `job_unknown`: Tried starting an invalid job type(should never occur, lmk if it does)
- `job_cancelled`: Job was cancelled via the REST API

#### Job Start

Signify the start of a job's processing and the arguments provided. The arguments provided are what's included in the original REST API call's body if it was valid to create a job in the first place. For `audio_bytes`, due to size, it is simply returned as a boolean indicating if it was included.

```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "start": { "input argument keyword": "input argument value", ... }
    }
}
```

#### Job Finish

Signify the successful end of a job's processing.

```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "finished": true,
        "success": true
    }
}
```

#### Job Cancelled

Signify the unsuccessful end of a job's processing. This may be due to some error during processing, or the result of an application cancelling the job through the REST API.

These will only be emitted once the job has started processing, even if the job was cancelled before then. Therefore, if an application cancels a job, it won't receive the cancelled event until all jobs prior have finished processing and this is put on next. The job is then cancelled immediately and all are notified.

```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "finished": true,
        "success": false,
        "result": {
            "type": "error type",
            "reason": "error message"
        }
    }
}
```

### Job-Specific

[Take me to the top!](#developer-guide)

#### `response`

Events contain details about generation and are sent in order they appear below.


Immediately after LLM generation but before text filters
```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "finished": false,
        "result": {
            "instruction_prompt": "Instructions for the LLM",
        }
    }
}
```
```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "finished": false,
        "result": {
            "history": [
                {"type": "raw", "message": "Example of raw user input"},
                {"type": "request", "time": 1234, "message": "Example of request message"},
                {"type": "chat", "time": 1234, "user": "some user or AI name", "message": "Example of chat message"},
                {"type": "tool", "time": 1234, "tool": "some tool name", "message": "Example of tool result"},
                {"type": "custom", "time": 1234, "id": "some custom context id", "message": "Example of context"}
            ],
        }
    }
}
```
```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "finished": false,
        "result": {
            "raw_content": "Response from LLM before application of text filters",
        }
    }
}
```

The following events are looped (once reaching end, loops back to this first event and continuing if more is generated).

This event's results depend on the filters applied. Some operations such as `emotion_roberta` augment the result by adding `emotion` alongside the `content` property for example.
```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "finished": false,
        "result": {
            "content": "Response from LLM after filters",
            "other augmented properties": "their value",
            ...
        }
    }
}
```

If audio is included, can produce multiple (each chunk for the next packet of audio):
```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "finished": false,
        "result": {
            "audio_bytes": "base64 utf-8 encoded bytes",
            "sr": 123,
            "sw": 123,
            "ch": 123
        }
    }
}
```

#### `context_clear`

No job-specific events.

#### `context_request_add`

Events contain details context added. Only one is generated.

```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "finished": false,
        "result": {
            "timestamp": 12345,
            "content": "content as given in arguments",
            "line": "[request]: as it appears in the script"
        }
    }
}
```

#### `context_conversation_add_text`

Events contain details context added. Only one is generated.

```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "finished": false,
        "result": {
            "user": "name of user associated with line",
            "timestamp": 12345,
            "content": "content as given in arguments",
            "line": "[line]: as it appears in the script"
        }
    }
}
```

#### `context_conversation_add_audio`

Events contain details context added. Only one is generated.

```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "finished": false,
        "result": {
            "user": "name of user associated with line",
            "timestamp": 12345,
            "content": "content as given in arguments",
            "line": "[line]: as it appears in the script"
        }
    }
}
```

#### `context_custom_register`

No job-specific events.

#### `context_custom_remove`

No job-specific events.

#### `context_custom_add`

Events contain details context added. Only one is generated.

```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "finished": false,
        "result": {
            "timestamp": 12345,
            "content": "content as given in arguments",
            "line": "[line]: as it appears in the script"
        }
    }
}
```

#### `operation_load`

Events contain details of loaded operation. One is generated per operation listed.

```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "finished": false,
        "result": {
            "type": "operation type",
            "id": "operation id"
        }
    }
}
```

#### `operation_reload_from_config`

No job-specific events.

#### `operation_unload`

Events contain details of unloaded operation. One is generated per operation listed.

```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "finished": false,
        "result": {
            "type": "operation type",
            "id": "operation id"
        }
    }
}
```

#### `operation_use`

Events contain results from using operation. Multiple of these can be generated if output is streamed. Resulting chunk differs between operations, but usual behavior is generalized under [Creating Custom Integrations - Operations](#creating-custom-integrations).

```json
{
    "status": 200,
    "message": "job type",
    "response": {
        "job_id": "job uuid generated when first created",
        "finished": false,
        "result": { "output chunk property": "output chunk value" }
    }
}
```

#### `config_load`

No job-specific events.

#### `config_update`

No job-specific events.

#### `config_save`

No job-specific events.


## Creating Custom Integrations

[Take me to the top!](#developer-guide)

In case you really want to use an unsupported service, directly implement a model into jaison-core, or just make and share an external application with jaison-core as it's backend, this guide should help you navigate and work on the code like Limit does.

- [Some Definitions](#some-definitions)
- [Making Operations](#making-operations)
    - [Implementing an Operation](#implementing-an-operation)
    - [Connecting an Operation for Use](#connecting-an-operation-for-use)
- [Adding Managed Processes](#adding-managed-processes)
    - [Implementing a Process](#implementing-a-process)
    - [Connecting a Process for Use](#connecting-a-process-for-use)
    - [Connecting with Operations for Management](#connecting-with-operations-for-management)
- [Adding MCP Servers](#adding-mcp-servers)
- [Making Applications](#making-applications)
- [Extending Configuration](#extending-configuration)
- [Extending API](#extending-rest-api)
    - [Non-Job-Based Endpoints](#non-job-based-endpoints)
    - [Job-Based Endpoints](#job-based-endpoints)

### Some Definitions

[Take me to the top!](#developer-guide)

Operation - A unit of compute that assists in creating or modifying a response.

Active operation - Operation that has started and can be used.

Inactive operation - Operation that has never been started or has closed and can't be used.

Process - An program that has to run in a separate process from jaison-core. When referred to in this context, it generally means jaison-core is responsible for starting and stopping this process (it is a child process to jaison-core and not another server you manually booted up on the side).

Application - A program that uses the REST API or websocket server of jaison-core.

Application layer - Main implementation of functionality for all REST API endpoints. `utils/jaison.py` is the file Limit refers to as the "application layer" whereas operations are seen as the "hardware layer".

Event - Message sent through a websocket from jaison-core to an application

Job - Special request created through the REST API. These are tasks to be completed after all previously created tasks are complete. They run one at a time and wait in a queue to be processed next. They outlive the original API request that made them, and they communicate back their results and status through websockets. Each job is associated with a single function in the application layer. Simply, they are queued functions that will produce events.

### Making Operations

[Take me to the top!](#developer-guide)

Everything you need to make a basic operation is in `utils/operations`.

To make a new operation, make a new file in the directory corresponding to your operation type. In this file, you will be implementing the base operation of that type. You can find that in the `base.py` in that type's directory.

#### Implementing an Operation

There are 2 inherited attributes:
`op_type`: (str) operation type specifier
`op_id`: (str) the operation id you specified in `__init__`

There are 6 functions to note:

`__init__(self)`: must be implemented with no additional arguments. In here, you must also call `super().__init__(op_id)` where `op_id` will be the id of this operation, unique to the one's of the same type (there are multiple `kobold`, but each `kobold` operation is in a different type). You can initialize attributes in here, but this is only ran once and is synchronous.

`__call__`: **DO NOT IMPLEMENT**

`async start(self)`: This is where you'll actually setup your operation. Make any connections, asynchronous calls, etc. This will be called every time the operation is loaded. Don't worry about closing before starting as it's handled automatically. Remember to call `await super().start()` at the beginning.

`async close(self)`: This is where you'll stop your operation. Close any connections and clean it up. This is what's called before every `start` if the operation has already started. Remember to call `await super().close()` at the beginning.

`async _parse_chunk(self, chunk_in)`: Extract information from input dictionary `chunk_in`, validate, and use as input to `_generate`. There is a default one already implemented, but if you need to parse additional fields not parsed by default (such as emotion for an emotion-based tts), then reimplement it with the same spec as the base.

`async _generate(self, **kwargs)`: Must be implemented. Instead of returning, use `yield` even if you only use it once. Results from `_parse_chunk` are used as `kwargs` here. Perform the calculation and `yield` the dictionary that contains at least the fields specified in `base.py`.

#### Connecting an Operation for Use

All operations are accessed from the `OperationManager` located in `utils/operations/manager.py`. Everything here is dynamic except for function `loose_load_operation`. This is what you'll be modifying.

1. Find function `loose_load_operation`
2. Find the case that matches your operation's type
3. Extend the if-else block
    - the `op_id` you match should be the one you initialized before, and is also the id you use in configuration
    - add your import statement here, not globally
    - return an instance like the rest of them

You can now use your custom operation.

### Adding Managed Processes

[Take me to the top!](#developer-guide)

#### Implementing a Process

If you have an operation that depends on another running application, you can have jaison-core automatically start and stop that application whenever that operation is in use or not. This is done for KoboldCPP, and can be done for your application as well as long as you can start and get an instance of that process in Python (see `utils/processes/processes/koboldcpp.py` for example).

Code for managing processes can be found in `utils/processes`. Process specific code is in `utils/processes/processes`. You will need to implement `BaseProcess` found in `utils/processes/base.py`.

You only need to implement 2 functions. All else should not be modified. Check the base implementation to know which these are.

`__init__`: Be sure to call `super().__init__(process_id)` where `process_id` is the a unique name chose purely for logging purposes.

`async reload(self)`: Starting logic. You will need to start the process and save it to the `process` attribute. You can also save the `port` is applicable for use in your operations.

#### Connecting a Process for Use

All processes are accessed through the `ProcessManager` found in `utils/processes/manager.py`. We need to add it here so it's exposed for use.

1. Open `utils/processes/manager.py`
2. Add an entry to the `ProcessType` enum for your process.
3. Create a new case in function `load`
    - Import your process in there
    - Add a new instance with the enum as the key
    - asynchronously call `reload` on that instance

#### Connecting with Operations for Management

The process does not start until an operation demands it. Likewise, it does not stop until there are no more operations that use it. To setup this relationship, we need to know 2 functions from the `ProcessManager`:

`link(link_id, process_type)`: Link an operation to that process. This lets the process know it's being used by that operation. `link_id` is an ID unique across all operations for that specific operation. `process_type` is the enum you created for your process.

`unlink(link_id, process_type)`: Unlink an operation to that process. This lets the process know the operation no longer needs it (because its closing or just doesn't need it). `link_id` is an ID unique across all operations for that specific operation. `process_type` is the enum you created for your process.

When all links are gone, a process will unload itself. Once an operation links up again, the process will start up again. For examples of how this is used, see any `kobold` operation.

There are additional helper functions you may find useful:

`get_process(process_type)`: Get the instance of that process. Useful if you need direct access to its attributes such as `port`.

`signal_reload(process_type)`: Have the process restart on the next clock cycle. Typically not needed for an operation and moreso for restarting a process with modified configuration.

`signal_unload(process_type)`: Have the process foribly unload on the next clock cycle. Ignores existing links and just shuts down the process. Typically not needed for an operation and moreso for jaison-core shutdown.

### Adding MCP Servers

[Take me to the top!](#developer-guide)

This project has an MCP client built in. Tool calls are generated by a separately configured tool-calling LLM (the one with role `mcp`) given the current user and system prompt as context. This tool-calling occurs in the response pipeline just before the prompts for the personality LLM is generated. Tools are automatically described and their results appended to the script for any MCP server, and any well documented MCP server will be compatible with this project.

To add an MCP server, add the MCP server directory to `models/mcp`. For example, I have an MCP server in the file `internet.py`, so I can put it in `models/mcp/internet/internet.py`. To configure the project to deploy and use that server, in the yaml config, add a new entry under `mcp`. For example:

```yaml
mcp:
- id: example_server
  command: python
  args: ["example_mcp_server.py"]
  cwd: "path/to/server/directory"
```

The `id` can be any arbitrary, unique id of your choice. The rest are self explanatory. You may use any MCP server (it doesn't have to be Python, and if it is Python, it should work with the current Python version and dependencies.).

### Making Applications

[Take me to the top!](#developer-guide)

Applications can vary in form and function. I [Limit] am not going to tell you how to make your application, but here are some pointers.

All interactions are started through the REST API. I've extensively documented it in using the OpenAPI standard in [`api.yaml`](api.yaml) and under the [REST API section](#rest-api).

Majority of interactions are job-based. It will most likely be necessary to create a websocket session. It's recommended to create a long-lived websocket connection and iterate through all incoming events indefinitely. Events can be associated with a specific job via `job_id` and the type of job via the `message`. For more information on these events from order to structure, see the [Websocket Events section](#websocket-events).

### Extending Configuration

[Take me to the top!](#developer-guide)

All configuration lives in `utils/config.py`. They are accessible all throughout the code by importing this module and fetching the singleton via `Config()`. Extending this configuration is as simple as adding a new attribute. **This attribute must have a type hint and a default value**. Now you can configure this value from your config files using the same name as the attribute.

### Extending API

[Take me to the top!](#developer-guide)

The API is implemented using [Quart](https://quart.palletsprojects.com/en/latest/) in `utils/server/app_server.py`. Every endpoint follows a very similar style, and has an entry for functionality and another entry for handling CORS. Regardless of if your making a job-based or non-job-based API endpoint, you need to create both of these entries.

Example functionality entry:
```python
@app.route('/api/config', methods=['GET'])
async def get_current_config():
    pass
```

Example CORSE entry:
```python
@app.route('/api/config', methods=['OPTIONS']) 
async def preflight_config():
    return create_preflight('GET')
```

The CORS entry will always return a call to `create_preflight(method)` and that suffices.

As for functional entries, their implementation differs if they are job-based or not.

#### Non-Job-Based Endpoints

Example

```python
@app.route('/api/config', methods=['GET'])
async def get_current_config():
    return create_response(200, f"Current config gotten", JAIson().get_current_config(), cors_header)
```

This is the typical structure of a non-job-based endpoint. This kind of endpoint does not queue a job. It is your traditional REST API endpoint.

`create_response` normalizes the response returned from the actual function. You can find the implementation in `utils/server/common.py`. In the snippet, besides the obious of changing defined function name, route, and possibly method, we also need to change the message and function call used in `create_response`.

Messages here hold no importance beside potential logging in applications.

All functions are defined in the application layer. This is by convention and up to you if you want to do that. You may return any JSON-serializable data-type, and this will appear in the `response` field of the body.

#### Job-Based Endpoints

Example
```python
@app.route('/api/response', methods=['POST'])
async def response():
    return await _request_job(JobType.RESPONSE)
```

These need to be defined after the definition of `_request_job`. Job-based endpoints are a lot more complicated to setup, so bear with me.

Besides the obvious of changing the API endpoint and method, you need to change the `JobType` to the correct enum. If you're making a new endpoint, chances are you don't have an enum for your job yet. To create a an enum, go to `utils/jaison.py` and add it to `JobType`. The string chosen here is what's used in `message` in events (used to identify which job type event results from).

To associate this enum with a job's function, you need to add a case for it under the function `create_job`. Copy the format of all other lines, only replacing the enum and the function called (**DO NOT AWAIT THIS FUNCTION**).

You will need to correctly define your job's function as well. Define a new **async** function to `JAIson` as follows

```python
    async def my_job_function(
        self,
        job_id: str,
        job_type: JobType,
        ...
    ):
        ...
```

There are several requirements here:

- The only args should be `self`, `job_id`, and `job_type`
- All arguments you expect to receive from the request body are listed as kwargs. You should not put `**kwargs` unless you intend to validate requests bodies in this function.
- **THIS MUST BE AN ASYNC FUNCTION**

Websocket events follow a predictable order, so its best you follow the order of emitted events to avoid breaking applications.

1. Start with `await self._handle_broadcast_start(job_id, job_type, {kwargs})`
    - if one of your kwargs is expected to be large, replace it with a shortform or boolean indicator so listeners can confirm paramenters of job
2. End with `await self._handle_broadcast_success(job_id, job_type)`

You don't need to handle error events as these are done automatically when the coroutine throws an exception.

Implement the rest of your function inbetween. To communicate status and results, use `await _handle_broadcast_event(job_id, job_type, {whatever you want})`. Whatever you put in the dictionary is what's put in `results` in the event.

Now your new job-based endpoint is all setup.

## Known Issues

[Take me to the top!](#developer-guide)

jaison-core will not capture kill signals until all websocket connections are closed. Since jaison-core itself does not let go of these connections, the applications themselves must terminate the connection before jaison-core can shutdown.

No data validation alongside insecure connections make this application vulnerable to all sorts of security attacks. Not recommended to host outside of private network.