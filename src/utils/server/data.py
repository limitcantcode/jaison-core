"""Pydantic models for the REST API and WebSocket event payloads.

HTTP job endpoints only queue work and return a ``job_id``. Progress and results are
broadcast on the WebSocket (``/``) as ``WebSocketEventMessage`` instances while the
job runs in ``JAIson``.
"""

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

_OP_ROLE_DESC = "Operation role: stt, mcp, t2t, tts, filter_audio, filter_text, or embedding."

# --- Envelope -----------------------------------------------------------------


class ApiResponse(BaseModel, Generic[T]):
    status: int = Field(description="HTTP-style status code mirrored in the JSON body.")
    message: str = Field(description="Human-readable summary of the result.")
    response: T = Field(description="Endpoint-specific payload.")


# --- Immediate HTTP responses -------------------------------------------------


class JobCreatedResponse(BaseModel):
    """Returned when a job is queued successfully."""

    job_id: str = Field(
        description=(
            "UUID of the queued job (same as the request's X-Request-ID); "
            "use to correlate WebSocket events and HTTP logs."
        )
    )


class EmptyResponse(BaseModel):
    """Returned by ``DELETE /api/job`` on success (``cancel_job`` returns ``None``)."""


class LoadedOperationsResponse(BaseModel):
    """Loaded operation IDs keyed by role (from ``JAIson.get_loaded_operations``)."""

    model_config = ConfigDict(extra="allow")

    stt: str | list[str] | Literal["unknown"] | None = Field(
        default=None, description="Loaded STT operation id, or list if multiple."
    )
    mcp: str | list[str] | Literal["unknown"] | None = Field(
        default=None, description="Loaded MCP operation id."
    )
    t2t: str | list[str] | Literal["unknown"] | None = Field(
        default=None, description="Loaded text-to-text operation id."
    )
    tts: str | list[str] | Literal["unknown"] | None = Field(
        default=None, description="Loaded text-to-speech operation id."
    )
    filter_audio: str | list[str] | Literal["unknown"] | None = Field(
        default=None, description="Loaded audio filter id(s)."
    )
    filter_text: str | list[str] | Literal["unknown"] | None = Field(
        default=None, description="Loaded text filter id(s)."
    )
    embedding: str | list[str] | Literal["unknown"] | None = Field(
        default=None, description="Loaded embedding operation id."
    )


class ConfigResponse(BaseModel):
    """Snapshot of the active application config (``vars(config)``)."""

    model_config = ConfigDict(extra="allow")

    CONFIG_DIR: str | None = Field(
        default=None, description="Directory containing YAML config files."
    )
    WORKING_DIR: str | None = Field(
        default=None, description="Temporary working directory for runtime files."
    )
    current_config: str | None = Field(
        default=None,
        description="Name of the loaded config file, or ``Unsaved`` if edited in memory.",
    )
    operations: list[Any] | None = Field(
        default=None, description="Operation entries from the active configuration."
    )
    prompter: dict[str, Any] | None = Field(
        default=None, description="Prompter configuration object."
    )
    mcp: list[Any] | None = Field(default=None, description="Configured MCP server entries.")
    PROMPT_DIR: str | None = Field(default=None, description="Root directory for prompt templates.")
    MCP_DIR: str | None = Field(
        default=None, description="Directory containing MCP server implementations."
    )
    MELO_DIR: str | None = Field(default=None, description="Directory for MeloTTS model assets.")
    history_filepath: str | None = Field(
        default=None, description="Debug path where conversation history is written."
    )
    kobold_filepath: str | None = Field(
        default=None, description="Path to the Kobold-compatible binary, if configured."
    )
    kcpps_filepath: str | None = Field(
        default=None, description="Path to the KoboldCPP server binary, if configured."
    )
    stt_working_src: str | None = Field(
        default=None, description="Working WAV path used by STT operations."
    )
    ffmpeg_working_src: str | None = Field(default=None, description="FFmpeg source WAV path.")
    ffmpeg_working_dest: str | None = Field(default=None, description="FFmpeg output WAV path.")
    spacy_model: str | None = Field(
        default=None, description="spaCy model name used by text filters."
    )


# --- Job request bodies (forwarded as ``create_job`` kwargs) ------------------


class ResponseJobRequest(BaseModel):
    include_audio: bool = Field(
        default=True,
        description="Whether to generate TTS audio during the response pipeline (disabled if no TTS is loaded).",
    )


class ContextConfigureRequest(BaseModel):
    name_translations: dict[str, str] | None = Field(
        default=None,
        description="Map of script names to display names shown to the model.",
    )
    character_name: str | None = Field(
        default=None, description="Name of the character in the script."
    )
    history_length: int | None = Field(
        default=None, description="Maximum number of script lines to retain in history."
    )
    instruction_prompt_filename: str | None = Field(
        default=None, description="Filename of the instruction prompt under the prompts directory."
    )
    character_prompt_filename: str | None = Field(
        default=None, description="Filename of the character prompt under the prompts directory."
    )
    scene_prompt_filename: str | None = Field(
        default=None, description="Filename of the scene prompt under the prompts directory."
    )


class ContextRequestAddRequest(BaseModel):
    content: str | None = Field(
        default=None, description="Request text appended to the script for the model to address."
    )


class ContextConversationTextRequest(BaseModel):
    user: str | None = Field(default=None, description="Speaker name associated with the message.")
    timestamp: float | int | None = Field(
        default=None, description="UNIX timestamp for the message; defaults to now if omitted."
    )
    content: str | None = Field(
        default=None, description="Message text added to the conversation history."
    )


class ContextConversationAudioRequest(BaseModel):
    user: str | None = Field(default=None, description="Speaker name associated with the audio.")
    timestamp: float | int | None = Field(
        default=None, description="UNIX timestamp for the message; defaults to now if omitted."
    )
    audio_bytes: str | None = Field(
        default=None,
        description="Base64-encoded PCM audio to transcribe and append as conversation text.",
    )
    sr: int | None = Field(default=None, description="Audio sample rate in Hz.")
    sw: int | None = Field(default=None, description="Sample width in bytes.")
    ch: int | None = Field(default=None, description="Number of audio channels.")


class ContextCustomRegisterRequest(BaseModel):
    context_id: str | None = Field(
        default=None, description="Identifier used when adding this custom context later."
    )
    context_name: str | None = Field(
        default=None, description="Display name of the custom context in the script."
    )
    context_description: str | None = Field(
        default=None, description="Description of the context provided to the model."
    )


class ContextCustomRemoveRequest(BaseModel):
    context_id: str | None = Field(
        default=None, description="Identifier of the custom context to unregister."
    )


class ContextCustomAddRequest(BaseModel):
    context_id: str | None = Field(
        default=None, description="Registered custom context id to append content for."
    )
    context_contents: str | None = Field(
        default=None, description="Content added to the script under the custom context."
    )
    timestamp: float | int | None = Field(
        default=None, description="UNIX timestamp for the entry; defaults to now if omitted."
    )


class OperationSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: str | None = Field(default=None, description=_OP_ROLE_DESC)
    id: str | None = Field(default=None, description="Operation id under the given role.")
    config: dict[str, Any] | None = Field(
        default=None, description="Role-specific configuration passed when loading the operation."
    )
    loose_key: str | None = Field(
        default=None, description="Optional loose-load key reported in load progress events."
    )


class OperationsListRequest(BaseModel):
    ops: list[OperationSpec] = Field(
        default_factory=list,
        description="Operations to load, unload, or configure.",
    )


class OperationUseRequest(BaseModel):
    role: str | None = Field(default=None, description=_OP_ROLE_DESC)
    id: str | None = Field(
        default=None,
        description="Specific operation id; uses the loaded operation for the role if omitted.",
    )
    payload: dict[str, Any] | None = Field(
        default=None,
        description="Input passed to the operation (see DEVELOPER.md for per-role fields).",
    )


class ConfigLoadRequest(BaseModel):
    config_name: str | None = Field(
        default=None, description="Name of the YAML config file to load from the configs directory."
    )


class ConfigUpdateRequest(BaseModel):
    """Config fields to merge; passed to ``Config.load_from_dict`` via ``config_d``."""

    model_config = ConfigDict(extra="allow")

    config_d: dict[str, Any] | None = Field(
        default=None,
        description="Configuration fields to apply. Flat request bodies are wrapped as ``config_d`` by the server.",
    )


class ConfigSaveRequest(BaseModel):
    config_name: str | None = Field(
        default=None, description="Filename to write the current in-memory configuration to."
    )


class CancelJobRequest(BaseModel):
    job_id: str = Field(description="UUID of the queued or running job to cancel.")
    reason: str | None = Field(
        default=None, description="Optional reason recorded in logs and cancellation events."
    )


# --- WebSocket event payloads (``JAIson._handle_broadcast_*``) ---------------


class JobErrorResult(BaseModel):
    type: str = Field(
        description=(
            "Error category, e.g. operation_unknown_role, operation_unloaded, "
            "config_unknown_field, or job_cancelled."
        )
    )
    reason: str = Field(description="Human-readable error message.")


class JobStartEvent(BaseModel):
    job_id: str = Field(description="UUID of the job that started processing.")
    start: dict[str, Any] = Field(
        description="Job arguments from the original REST request (large fields may be abbreviated)."
    )


class JobProgressEvent(BaseModel):
    job_id: str = Field(description="UUID of the job emitting this event.")
    finished: Literal[False] = Field(
        default=False, description="Always false for in-progress result events."
    )
    result: dict[str, Any] = Field(description="Partial output or status payload for this job.")


class JobSuccessEvent(BaseModel):
    job_id: str = Field(description="UUID of the job that completed successfully.")
    finished: Literal[True] = Field(default=True, description="Always true when the job completed.")
    success: Literal[True] = Field(
        default=True, description="Always true for a successful completion."
    )


class JobErrorEvent(BaseModel):
    job_id: str = Field(description="UUID of the job that failed or was cancelled.")
    finished: Literal[True] = Field(default=True, description="Always true when the job has ended.")
    success: Literal[False] = Field(
        default=False, description="Always false for error or cancellation events."
    )
    result: JobErrorResult = Field(description="Structured error details.")


JobEventPayload = JobStartEvent | JobProgressEvent | JobSuccessEvent | JobErrorEvent


class WebSocketEventMessage(BaseModel):
    """JSON message pushed to WebSocket clients (``message`` is the ``JobType`` value)."""

    status: int = Field(
        default=200, description="Envelope status; always 200 for broadcast events."
    )
    message: str = Field(
        description="Job type string (``JobType.value``), e.g. response or context_clear."
    )
    response: JobEventPayload = Field(description="Start, progress, success, or error event body.")


# Response type aliases (for route ``response_model``)
AnyApiResponse = ApiResponse[dict[str, Any]]
JobCreatedApiResponse = ApiResponse[JobCreatedResponse]
LoadedOperationsApiResponse = ApiResponse[LoadedOperationsResponse]
ConfigApiResponse = ApiResponse[ConfigResponse]
EmptyApiResponse = ApiResponse[EmptyResponse]
WebSocketEventApiResponse = ApiResponse[JobEventPayload]
