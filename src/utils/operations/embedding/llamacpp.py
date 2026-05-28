import base64
import struct

import httpx

from utils.helpers.subprocess_server import (
    allocate_port,
    bin_executable,
    start_shell_process,
    stop_process,
)

from .base import EmbeddingOperation


def _embedding_to_base64(float_list: list[float]) -> str:
    format_string = "<" + "f" * len(float_list)
    packed_bytes = struct.pack(format_string, *float_list)
    return base64.b64encode(packed_bytes).decode("utf-8")


def _extract_embedding_vector(body: object) -> list[float]:
    if isinstance(body, dict) and "embedding" in body:
        vec = body["embedding"]
    elif isinstance(body, list) and body:
        first = body[0]
        vec = first["embedding"] if isinstance(first, dict) else first
    else:
        raise RuntimeError(f"Unexpected llamacpp embedding response: {body!r}")

    if not vec:
        raise RuntimeError("llamacpp embedding response was empty")

    if isinstance(vec[0], (list, tuple)):
        width = len(vec[0])
        return [sum(row[i] for row in vec) / len(vec) for i in range(width)]

    return [float(x) for x in vec]


class LlamaCPPEmbedding(EmbeddingOperation):
    def __init__(self):
        super().__init__("llamacpp")
        self.uri = None
        self.model_filepath = None
        self.pooling = "mean"
        self.embd_normalize = 2
        self._server_process = None
        self._port: int | None = None
        self._label: str = "llama.cpp embedding server"
        self._http: httpx.AsyncClient | None = None

    async def start(self) -> None:
        await super().start()
        if self._server_process is not None:
            return

        server = bin_executable("llama-server")
        self._port = allocate_port()
        cmd = (
            f'"{server}" -m "{self.model_filepath}" --host 127.0.0.1 --port {self._port} '
            f"--embeddings --pooling {self.pooling}"
        )
        self._server_process = start_shell_process(cmd, label=self._label)
        self.uri = f"http://127.0.0.1:{self._port}"
        self._http = httpx.AsyncClient(base_url=self.uri, timeout=httpx.Timeout(600.0))

    async def close(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None
        stop_process(self._server_process, label=self._label)
        self._server_process = None
        self._port = None
        self.uri = None
        await super().close()

    async def configure(self, config_d):
        if "model_filepath" in config_d:
            self.model_filepath = str(config_d["model_filepath"])
        if "pooling" in config_d:
            self.pooling = str(config_d["pooling"])
        if "embd_normalize" in config_d:
            self.embd_normalize = int(config_d["embd_normalize"])

        assert self.model_filepath is not None and len(self.model_filepath) > 0
        assert self.pooling in {"none", "mean", "cls", "last", "rank"}
        assert self.embd_normalize in {-1, 0, 1, 2} or self.embd_normalize > 2

    async def get_configuration(self):
        return {
            "model_filepath": self.model_filepath,
            "pooling": self.pooling,
            "embd_normalize": self.embd_normalize,
        }

    async def _check_health(self) -> None:
        if self._http is None:
            raise RuntimeError("LlamaCPPEmbedding server is not running")
        try:
            health_resp = await self._http.get("/health", timeout=5.0)
            health_resp.raise_for_status()
        except httpx.HTTPError as e:
            raise RuntimeError(f"LlamaCPPEmbedding server health check failed: {e}") from e

    async def _generate(self, content: str = None, **kwargs):
        await self._check_health()

        try:
            response = await self._http.post(
                "/embedding",
                json={"content": content, "embd_normalize": self.embd_normalize},
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to get embedding result: {e}") from e

        float_list = _extract_embedding_vector(response.json())
        yield {"embedding": _embedding_to_base64(float_list)}
