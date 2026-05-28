import json

import httpx

from utils.helpers.subprocess_server import (
    allocate_port,
    bin_executable,
    start_shell_process,
    stop_process,
)
from utils.prompter.message import ChatMessage

from .base import T2TOperation


class LlamaCPPT2T(T2TOperation):
    def __init__(self):
        super().__init__("llamacpp")
        self.uri = None
        self.model_filepath = None
        self.n_predict = 256
        self.temperature = 0.8
        self.top_p = 0.95
        self.top_k = 40
        self.min_p = 0.05
        self.typical_p = 1.0
        self.repeat_penalty = 1.1
        self.repeat_last_n = 64
        self.presence_penalty = 0.0
        self.frequency_penalty = 0.0
        self.dry_multiplier = 0.0
        self.dry_base = 1.75
        self.dry_allowed_length = 2
        self.dry_penalty_last_n = -1
        self.dry_sequence_breakers = ["\n", ":", '"', "*"]
        self.samplers = ["dry", "top_k", "typ_p", "top_p", "min_p", "temperature"]
        self._server_process = None
        self._port: int | None = None
        self._label: str = "llama.cpp server"
        self._http: httpx.AsyncClient | None = None

    async def start(self) -> None:
        await super().start()
        if self._server_process is not None:
            return

        server = bin_executable("llama-server")
        self._port = allocate_port()
        cmd = f'"{server}" -m "{self.model_filepath}" --host 127.0.0.1 --port {self._port}'
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
        if "n_predict" in config_d:
            self.n_predict = int(config_d["n_predict"])
        if "max_tokens" in config_d:
            self.n_predict = int(config_d["max_tokens"])
        if "max_length" in config_d:
            self.n_predict = int(config_d["max_length"])
        if "temperature" in config_d:
            self.temperature = float(config_d["temperature"])
        if "top_p" in config_d:
            self.top_p = float(config_d["top_p"])
        if "top_k" in config_d:
            self.top_k = int(config_d["top_k"])
        if "min_p" in config_d:
            self.min_p = float(config_d["min_p"])
        if "typical_p" in config_d:
            self.typical_p = float(config_d["typical_p"])
        if "repeat_penalty" in config_d:
            self.repeat_penalty = float(config_d["repeat_penalty"])
        if "repeat_last_n" in config_d:
            self.repeat_last_n = int(config_d["repeat_last_n"])
        if "presence_penalty" in config_d:
            self.presence_penalty = float(config_d["presence_penalty"])
        if "frequency_penalty" in config_d:
            self.frequency_penalty = float(config_d["frequency_penalty"])
        if "dry_multiplier" in config_d:
            self.dry_multiplier = float(config_d["dry_multiplier"])
        if "dry_base" in config_d:
            self.dry_base = float(config_d["dry_base"])
        if "dry_allowed_length" in config_d:
            self.dry_allowed_length = int(config_d["dry_allowed_length"])
        if "dry_penalty_last_n" in config_d:
            self.dry_penalty_last_n = int(config_d["dry_penalty_last_n"])
        if "dry_sequence_breakers" in config_d:
            self.dry_sequence_breakers = list(config_d["dry_sequence_breakers"])
        if "samplers" in config_d:
            self.samplers = list(config_d["samplers"])

        assert self.model_filepath is not None and len(self.model_filepath) > 0
        assert self.n_predict > 0
        assert self.temperature >= 0
        assert self.top_k >= 0
        assert 0 <= self.top_p <= 1
        assert 0 <= self.min_p <= 1
        assert self.typical_p > 0
        assert self.dry_multiplier >= 0
        assert self.dry_base > 0
        assert self.dry_allowed_length >= 0
        assert len(self.samplers) > 0

    async def get_configuration(self):
        return {
            "model_filepath": self.model_filepath,
            "n_predict": self.n_predict,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "min_p": self.min_p,
            "typical_p": self.typical_p,
            "repeat_penalty": self.repeat_penalty,
            "repeat_last_n": self.repeat_last_n,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "dry_multiplier": self.dry_multiplier,
            "dry_base": self.dry_base,
            "dry_allowed_length": self.dry_allowed_length,
            "dry_penalty_last_n": self.dry_penalty_last_n,
            "dry_sequence_breakers": self.dry_sequence_breakers,
            "samplers": self.samplers,
        }

    async def _check_health(self) -> None:
        if self._http is None:
            raise RuntimeError("LlamaCPPT2T server is not running")
        try:
            health_resp = await self._http.get("/health", timeout=5.0)
            health_resp.raise_for_status()
        except httpx.HTTPError as e:
            raise RuntimeError(f"LlamaCPPT2T server health check failed: {e}") from e

    def _chat_messages(self, instruction_prompt: str, messages: list) -> list[dict[str, str]]:
        history = [{"role": "system", "content": instruction_prompt}]
        for msg in messages:
            if isinstance(msg, ChatMessage) and msg.user == self.prompter.character_name:
                history.append({"role": "assistant", "content": msg.message})
            else:
                history.append({"role": "user", "content": msg.to_line()})
        return history

    async def _apply_chat_template(self, messages: list[dict[str, str]]) -> str:
        response = await self._http.post("/apply-template", json={"messages": messages})
        response.raise_for_status()
        prompt = response.json().get("prompt")
        if not prompt:
            raise RuntimeError("LlamaCPPT2T /apply-template returned no prompt")
        return prompt

    def _completion_payload(self, prompt: str) -> dict:
        payload = {
            "prompt": prompt,
            "stream": True,
            "n_predict": self.n_predict,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "min_p": self.min_p,
            "typical_p": self.typical_p,
            "repeat_penalty": self.repeat_penalty,
            "repeat_last_n": self.repeat_last_n,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "dry_multiplier": self.dry_multiplier,
            "dry_base": self.dry_base,
            "dry_allowed_length": self.dry_allowed_length,
            "dry_penalty_last_n": self.dry_penalty_last_n,
            "dry_sequence_breakers": self.dry_sequence_breakers,
            "samplers": self.samplers,
        }
        if self.mcp_json_schema is not None:
            payload["json_schema"] = self.mcp_json_schema
        return payload

    async def _iter_completion_stream(self, prompt: str):
        payload = self._completion_payload(prompt)
        async with self._http.stream("POST", "/completion", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                data = line.removeprefix("data:").strip()
                if not data or data == "[DONE]":
                    if data == "[DONE]":
                        break
                    continue
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if event.get("stop"):
                    break
                content = event.get("content")
                if content:
                    yield content

    async def _generate(self, instruction_prompt: str = None, messages: list = None, **kwargs):
        if self.prompter is None:
            raise RuntimeError("LlamaCPPT2T missing runtime dependency: prompter")

        await self._check_health()

        chat_messages = self._chat_messages(instruction_prompt, messages)
        try:
            prompt = await self._apply_chat_template(chat_messages)
            async for content_chunk in self._iter_completion_stream(prompt):
                yield {"content": content_chunk}
        except httpx.HTTPError as e:
            raise Exception(f"Failed to get T2T result: {e}") from e
