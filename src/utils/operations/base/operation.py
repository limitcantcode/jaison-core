from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from .error import CloseInactiveError, StartActiveError, UsedInactiveError


class Operation:
    def __init__(self, op_type: str, op_id: str):
        self.op_type = op_type
        self.op_id = op_id

        self.active = False
        self.process_manager: ProcessManager | None = None
        self.prompter: Prompter | None = None

    def bind_runtime(
        self, process_manager: ProcessManager | None = None, prompter: Prompter | None = None
    ) -> Operation:
        self.process_manager = process_manager
        self.prompter = prompter
        return self

    async def __call__(self, chunk_in: dict[str, Any]) -> AsyncGenerator[dict[str, Any], None]:
        """Generates a stream of chunks similar to chunk_in but augmented with new data"""
        if not self.active:
            raise UsedInactiveError(self.op_type, self.op_id)
        start_time = time.perf_counter()

        kwargs = await self._parse_chunk(chunk_in)

        async for chunk_out in self._generate(**kwargs):
            # yield chunk_in | chunk_out
            yield chunk_out
        end_time = time.perf_counter()
        logging.info(
            f"{self.op_type} operation {self.op_id} completed in {(end_time - start_time) * 1000} ms"
        )

    ## TO BE OVERRIDEN ####
    async def start(self) -> None:
        """General setup needed to start generated"""
        if self.active:
            raise StartActiveError(self.op_type, self.op_id)
        logging.info(f"Starting {self.op_type} operation {self.op_id}")
        self.active = True

    async def close(self) -> None:
        """Clean up resources before unloading"""
        if not self.active:
            raise CloseInactiveError(self.op_type, self.op_id)
        logging.info(f"Closing {self.op_type} operation {self.op_id}")
        self.active = False

    ## TO BE IMPLEMENTED ####
    async def configure(self, config_d: dict[str, Any]):
        """Configure and validate operation-specific configuration"""
        raise NotImplementedError

    async def get_configuration(self) -> dict[str, Any]:
        """Returns values of configurable fields"""
        raise NotImplementedError

    async def _parse_chunk(self, chunk_in: dict[str, Any]) -> dict[str, Any]:
        """Extract information from input for use in _generate"""
        raise NotImplementedError

    async def _generate(self, **kwargs) -> AsyncGenerator[dict[str, Any], None]:
        """Generate a output stream"""
        raise NotImplementedError
