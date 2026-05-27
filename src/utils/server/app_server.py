import asyncio
import base64
import logging
from typing import Any

import uvicorn
from fastapi import Body, FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from utils.args import args
from utils.helpers.observer import BaseObserverClient
from utils.helpers.singleton import Singleton
from utils.jaison import JAIson, JobType, NonexistantJobException

from .common import api_response
from .middleware import RequestMetricsTrackingMiddleware
from .data import (
    AnyApiResponse,
    ApiResponse,
    CancelJobRequest,
    ConfigApiResponse,
    ConfigLoadRequest,
    ConfigResponse,
    ConfigSaveRequest,
    ConfigUpdateRequest,
    ContextConfigureRequest,
    ContextConversationAudioRequest,
    ContextConversationTextRequest,
    ContextCustomAddRequest,
    ContextCustomRegisterRequest,
    ContextCustomRemoveRequest,
    ContextRequestAddRequest,
    EmptyApiResponse,
    EmptyResponse,
    JobCreatedApiResponse,
    JobCreatedResponse,
    JobStartEvent,
    LoadedOperationsApiResponse,
    LoadedOperationsResponse,
    OperationsListRequest,
    OperationUseRequest,
    ResponseJobRequest,
    WebSocketEventApiResponse,
)

app = FastAPI(
    title="jaison-core",
    description=(
        "Job-based REST API. Job endpoints return a `job_id` immediately; "
        "subscribe to the WebSocket at `/` for start, progress, success, and error events."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestMetricsTrackingMiddleware)

API_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": AnyApiResponse, "description": "Client error"},
    500: {"model": AnyApiResponse, "description": "Server error"},
}

JOB_DESCRIPTION = "Queues a job and returns its ID. Progress and results are sent on the WebSocket at `/`."

## Websocket Event Broadcasting Server ##


class SocketServerObserver(BaseObserverClient, metaclass=Singleton):
    def __init__(self):
        super().__init__(server=JAIson().event_server)
        self.connections: set[WebSocket] = set()
        self.shutdown_signal = asyncio.Future()

    async def handle_event(self, event_id: str, payload: dict[str, Any]) -> None:
        """Broadcast events from broadcast server."""
        for key in payload:
            if isinstance(payload[key], bytes):
                payload[key] = base64.b64encode(payload[key]).decode("utf-8")
        message = ApiResponse(status=200, message=event_id, response=payload).model_dump_json()
        logging.debug(f"Broadcasting event to {len(self.connections)} clients")
        for ws in set(self.connections):
            await ws.send_text(message)

    def shutdown(self, *args):  # TODO set for use somewhere
        self.shutdown_signal.set_result(None)


@app.websocket("/")
async def ws(websocket: WebSocket):
    """Receive job events as JSON matching ``WebSocketEventMessage`` (see ``GET /api/events/schema``)."""
    sso = SocketServerObserver()
    logging.info("Opened new websocket connection")
    await websocket.accept()
    sso.connections.add(websocket)
    try:
        while not sso.shutdown_signal.done():
            await asyncio.sleep(10)
    except (WebSocketDisconnect, asyncio.CancelledError):
        sso.connections.discard(websocket)
        logging.info("Closed websocket connection")
        raise


## Schema documentation ######################################################


@app.get(
    "/api/events/schema",
    response_model=WebSocketEventApiResponse,
    tags=["websocket"],
    summary="Example WebSocket event envelope",
    description=(
        "Illustrates the JSON shape pushed on `/`. The `message` field is the "
        "`JobType` value (e.g. `response`). Real `response` objects vary by event kind."
    ),
)
async def websocket_event_schema() -> WebSocketEventApiResponse:
    return ApiResponse(
        status=200,
        message=JobType.RESPONSE.value,
        response=JobStartEvent(
            job_id="00000000-0000-0000-0000-000000000000",
            start={"include_audio": True},
        ),
    )


## Generic endpoints ###################


@app.get("/api/operations", response_model=LoadedOperationsApiResponse)
async def get_loaded_operations() -> LoadedOperationsApiResponse:
    ops = LoadedOperationsResponse.model_validate(JAIson().get_loaded_operations())
    return api_response(200, "Loaded operations gotten", ops)


@app.get("/api/config", response_model=ConfigApiResponse)
async def get_current_config() -> ConfigApiResponse:
    config = ConfigResponse.model_validate(JAIson().get_current_config())
    return api_response(200, "Current config gotten", config)


## Job management endpoints ###########


@app.delete("/api/job", response_model=EmptyApiResponse, responses=API_ERROR_RESPONSES)
async def cancel_job(body: CancelJobRequest, http_response: Response) -> EmptyApiResponse:
    try:
        await JAIson().cancel_job(body.job_id, body.reason)
        return api_response(200, "Job flagged for cancellation", EmptyResponse(), http_response=http_response)
    except NonexistantJobException:
        return api_response(
            400,
            "Job ID does not exist or already finished",
            EmptyResponse(),
            http_response=http_response,
        )
    except Exception as err:
        return api_response(500, str(err), EmptyResponse(), http_response=http_response)


## Specific job creation endpoints ####


def _job_kwargs(job_type: JobType, body: BaseModel | None) -> dict[str, Any]:
    if body is None:
        return {}
    data = body.model_dump(exclude_none=True)
    if job_type == JobType.CONFIG_UPDATE and data and "config_d" not in data:
        return {"config_d": data}
    return data


async def _request_job(
    job_type: JobType,
    body: BaseModel | None,
    http_response: Response,
    request: Request,
) -> JobCreatedApiResponse | AnyApiResponse:
    job_name = job_type.value
    job_id = request.state.request_id
    try:
        job_id = await JAIson().create_job(job_type, job_id, **_job_kwargs(job_type, body))
        return api_response(
            200,
            f"{job_name} job created",
            JobCreatedResponse(job_id=job_id),
            http_response=http_response,
        )
    except Exception as err:
        logging.error(f"Error occured for {job_name} API request", stack_info=True, exc_info=True)
        return api_response(500, str(err), EmptyResponse(), http_response=http_response)


@app.post(
    "/api/response",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue a response pipeline job",
    description=JOB_DESCRIPTION,
)
async def response(
    request: Request,
    http_response: Response,
    body: ResponseJobRequest | None = Body(default=None),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.RESPONSE, body, http_response, request)


@app.delete(
    "/api/context",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue a context clear job",
    description=JOB_DESCRIPTION,
)
async def context_clear(
    request: Request, http_response: Response
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.CONTEXT_CLEAR, None, http_response, request)


@app.put(
    "/api/context/config",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue a prompter configuration job",
    description=JOB_DESCRIPTION,
)
async def context_configure(
    request: Request,
    http_response: Response,
    body: ContextConfigureRequest = Body(...),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.CONTEXT_CONFIGURE, body, http_response, request)


@app.post(
    "/api/context/request",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue a request-context append job",
    description=JOB_DESCRIPTION,
)
async def context_request_add(
    request: Request,
    http_response: Response,
    body: ContextRequestAddRequest = Body(...),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.CONTEXT_REQUEST_ADD, body, http_response, request)


@app.post(
    "/api/context/conversation/text",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue a text conversation append job",
    description=JOB_DESCRIPTION,
)
async def context_conversation_add_text(
    request: Request,
    http_response: Response,
    body: ContextConversationTextRequest = Body(...),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.CONTEXT_CONVERSATION_ADD_TEXT, body, http_response, request)


@app.post(
    "/api/context/conversation/audio",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue an audio conversation append job",
    description=JOB_DESCRIPTION,
)
async def context_conversation_add_audio(
    request: Request,
    http_response: Response,
    body: ContextConversationAudioRequest = Body(...),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.CONTEXT_CONVERSATION_ADD_AUDIO, body, http_response, request)


@app.put(
    "/api/context/custom",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue a custom context registration job",
    description=JOB_DESCRIPTION,
)
async def context_custom_register(
    request: Request,
    http_response: Response,
    body: ContextCustomRegisterRequest = Body(...),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.CONTEXT_CUSTOM_REGISTER, body, http_response, request)


@app.delete(
    "/api/context/custom",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue a custom context removal job",
    description=JOB_DESCRIPTION,
)
async def context_custom_remove(
    request: Request,
    http_response: Response,
    body: ContextCustomRemoveRequest = Body(...),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.CONTEXT_CUSTOM_REMOVE, body, http_response, request)


@app.post(
    "/api/context/custom",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue a custom context append job",
    description=JOB_DESCRIPTION,
)
async def context_custom_add(
    request: Request,
    http_response: Response,
    body: ContextCustomAddRequest = Body(...),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.CONTEXT_CUSTOM_ADD, body, http_response, request)


@app.post(
    "/api/operations/load",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue an operation load job",
    description=JOB_DESCRIPTION,
)
async def operation_start(
    request: Request,
    http_response: Response,
    body: OperationsListRequest = Body(...),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.OPERATION_LOAD, body, http_response, request)


@app.post(
    "/api/operations/reload",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue a reload-from-config job",
    description=JOB_DESCRIPTION,
)
async def operation_reload(
    request: Request, http_response: Response
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.OPERATION_CONFIG_RELOAD, None, http_response, request)


@app.post(
    "/api/operations/unload",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue an operation unload job",
    description=JOB_DESCRIPTION,
)
async def operation_unload(
    request: Request,
    http_response: Response,
    body: OperationsListRequest = Body(...),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.OPERATION_UNLOAD, body, http_response, request)


@app.post(
    "/api/operations/config",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue an operation configure job",
    description=JOB_DESCRIPTION,
)
async def operation_configure(
    request: Request,
    http_response: Response,
    body: OperationsListRequest = Body(...),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.OPERATION_CONFIGURE, body, http_response, request)


@app.post(
    "/api/operations/use",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue a direct operation use job",
    description=JOB_DESCRIPTION,
)
async def operation_use(
    request: Request,
    http_response: Response,
    body: OperationUseRequest = Body(...),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.OPERATION_USE, body, http_response, request)


@app.put(
    "/api/config/load",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue a config load job",
    description=JOB_DESCRIPTION,
)
async def config_load(
    request: Request,
    http_response: Response,
    body: ConfigLoadRequest = Body(...),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.CONFIG_LOAD, body, http_response, request)


@app.put(
    "/api/config/update",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue a config update job",
    description=JOB_DESCRIPTION,
)
async def config_update(
    request: Request,
    http_response: Response,
    body: ConfigUpdateRequest = Body(...),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.CONFIG_UPDATE, body, http_response, request)


@app.post(
    "/api/config/save",
    response_model=JobCreatedApiResponse,
    responses=API_ERROR_RESPONSES,
    summary="Queue a config save job",
    description=JOB_DESCRIPTION,
)
async def config_save(
    request: Request,
    http_response: Response,
    body: ConfigSaveRequest = Body(...),
) -> JobCreatedApiResponse | AnyApiResponse:
    return await _request_job(JobType.CONFIG_SAVE, body, http_response, request)


## START ###################################


async def start_web_server():  # TODO launch application plugins here as well
    try:
        await JAIson().start()
        SocketServerObserver()
        config = uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    except Exception:
        logging.error("Stopping server due to exception", exc_info=True)
    finally:
        await JAIson().stop()
