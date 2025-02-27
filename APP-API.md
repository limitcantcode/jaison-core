# API for Application Plugins
_Because I'm too lazy to make an OpenAPI doc right now_

## REST

### Requesting responses

#### `/run [POST]`:

Request a response or add to main contexts

Body:
- `input_user`: (`str`,`None`) Name associated with input. Can be empty for requests
- `input_time`: (`datetime iso string`,`None`) Time associated with input. Ignored for request
- `input_audio_bytes`: (`str`,`None`) Input audio bytes that are base64 encoded in utf-8
- `input_audio_sample_rate`: (`int`,`None`) Input audio sample rate
- `input_audio_sample_width`: (`int`,`None`) Input audio sample width
- `input_audio_channels`: (`int`,`None`) Input audio channels
- `input_text`: (`str`,`None`) Input text
- `process_dialog`: (`bool`,`False`) Process input as line in main conversation context
- `process_request`: (`bool`,`False`) Process input as addition to request context
- `output_text`: (`bool`,`True`) Create T2T response
- `output_audio`: (`bool`,`True`) Create T2T and TTS response
- `skip_ttsc`: (`bool`,`False`) Whether to skip the TTSC (voice cloning) pass for this generation

Returns
- `run_id`: (`uuid string`) New response run's id

Requirements
- exactly one of `process_dialog` or `process_request` is `True`
- exactly one of `input_text` or all of `input_audio_...`
- `input_user` required if `process_dialog` is `True` 

#### `/run [DELETE]`:

Cancel a response or main context update

Body:
- `run_id`: (`uuid string`) Response run's id to cancel

Returns:
- `run_id`: (`uuid string`) Response run's id to cancel

### Managing external context

#### `/context [POST]`

Register a new context to be added to prompts.

Body:
- `id`: (`str`) Unique identifier
- `name`: (`str`) Actual name/title for header
- `description`: (`str`) Description for understanding prompt context

Returns:
- `id`: (`str`) Id of modified context

Notes:
- if there is a clash in `id`, then the latest `name` and `description` is used and context data is cleared

#### `/context [PUT]`

Update context content.

Body:
- `id`: (`str`) Unique identifier
- `content`: (`str`) Contents to put under context header in prompt

Returns:
- `id`: (`str`) Id of modified context

#### `/context [DELETE]`

Remove context from prompt.

Body:
- `id`: (`str`) Unique identifier of context

Returns:
- `id`: (`str`) Id of modified context

## Websocket

Simply connect to the root endpoint (for example `http://localhost:5001`) to start listening.

### Response structure

All events are json strings of the following format
```json
{
    "status": 200, // Regular http status codes. 200, 400, 500 generally sent
    "message": "run_start", // Event name
    "response": {...} // Event contents
}
```

`response` contains fields as specified in [Possible events](#possible-events). Here's what each mean

<hr/>

- run_id: (str) uuid string id for that requested run

<hr/>

- output_text: (bool) whether to expect text output
- output_audio: (bool) whether to expect audio output
- runtime: (float) length of execution in seconds
- reason: (str) Reason for cancellation

<hr/>

- some chunk: (str) Parts of the response as they are generating/streaming. For textual responses (`stt`, `context`, `t2t`), these are the literal responses. For audio responses (`tts`), these are bytes that have been base64 encoded as utf-8. See the event loop of my [Discord Bot](https://github.com/limitcantcode/app-jaison-discord-lcc) for an example of how to turn it back into audio bytes.
- success: (str) True until a non-cancelling error occurs in processing. When this happens, previously generated responses are typically overwritten with a new response.
- sample_rate, sample_width, channels: (int) audio metadata


### Possible events

<hr/>

- `run_start`: New response_pipeline run starts (`{run_id, output_text, output_audio}`)
- `run_finish`: response_pipeline run finishes successfully (`{run_id, runtime}`)
- `run_cancel`: response_pipeline cancelled for some reason and didn't finish successfully (`{run_id, reason}`)

<hr/>

- `run_stt_start`: STT stage began (`{run_id}`)
- `run_context_start`: Context generation stage began (`{run_id}`)
- `run_t2t_start`: T2T stage began (`{run_id}`)
- `run_tts_start`: TTS stage began (`{run_id}`)

<hr/>

- `run_stt_chunk`: STT streamed result (`{run_id, chunk, success}`)
- `run_context_chunk`: Context generation streamed result (`{run_id, sys_chunk, user_chunk, success}`)
- `run_t2t_chunk`: T2T streamed result (`{run_id, chunk, success}`)
- `run_tts_chunk`: TTS streamed result (`{run_id, chunk, sample_rate, sample_width, channels, success}`)

<hr/>

- `run_stt_stop`: STT stage completion (`{run_id, success}`)
- `run_context_stop`: Context generation stage completion (`{run_id, success}`)
- `run_t2t_stop`: T2T stage completion (`{run_id, success}`)
- `run_tts_stop`: TTS stage completion (`{run_id, success}`)