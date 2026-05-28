from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

from .base import Operation
from .embedding.base import EmbeddingOperation
from .embedding.llamacpp import LlamaCPPEmbedding
from .embedding.openai import OpenAIEmbedding
from .error import DuplicateFilter, OperationUnloaded, UnknownOpID, UnknownOpRole, UnknownOpType
from .filter_audio.base import FilterAudioOperation
from .filter_audio.pitch import PitchFilter
from .filter_audio.rvc import RVCFilter
from .filter_text.base import FilterTextOperation
from .filter_text.chunker_sentence import SentenceChunkerFilter
from .filter_text.emotion_roberta import RobertaEmotionFilter
from .filter_text.filter_clean import ResponseCleaningFilter
from .filter_text.mod_koala import KoalaModerationFilter
from .stt.azure import AzureSTT
from .stt.base import STTOperation
from .stt.fish import FishSTT
from .stt.openai import OpenAISTT
from .stt.whispercpp import WhisperCPPSTT
from .t2t.base import T2TOperation
from .t2t.llamacpp import LlamaCPPT2T
from .t2t.openai import OpenAIT2T
from .tts.azure import AzureTTS
from .tts.base import TTSOperation
from .tts.fish import FishTTS
from .tts.melo import MeloTTS
from .tts.openai import OpenAITTS
from .tts.pytts import PyttsTTS


class OpTypes(Enum):
    STT = "stt"
    T2T = "t2t"
    TTS = "tts"
    FILTER_AUDIO = "filter_audio"
    FILTER_TEXT = "filter_text"
    EMBEDDING = "embedding"


class OpRoles(Enum):
    STT = "stt"
    MCP = "mcp"
    T2T = "t2t"
    TTS = "tts"
    FILTER_AUDIO = "filter_audio"
    FILTER_TEXT = "filter_text"
    EMBEDDING = "embedding"


ROLE_TO_TYPE: dict[OpRoles, OpTypes] = {
    OpRoles.STT: OpTypes.STT,
    OpRoles.MCP: OpTypes.T2T,
    OpRoles.T2T: OpTypes.T2T,
    OpRoles.TTS: OpTypes.TTS,
    OpRoles.FILTER_AUDIO: OpTypes.FILTER_AUDIO,
    OpRoles.FILTER_TEXT: OpTypes.FILTER_TEXT,
    OpRoles.EMBEDDING: OpTypes.EMBEDDING,
}

OP_CLASSES: dict[OpTypes, dict[str, type[Operation]]] = {
    OpTypes.STT: {
        "fish": FishSTT,
        "azure": AzureSTT,
        "openai": OpenAISTT,
        "whispercpp": WhisperCPPSTT,
    },
    OpTypes.T2T: {
        "openai": OpenAIT2T,
        "llamacpp": LlamaCPPT2T,
    },
    OpTypes.TTS: {
        "azure": AzureTTS,
        "fish": FishTTS,
        "openai": OpenAITTS,
        "melo": MeloTTS,
        "pytts": PyttsTTS,
    },
    OpTypes.FILTER_AUDIO: {
        "rvc": RVCFilter,
        "pitch": PitchFilter,
    },
    OpTypes.FILTER_TEXT: {
        "chunker_sentence": SentenceChunkerFilter,
        "emotion_roberta": RobertaEmotionFilter,
        "mod_koala": KoalaModerationFilter,
        "filter_clean": ResponseCleaningFilter,
    },
    OpTypes.EMBEDDING: {
        "openai": OpenAIEmbedding,
        "llamacpp": LlamaCPPEmbedding,
    },
}


def role_to_type(op_role: OpRoles) -> OpTypes:
    try:
        return ROLE_TO_TYPE[op_role]
    except KeyError:
        raise UnknownOpRole(op_role) from None


def load_op(op_type: OpTypes, op_id: str) -> Operation:
    """
    Return an operation, but do not saved to OperationManager

    Starting, usage and eventual closing of this operation is deferred to the caller.
    This is mainly used for temporarily loading an operation to be used, such
    as a filter used as a one-time preview and not intended to last whole session
    """
    try:
        op_class = OP_CLASSES[op_type][op_id]
    except KeyError:
        raise UnknownOpID(op_type.name, op_id) from None
    return op_class()


_T = TypeVar("_T")


@dataclass(frozen=True)
class OpRoleSlot:
    attr: str
    multi: bool = False


ROLE_SLOTS: dict[OpRoles, OpRoleSlot] = {
    OpRoles.STT: OpRoleSlot("stt"),
    OpRoles.MCP: OpRoleSlot("mcp"),
    OpRoles.T2T: OpRoleSlot("t2t"),
    OpRoles.TTS: OpRoleSlot("tts"),
    OpRoles.FILTER_AUDIO: OpRoleSlot("filter_audio", multi=True),
    OpRoles.FILTER_TEXT: OpRoleSlot("filter_text", multi=True),
    OpRoles.EMBEDDING: OpRoleSlot("embedding"),
}


class OperationManager:
    def __init__(self, prompter: "Prompter"):
        self.prompter = prompter
        self.stt: STTOperation | None = None
        self.mcp: T2TOperation | None = None
        self.t2t: T2TOperation | None = None
        self.tts: TTSOperation | None = None
        self.filter_audio: list[FilterAudioOperation] = []
        self.filter_text: list[FilterTextOperation] = []
        self.embedding: EmbeddingOperation | None = None

    @staticmethod
    def _slot(op_role: OpRoles) -> OpRoleSlot:
        try:
            return ROLE_SLOTS[op_role]
        except KeyError:
            raise UnknownOpRole(op_role) from None

    def _storage(self, op_role: OpRoles) -> Operation | list[Operation] | None:
        return getattr(self, self._slot(op_role).attr)

    def _resolve_operation(
        self, op_role: OpRoles, op_id: str | None = None, *, require_id: bool = False
    ) -> Operation:
        slot = self._slot(op_role)
        label = op_role.name

        if slot.multi:
            if require_id:
                assert op_id is not None
            if op_id is None:
                raise OperationUnloaded(label)
            for op in getattr(self, slot.attr):
                if op.op_id == op_id:
                    return op
            raise OperationUnloaded(label, op_id=op_id)

        op: Operation | None = getattr(self, slot.attr)
        if not op:
            raise OperationUnloaded(label)
        if op_id is not None and op.op_id != op_id:
            raise OperationUnloaded(label, op_id=op_id)
        return op

    async def _act_on_loaded_operation(
        self, op_role: OpRoles, op_id: str, action: Callable[[Operation], Awaitable[_T]]
    ) -> _T:
        op = self._resolve_operation(op_role, op_id, require_id=self._slot(op_role).multi)
        return await action(op)

    def get_operation(self, op_role: OpRoles) -> Operation | list[Operation] | None:
        return self._storage(op_role)

    def get_operation_all(self) -> dict[str, Operation | list[Operation] | None]:
        return {role.value: self.get_operation(role) for role in OpRoles}

    async def get_configuration(self, op_role: OpRoles, op_id: str = None):
        """Get configuration for a loaded operation"""
        return await self._act_on_loaded_operation(
            op_role, op_id, lambda op: op.get_configuration()
        )

    def _bind_runtime(self, op: Operation) -> Operation:
        return op.bind_runtime(prompter=self.prompter)

    def loose_load_operation(self, op_role: OpRoles, op_id: str) -> Operation:
        return self._bind_runtime(load_op(role_to_type(op_role), op_id))

    async def load_operation(
        self, op_role: OpRoles, op_id: str, op_details: dict[str, Any]
    ) -> None:
        """Load, start, and save an Operation in the OperationManager"""
        slot = self._slot(op_role)
        if slot.multi:
            for op in getattr(self, slot.attr):
                if op.op_id == op_id:
                    raise DuplicateFilter(op_role.name, op_id)

        new_op = self._bind_runtime(load_op(role_to_type(op_role), op_id))
        await new_op.configure(op_details)
        await new_op.start()

        if slot.multi:
            getattr(self, slot.attr).append(new_op)
            return

        current: Operation | None = getattr(self, slot.attr)
        if current:
            await current.close()
        setattr(self, slot.attr, new_op)

    async def close_operation(self, op_role: OpRoles, op_id: str = None) -> None:
        slot = self._slot(op_role)
        label = op_role.name

        if slot.multi:
            ops: list[Operation] = getattr(self, slot.attr)
            for op in ops:
                if op.op_id == op_id:
                    await op.close()
                    ops.remove(op)
                    return
            raise OperationUnloaded(label, op_id=op_id)

        op: Operation | None = getattr(self, slot.attr)
        if not op:
            raise OperationUnloaded(label)
        if op_id is not None and op.op_id != op_id:
            raise OperationUnloaded(label, op_id=op_id)
        await op.close()
        setattr(self, slot.attr, None)

    async def close_operation_all(self) -> None:
        for slot in ROLE_SLOTS.values():
            storage = getattr(self, slot.attr)
            if slot.multi:
                for op in storage:
                    await op.close()
                storage.clear()
            elif storage is not None:
                await storage.close()
                setattr(self, slot.attr, None)

    async def configure(self, op_role: OpRoles, config_d: dict[str, Any], op_id: str = None):
        """Configure an operation that has already been loaded prior"""
        return await self._act_on_loaded_operation(
            op_role, op_id, lambda op: op.configure(config_d)
        )

    async def _use_filter(
        self, filter_list: list[Operation], filter_idx: int, chunk_in: dict[str, Any]
    ):
        if filter_idx >= len(filter_list):
            yield chunk_in
        elif filter_idx < len(filter_list) - 1:  # Not last filter
            async for result_chunk in filter_list[filter_idx](chunk_in):
                async for chunk_out in self._use_filter(filter_list, filter_idx + 1, result_chunk):
                    yield chunk_out
        else:  # Is last filter
            async for chunk_out in filter_list[filter_idx](chunk_in):
                yield chunk_out

    def use_operation(
        self, op_role: OpRoles, chunk_in: dict[str, Any], op_id: str = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Use an operation that has already been loaded prior"""
        slot = self._slot(op_role)
        if slot.multi and op_id is None:
            return self._use_filter(getattr(self, slot.attr), 0, chunk_in)
        return self._resolve_operation(op_role, op_id)(chunk_in)
