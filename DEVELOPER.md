# Developer Guide

## Table of Contents

- [Developer Guide](#developer-guide)
  - [Table of Contents](#table-of-contents)
  - [Community](#community)
  - [Getting Started](#getting-started)
  - [Configuration Basics](#configuration-basics)
    - [Prompting](#prompting)
    - [Operations Pipeline](#operations-pipeline)
  - [Service Providers](#service-providers)
    - [Local Services](#local-services)
      - [KoboldCPP Setup](#koboldcpp-setup)
      - [MeloTTS Setup](#melotts-setup)
      - [RVC (Voice Conversion)](#rvc-voice-conversion)
    - [Cloud Services](#cloud-services)
      - [Azure Speech Services](#azure-speech-services)
      - [Fish Audio](#fish-audio)
      - [OpenAI](#openai)
  - [Operations Reference](#operations-reference)
    - [Speech-to-Text (STT)](#speech-to-text-stt)
      - [Azure](#azure)
      - [Fish](#fish)
      - [Kobold (using Whisper)](#kobold-using-whisper)
      - [OpenAI](#openai-1)
    - [Text-to-Text (T2T)](#text-to-text-t2t)
      - [Kobold](#kobold)
      - [OpenAI](#openai-2)
    - [Text-to-Speech (TTS)](#text-to-speech-tts)
      - [MeloTTS (Recommended)](#melotts-recommended)
      - [Azure](#azure-1)
      - [Fish](#fish-1)
      - [Kobold](#kobold-1)
      - [OpenAI](#openai-3)
      - [pytts](#pytts)
    - [Audio Filters](#audio-filters)
      - [pitch](#pitch)
      - [rvc](#rvc)
    - [Text Filters](#text-filters)
      - [filter\_clean](#filter_clean)
      - [emotion\_roberta](#emotion_roberta)
      - [mod\_koala](#mod_koala)
      - [chunker\_sentence](#chunker_sentence)
    - [Embeddings](#embeddings)
      - [OpenAI](#openai-4)
  - [REST API](#rest-api)
  - [Websocket Events](#websocket-events)
    - [Shared](#shared)
      - [Some Common Enums and Definitions](#some-common-enums-and-definitions)
        - [Job Types](#job-types)
        - [Error Types](#error-types)
      - [Job Start](#job-start)
      - [Job Finish](#job-finish)
      - [Job Cancelled](#job-cancelled)
    - [Job-Specific](#job-specific)
      - [`response`](#response)
      - [`context_clear`](#context_clear)
      - [`context_request_add`](#context_request_add)
      - [`context_conversation_add_text`](#context_conversation_add_text)
      - [`context_conversation_add_audio`](#context_conversation_add_audio)
      - [`context_custom_register`](#context_custom_register)
      - [`context_custom_remove`](#context_custom_remove)
      - [`context_custom_add`](#context_custom_add)
      - [`operation_load`](#operation_load)
      - [`operation_reload_from_config`](#operation_reload_from_config)
      - [`operation_unload`](#operation_unload)
      - [`operation_use`](#operation_use)
      - [`config_load`](#config_load)
      - [`config_update`](#config_update)
      - [`config_save`](#config_save)
  - [Creating Custom Integrations](#creating-custom-integrations)
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
    - [Extending API](#extending-api)
      - [Non-Job-Based Endpoints](#non-job-based-endpoints)
      - [Job-Based Endpoints](#job-based-endpoints)
  - [Known Issues](#known-issues)

---

## Community

**Join the [Discord](https://discord.gg/Z8yyEzHsYM) for discussions related to this project!**

---

## Getting Started

[↑ Back to top](#developer-guide)

An [example configuration](configs/example.yaml) is provided to help you get started. Example prompts can be found under the [`prompts`](prompts) directory.

---

## Configuration Basics

[↑ Back to top](#developer-guide)

### Prompting

Customize your AI character's personality and scenario using prompt files:

**Directory Structure:**
- `prompts/instructions/` - General system/behavior instructions
- `prompts/characters/` - Character personality prompts
- `prompts/scenes/` - Scenario/scene prompts

**Configuration Options:**
```yaml
instruction_prompt_filename: "default"  # Filename without .txt extension
character_prompt_filename: "assistant"  # Filename without .txt extension
scene_prompt_filename: "casual"         # Filename without .txt extension
character_name: "JAIson"                # Name of the character
history_length: 20                      # Number of conversation lines to retain

# Optional: Translate usernames. You can probably exclude this.
name_translations:
  old-name: new-name
```

### Operations Pipeline

Operations are loaded in the order specified in your configuration file. The pipeline processes: **Speech Input → Text Processing → Speech Output**

**Example Configuration:**
```yaml
operations: 
  - role: stt              # Speech-to-Text
    id: fish
  - role: t2t              # Text-to-Text (LLM)
    id: openai
  - role: filter_text      # Text filters (applied in order)
    id: filter_clean
  - role: filter_text
    id: chunker_sentence
  - role: tts              # Text-to-Speech
    id: azure
  - role: filter_audio     # Audio filters (applied in order)
    id: pitch
```

**Important Notes:**
- Only one STT, T2T, and TTS operation can be active (later configs override earlier ones)
- Multiple filters can be active and are applied in the order listed
- Each operation may have additional configuration parameters

---

## Service Providers

[↑ Back to top](#developer-guide)

### Local Services

Run everything on your own hardware without external API calls.

#### KoboldCPP Setup

**Compatibility:** Limited (depends on model)  
**Cost:** Free (local)  
**Supports:** STT, T2T, TTS

**Installation:**

1. **Download KoboldCPP** from [releases](https://github.com/LostRuins/koboldcpp/releases):
   - **NVIDIA GPU (e.g. RTX series):** `koboldcpp.exe` for Windows or `koboldcpp-linux-x64` for Linux
   - **Older NVIDIA GPU (CUDA 11):** `koboldcpp-oldpc.exe` for Windows or `koboldcpp-linux-x64-oldpc` for Linux
   - **Non-NVIDIA (No CUDA):** `koboldcpp-nocuda.exe` for Windows or `koboldcpp-linux-x64-nocuda` for Linux

    Place the KoboldCPP executable in the `models/kobold/` directory.

2. **Download models:**
   - **For T2T (LLM):** Download GGUF models as described [here](https://github.com/LostRuins/koboldcpp?tab=readme-ov-file#Obtaining-a-GGUF-model). Generally, any text-generation GGUF model from HuggingFace will work as long as your hardware meets its requirements. 
   - **For STT (Whisper):** Download the desired `.bin` file from [koboldcpp/whisper](https://huggingface.co/koboldcpp/whisper/tree/main)
     - Recommended: `base.en` or `tiny.en` for balanced performance (English only), or `small` for multilingual support.
   
   Place all models in `models/kobold/`

3. **Configure KoboldCPP:**
   - Run the KoboldCPP executable to open the configuration interface
   - **Under Quick Launch:**
     - Select the correct GPU ID from the dropdown
     - Disable "Launch Browser"
     - Enable "Quiet Mode" (optional, reduces console spam)
     - Enable "Use FlashAttention" (improves performance)
     - Set Context Size based on your available VRAM (2048-8192+ tokens)
     - Click "Browse" and load your GGUF LLM model
   - **Under Context (optional):**
     - Enable "Quantize KV Cache" and set to 8-bit or 4-bit to reduce VRAM usage with minimal quality impact
   - **Under Audio (for STT):**
     - Click "Browse" and load your Whisper model (`.bin` file)
   - **IMPORTANT:** Click "Save" and save the configuration as a `.kcpps` file in `models/kobold/`

4. **Update JAIson configuration:**
   ```yaml
   kobold_filepath: "C:\\path\\to\\models\\kobold\\koboldcpp.exe"
   kcpps_filepath: "C:\\path\\to\\models\\kobold\\myconfig.kcpps"
   ```
   **Note:** On Windows, use double backslashes (`\\`) in file paths

#### MeloTTS Setup

**Compatibility:** All platforms  
**Cost:** Free (local)  
**Supports:** TTS

[MeloTTS](https://github.com/myshell-ai/MeloTTS) provides fast, high-quality local text-to-speech with full control over voice characteristics.

**Recommended for:** Users who want consistent latency and are comfortable with model configuration.

**Installation**
1. MeloTTS was automatically installed during setup when you ran `pip install --no-deps -r requirements.no_deps.txt`
2. Browse the [MeloTTS](https://github.com/myshell-ai/MeloTTS) repo to see available languages and accents. Then, update the `speaker_id` in the JAIson config file. The available speakers are: `EN-Default`, `EN-US`, `EN-BR`, `EN_INDIA`, `EN-AU`. Here is an example config for English (Australian accent):
    ```
    - role: tts
    id: melo
    config_filepath: null
    model_filepath: null
    speaker_id: EN-AU
    device: cuda
    language: EN
    sdp_ratio: 0.7
    noise_scale: 0.6
    noise_scale_w: 0.8
    speed: 1.05
    ```

#### RVC (Voice Conversion)

**Compatibility:** Limited (requires GPU with 8GB+ VRAM for training)  
**Cost:** Free (local)  
**Supports:** Audio filtering (voice conversion)

**Installation:**

1. **Ensure prerequisites:**
   - Git and Git LFS installed on your system

2. **Clone RVC Project:**
   ```bash
   git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git
   ```

3. **Download model assets:**
   ```bash
   cd Retrieval-based-Voice-Conversion-WebUI
   python tools/download_models.py
   ```

4. **Verify download:**
   - Check `assets/hubert/` for `hubert_base.pt` (NOT `hubert_inputs.pth`)

5. **Copy assets to JAIson:**
   - Copy entire `assets/` folder contents to `assets/rvc/` in this project

6. **Train or acquire voice model:**
   - **Training:** Requires NVIDIA GPU with 8GB+ VRAM. See [RVC documentation](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/main/docs/en/README.en.md)
   - **Pre-trained:** Find community models online

7. **Install voice model:**
   - Copy `.pth` file to `assets/rvc/weights/`
   - Copy `.index` file (or folder containing it) to `models/rvc/`
     - If you only have the `.index` file, create a folder named after your `.pth` file

8. **Environment setup:**
   - Copy `.env-template` if not already done
   - Ensure RVC section exists (DO NOT MODIFY)

---

### Cloud Services

Use third-party APIs for high-quality results without local hardware requirements.

#### Azure Speech Services

**Compatibility:** All platforms  
**Cost:** Free tier available  
**Supports:** STT, TTS

**Setup:**

1. Go to [Azure Portal](https://azure.microsoft.com/en-ca) and sign in
2. Navigate to [Resource groups](https://portal.azure.com/#browse/resourcegroups)
3. Click "Create" and configure:
   - Use default subscription (free tier for new accounts)
   - Select a region close to your location
4. Open your new resource group and click "Create"
5. Search for "SpeechServices" and create a [Speech service](https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/CognitiveServicesHub/~/SpeechServices):
   - Select your resource group
   - Choose a nearby region
   - Select "Standard S0" (free tier)
6. Open the Speech service and scroll to the bottom
7. Copy one of the `KEY` values and the `Location/Region`
8. Update your `.env` file:
   ```
   AZURE_API_KEY=your_key_here
   AZURE_REGION=your_region_here
   ```

#### Fish Audio

**Compatibility:** All platforms  
**Cost:** Pay-per-use (premium tier not required)  
**Supports:** STT, TTS (voice cloning)

**Setup:**

1. Go to [Fish Audio](https://fish.audio/auth/) and sign in
2. Navigate to the "API" tab
3. Purchase API credits if needed
4. Go to "API Keys" and click "Create Secret Key"
   - Set a long expiry or "Never expires"
5. Copy the "Secret Key" from the "API List"
6. Update your `.env` file:
   ```
   FISH_API_KEY=your_key_here
   ```

#### OpenAI

**Compatibility:** All platforms (or OpenAI-compatible APIs)  
**Cost:** Pay-per-use  
**Supports:** STT, T2T, TTS

**Setup:**

1. Go to [OpenAI Platform](https://platform.openai.com/) and sign in
2. Navigate to "Profile" → "Secrets"
3. Create and copy a new API key
4. Update your `.env` file:
   ```
   OPENAI_API_KEY=your_key_here
   ```

**For OpenAI-Compatible APIs:**
Many services (like Ollama, LocalAI) offer OpenAI-compatible endpoints. Configure the base URL in your YAML:
```yaml
base_url: "http://localhost:11434/v1"  # Example for Ollama
```

---

## Operations Reference

[↑ Back to top](#developer-guide)

### Speech-to-Text (STT)

Convert spoken audio into text.

#### Azure
- **Service:** Azure Speech Services (Cloud)
- **Cost:** Free tier available
- **Config:**
  ```yaml
  - role: stt
    id: azure
    language: "en-US"  # See Azure language codes
  ```

#### Fish
- **Service:** Fish Audio (Cloud)
- **Cost:** Pay-per-use
- **Config:**
  ```yaml
  - role: stt
    id: fish
  ```

#### Kobold (using Whisper)
- **Service:** KoboldCPP (Local)
- **Cost:** Free
- **Config:**
  ```yaml
  - role: stt
    id: kobold
    suppress_non_speech: true
    langcode: "en"
  ```

#### OpenAI
- **Service:** OpenAI or compatible (Cloud/Local)
- **Cost:** Varies
- **Config:**
  ```yaml
  - role: stt
    id: openai
    base_url: "https://api.openai.com/v1"  # Optional, for custom endpoints
    model: "whisper-1"
    language: "en"  # See Whisper language codes
  ```

---

### Text-to-Text (T2T)

Process and generate conversational responses using LLMs.

#### Kobold
- **Service:** KoboldCPP (Local)
- **Cost:** Free
- **Features:** Advanced sampler controls
- **Config:**
  ```yaml
  - role: t2t
    id: kobold
    max_context_length: 4096    # Context length set during Kobold config
    max_length: 200             # Max response length
    quiet: true                 # Quiet mode
    rep_pen: 1.1                # Repetition penalty - depends on model, but 1.1 is common
    rep_pen_range: 1024         # Depends on model
    temperature: 0.7            # Controls randomness: higher is more creative, lower is more deterministic
    top_k: 40                   # Limits the next word selection to the top X most likely candidates
    top_p: 0.95                 # Nucleus sampling: only considers tokens that make up the top X% probability mass
    typical: 1                  # Typical sampling threshold; 1 = disabled
  ```

#### OpenAI
- **Service:** OpenAI or compatible (Cloud/Local)
- **Cost:** Varies
- **Config:**
  ```yaml
  - role: t2t
    id: openai
    base_url: "https://api.openai.com/v1"
    model: "gpt-4"
    temperature: 0.7
    top_p: 1.0
    presence_penalty: 0.0
    frequency_penalty: 0.0
  ```

---

### Text-to-Speech (TTS)

Convert text responses into spoken audio.

#### MeloTTS (Recommended)
- **Service:** MeloTTS (Local)
- **Cost:** Free
- **Quality:** Fast, consistent, highly configurable
- **Config:**
  ```yaml
  - role: tts
    id: melo
    config_filepath: null
    model_filepath: null
    speaker_id: "EN-US"     # Or whichever voice you prefer
    device: "cuda"          # or "cpu"
    language: "EN"
    sdp_ratio: 0.5          # Expressiveness and rhythmic variation
    noise_scale: 0.6        # Energy and emotional variance 
    noise_scale_w: 0.8      # Cadence and smoothness; "breathiness"
    speed: 1.0
  ```

#### Azure
- **Service:** Azure Speech Services (Cloud)
- **Cost:** Free tier available
- **Quality:** Natural, professional voices
- **Config:**
  ```yaml
  - role: tts
    id: azure
    voice: "en-US-AshleyNeural"  # See Azure voice gallery
  ```

#### Fish
- **Service:** Fish Audio (Cloud)
- **Cost:** Pay-per-use
- **Quality:** Voice cloning capability
- **Config:**
  ```yaml
  - role: tts
    id: fish
    model_id: "your_model_id"
    backend: "default"
    normalize: true
    latency: "normal"  # "normal" or "balanced"
  ```

#### Kobold
- **Service:** KoboldCPP (Local)
- **Cost:** Free
- **Note:** Basic quality, included for completeness
- **Config:**
  ```yaml
  - role: tts
    id: kobold
    voice: "default"
  ```

#### OpenAI
- **Service:** OpenAI or compatible (Cloud/Local)
- **Cost:** Varies
- **Config:**
  ```yaml
  - role: tts
    id: openai
    base_url: "https://api.openai.com/v1"
    model: "tts-1"
    voice: "alloy"
  ```

#### pytts
- **Service:** System TTS (Local)
- **Cost:** Free
- **Note:** Uses OS speech synthesizer (SAPI/ESpeak)
- **Config:**
  ```yaml
  - role: tts
    id: pytts
    voice: "voice_id"  # List printed on startup
    gender: "female"
  ```

---

### Audio Filters

Post-process generated audio.

#### pitch
- **Service:** Local processing
- **Cost:** Free
- **Purpose:** Adjust voice pitch
- **Config:**
  ```yaml
  - role: filter_audio
    id: pitch
    pitch_amount: 2  # Semitones (+/-)
  ```

#### rvc
- **Service:** RVC (Local)
- **Cost:** Free
- **Purpose:** Voice conversion/transformation
- **Config:**
  ```yaml
  - role: filter_audio
    id: rvc
    voice: "model_name"
    f0_up_key: 0
    f0_method: "rmvpe"
    index_rate: 0.75
    filter_radius: 3
    resample_sr: 0
    rms_mix_rate: 0.25
    protect: 0.33
  ```

---

### Text Filters

Process text before speech synthesis.

#### filter_clean
- **Service:** Local processing
- **Cost:** Free
- **Purpose:** Clean and normalize text output
- **Config:**
  ```yaml
  - role: filter_text
    id: filter_clean
  ```

#### emotion_roberta
- **Service:** Local ML model
- **Cost:** Free
- **Purpose:** Detect emotion in responses
- **Model:** [SamLowe/roberta-base-go_emotions](https://huggingface.co/SamLowe/roberta-base-go_emotions)
- **Config:**
  ```yaml
  - role: filter_text
    id: emotion_roberta
  ```

#### mod_koala
- **Service:** Local ML model
- **Cost:** Free
- **Purpose:** Content moderation and filtering (remove for uncensored output)
- **Model:** [Koala/Text-Moderation](https://huggingface.co/KoalaAI/Text-Moderation)
- **Config:**
  ```yaml
  - role: filter_text
    id: mod_koala
  ```

#### chunker_sentence
- **Service:** Local processing
- **Cost:** Free
- **Purpose:** Split text into sentences for smoother TTS
- **Config:**
  ```yaml
  - role: filter_text
    id: chunker_sentence
  ```

---

### Embeddings

Generate text embeddings for semantic operations.

#### OpenAI
- **Service:** OpenAI or compatible (Cloud/Local)
- **Cost:** Varies
- **Config:**
  ```yaml
  - role: embedding
    id: openai
    base_url: "https://api.openai.com/v1"
    model: "text-embedding-3-small"
  ```

---

## REST API

[↑ Back to top](#developer-guide)

API spec is made with OpenAPI 3.1.0 standard and can be found [`api.yaml`](api.yaml).

Please read the description of the endpoint you are interested in. If it specifies use of websockets to communicate status or results, you will need to setup a websocket for updates on your request. Using such REST API endpoints are successful when they successfully queue a job and doesn't mean the job itself was successful.

Please see [Websocket Events](#websocket-events) for websocket messages related to each job.

## Websocket Events

[↑ Back to top](#developer-guide)

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

[↑ Back to top](#developer-guide)

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

Operation - A unit of compute that assists in creating or modifying a response.

Active operation - Operation that has started and can be used.

Inactive operation - Operation that has never been started or has closed and can't be used.

Process - An program that has to run in a separate process from jaison-core. When referred to in this context, it generally means jaison-core is responsible for starting and stopping this process (it is a child process to jaison-core and not another server you manually booted up on the side).

Application - A program that uses the REST API or websocket server of jaison-core.

Application layer - Main implementation of functionality for all REST API endpoints. `utils/jaison.py` is the file Limit refers to as the "application layer" whereas operations are seen as the "hardware layer".

Event - Message sent through a websocket from jaison-core to an application

Job - Special request created through the REST API. These are tasks to be completed after all previously created tasks are complete. They run one at a time and wait in a queue to be processed next. They outlive the original API request that made them, and they communicate back their results and status through websockets. Each job is associated with a single function in the application layer. Simply, they are queued functions that will produce events.

### Making Operations

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

Applications can vary in form and function. I [Limit] am not going to tell you how to make your application, but here are some pointers.

All interactions are started through the REST API. I've extensively documented it in using the OpenAPI standard in [`api.yaml`](api.yaml) and under the [REST API section](#rest-api).

Majority of interactions are job-based. It will most likely be necessary to create a websocket session. It's recommended to create a long-lived websocket connection and iterate through all incoming events indefinitely. Events can be associated with a specific job via `job_id` and the type of job via the `message`. For more information on these events from order to structure, see the [Websocket Events section](#websocket-events).

### Extending Configuration

All configuration lives in `utils/config.py`. They are accessible all throughout the code by importing this module and fetching the singleton via `Config()`. Extending this configuration is as simple as adding a new attribute. **This attribute must have a type hint and a default value**. Now you can configure this value from your config files using the same name as the attribute.

### Extending API

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

[↑ Back to top](#developer-guide)

jaison-core will not capture kill signals until all websocket connections are closed. Since jaison-core itself does not let go of these connections, the applications themselves must terminate the connection before jaison-core can shutdown.

No data validation alongside insecure connections make this application vulnerable to all sorts of security attacks. Not recommended to host outside of private network.