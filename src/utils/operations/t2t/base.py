"""
T2T Operations (at minimum) require the following fields for input chunks:
- system_prompt: (str) System prompt text
- user_prompt: (str) User prompt text

Adds to chunk:
- content: (str) Generated text
"""

from collections.abc import AsyncGenerator
from typing import Any

from ..base import Operation


class T2TOperation(Operation):
    def __init__(self, op_id: str):
        super().__init__("T2T", op_id)
        # Set by the MCP client at runtime (not user YAML); constrains MCP tool-call output.
        self.mcp_json_schema: dict[str, Any] | None = None

    ## TO BE OVERRIDEN ####
    async def start(self) -> None:
        """General setup needed to start generated"""
        await super().start()

    async def close(self) -> None:
        """Clean up resources before unloading"""
        await super().close()

    async def _parse_chunk(self, chunk_in: dict[str, Any]) -> dict[str, Any]:
        """Extract information from input for use in _generate"""
        # assert "system_prompt" in chunk_in
        # assert isinstance(chunk_in["system_prompt"], str)
        # assert len(chunk_in["system_prompt"]) > 0
        # assert "user_prompt" in chunk_in
        # assert isinstance(chunk_in["user_prompt"], str)
        # assert len(chunk_in["user_prompt"]) > 0

        # return {
        #     "system_prompt": chunk_in["system_prompt"],
        #     "user_prompt": chunk_in["user_prompt"],
        # }

        assert "instruction_prompt" in chunk_in
        assert isinstance(chunk_in["instruction_prompt"], str)
        assert "messages" in chunk_in
        assert isinstance(chunk_in["messages"], list)

        return {
            "instruction_prompt": chunk_in["instruction_prompt"],
            "messages": chunk_in["messages"],
        }

    ## TO BE IMPLEMENTED ####
    async def configure(self, config_d: dict[str, Any]):
        """Configure and validate operation-specific configuration"""
        raise NotImplementedError

    async def get_configuration(self) -> dict[str, Any]:
        """Returns values of configurable fields"""
        raise NotImplementedError

    async def _generate(
        self, instruction_prompt: str = None, messages: list = None, **kwargs
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Generate a output stream"""
        raise NotImplementedError

        yield {"content": "example generated text"}

    def set_mcp_json_schema(self, schema: dict[str, Any] | None) -> None:
        """Apply a JSON schema for MCP structured output (provided by the MCP client)."""
        if schema is not None:
            assert isinstance(schema, dict)
        self.mcp_json_schema = schema
