import wave
from io import BytesIO

import httpx

from utils.helpers.subprocess_server import (
    allocate_port,
    bin_executable,
    start_shell_process,
    stop_process,
)

from .base import STTOperation


class WhisperCPPSTT(STTOperation):
    def __init__(self):
        super().__init__("whispercpp")
        self.uri = None
        self.model_filepath = None
        self.language = "en"
        self.temperature = 0.0
        self.response_format = "json"
        self._server_process = None
        self._port: int | None = None
        self._label: str = "whisper.cpp server"
        self._http: httpx.AsyncClient | None = None

    async def start(self) -> None:
        await super().start()
        if self._server_process is not None:
            return

        server = bin_executable("whisper-server")
        self._port = allocate_port()
        cmd = (
            f'"{server}" -m "{self.model_filepath}" --host 127.0.0.1 --port {self._port} '
            f"-l {self.language}"
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
        if "language" in config_d:
            self.language = str(config_d["language"])
        if "temperature" in config_d:
            self.temperature = float(config_d["temperature"])
        if "response_format" in config_d:
            self.response_format = str(config_d["response_format"])

        assert self.model_filepath is not None and len(self.model_filepath) > 0
        assert self.language is not None and len(self.language) > 0
        assert self.response_format in {"json", "text", "verbose_json", "srt", "vtt"}

    async def get_configuration(self):
        return {
            "model_filepath": self.model_filepath,
            "language": self.language,
            "temperature": self.temperature,
            "response_format": self.response_format,
        }

    async def _check_health(self) -> None:
        if self._http is None:
            raise RuntimeError("WhisperCPPSTT server is not running")
        try:
            health_resp = await self._http.get("/v1/health", timeout=5.0)
            health_resp.raise_for_status()
        except httpx.HTTPError as e:
            raise RuntimeError(f"WhisperCPPSTT server health check failed: {e}") from e

    async def _generate(
        self,
        prompt: str = None,
        audio_bytes: bytes = None,
        sr: int = None,
        sw: int = None,
        ch: int = None,
        **kwargs,
    ):
        await self._check_health()

        audio_data = BytesIO()
        with wave.open(audio_data, "wb") as f:
            f.setframerate(sr)
            f.setsampwidth(sw)
            f.setnchannels(ch)
            f.writeframes(audio_bytes)
        audio_data.seek(0)

        try:
            response = await self._http.post(
                "/inference",
                files={"file": ("audio.wav", audio_data.read(), "audio/wav")},
                data={
                    "temperature": str(self.temperature),
                    "response_format": self.response_format,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to get STT result: {e}") from e

        if self.response_format == "text":
            text = response.text
        else:
            body = response.json()
            text = body.get("text") or body.get("transcription") or ""
            if not text and "segments" in body:
                text = " ".join(seg.get("text", "") for seg in body["segments"]).strip()

        yield {"transcription": text}
