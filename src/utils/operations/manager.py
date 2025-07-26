from enum import Enum
from typing import Dict, List, AsyncGenerator, Any

from .error import UnknownOpType, UnknownOpRole, UnknownOpID, DuplicateFilter, OperationUnloaded
from .base import Operation
from utils.helpers.singleton import Singleton
from utils.config import Config

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
    
def role_to_type(op_role: OpRoles) -> OpTypes:
    match op_role:
        case OpRoles.STT:
            return OpTypes.STT
        case OpRoles.MCP:
            return OpTypes.T2T
        case OpRoles.T2T:
            return OpTypes.T2T
        case OpRoles.TTS:
            return OpTypes.TTS
        case OpRoles.FILTER_AUDIO:
            return OpTypes.FILTER_AUDIO
        case OpRoles.FILTER_TEXT:
            return OpTypes.FILTER_TEXT
        case OpRoles.EMBEDDING:
            return OpTypes.EMBEDDING
        case _:
            raise UnknownOpRole(op_role)
    
    
def load_op(op_type: OpTypes, op_id: str):
    '''
    Return an operation, but do not saved to OperationManager
    
    Starting, usage and eventual closing of this operation is deferred to the caller.
    This is mainly used for temporarily loading an operation to be used, such
    as a filter used as a one-time preview and not intended to last whole session
    '''
    match op_type:
        case OpTypes.STT:
            if op_id == "fish":
                from .stt.fish import FishSTT
                return FishSTT()
            elif op_id == "azure":
                from .stt.azure import AzureSTT
                return AzureSTT()
            elif op_id == "openai":
                from .stt.openai import OpenAISTT
                return OpenAISTT()
            elif op_id == "kobold":
                from .stt.kobold import KoboldSTT
                return KoboldSTT()
            else:
                raise UnknownOpID("STT", op_id)
        case OpTypes.T2T:
            if op_id == "openai":
                from .t2t.openai import OpenAIT2T
                return OpenAIT2T()
            elif op_id == "kobold":
                from .t2t.kobold import KoboldT2T
                return KoboldT2T()
            else:
                raise UnknownOpID("T2T", op_id)
        case OpTypes.TTS:
            if op_id == "azure":
                from .tts.azure import AzureTTS
                return AzureTTS()
            elif op_id == "fish":
                from .tts.fish import FishTTS
                return FishTTS()
            elif op_id == "openai":
                from .tts.openai import OpenAITTS
                return OpenAITTS()
            elif op_id == "kobold":
                from .tts.kobold import KoboldTTS
                return KoboldTTS()
            elif op_id == "melo":
                from .tts.melo import MeloTTS
                return MeloTTS()
            elif op_id == "pytts":
                from .tts.pytts import PyttsTTS
                return PyttsTTS()
            else:
                raise UnknownOpID("TTS", op_id)
        case OpTypes.FILTER_AUDIO:
            if op_id == "rvc":
                from .filter_audio.rvc import RVCFilter
                return RVCFilter()
            elif op_id == "pitch":
                from .filter_audio.pitch import PitchFilter
                return PitchFilter()
            else:
                raise UnknownOpID("FILTER_AUDIO", op_id)
        case OpTypes.FILTER_TEXT:
            if op_id == "chunker_sentence":
                from .filter_text.chunker_sentence import SentenceChunkerFilter
                return SentenceChunkerFilter()
            elif op_id == "emotion_roberta":
                from .filter_text.emotion_roberta import RobertaEmotionFilter
                return RobertaEmotionFilter()
            elif op_id == "mod_koala":
                from .filter_text.mod_koala import KoalaModerationFilter
                return KoalaModerationFilter()
            elif op_id == "filter_clean":
                from .filter_text.filter_clean import ResponseCleaningFilter
                return ResponseCleaningFilter()
            else:
                raise UnknownOpID("FILTER_TEXT", op_id)
        case OpTypes.EMBEDDING:
            if op_id == "openai":
                from .embedding.openai import OpenAIEmbedding
                return OpenAIEmbedding()
            else:
                raise UnknownOpID("EMBEDDING", op_id)
        case _:
            # Should never get here if op_role is indeed OpRole
            raise UnknownOpRole(op_type)
    
class OperationManager(metaclass=Singleton):
    def __init__(self):
        self.stt = None
        self.mcp = None
        self.t2t = None
        self.tts = None
        self.filter_audio = list()
        self.filter_text = list()
        self.embedding = None

    def get_operation(self, op_role: OpRoles) -> Operation:
        match op_role:
            case OpRoles.STT:
                return self.stt
            case OpRoles.MCP:
                return self.mcp
            case OpRoles.T2T:
                return self.t2t
            case OpRoles.TTS:
                return self.tts
            case OpRoles.FILTER_AUDIO:
                return self.filter_audio
            case OpRoles.FILTER_TEXT:
                return self.filter_text
            case OpRoles.EMBEDDING:
                return self.embedding
            case _:
                # Should never get here if op_role is indeed OpRoles
                raise UnknownOpRole(op_role)
            
    def get_operation_all(self) -> Dict[str, Operation | List[Operation]]:
        return {
            "stt": self.get_operation(OpRoles.STT),
            "mcp": self.get_operation(OpRoles.MCP),
            "t2t": self.get_operation(OpRoles.T2T),
            "tts": self.get_operation(OpRoles.TTS),
            "filter_audio": self.get_operation(OpRoles.FILTER_AUDIO),
            "filter_text": self.get_operation(OpRoles.FILTER_TEXT),
            "embedding": self.get_operation(OpRoles.EMBEDDING),
        }
        
    async def get_configuration(
        self,
        op_role: OpRoles,
        op_id: str = None
    ):
        '''Get configuration for a loaded operation'''
        match op_role:
            case OpRoles.STT:
                if not self.stt:
                    raise OperationUnloaded("STT")
                elif op_id and self.stt and self.stt.op_id != op_id:
                    raise OperationUnloaded("STT", op_id=op_id)
                
                return await self.stt.get_configuration()
            case OpRoles.MCP:
                if not self.mcp:
                    raise OperationUnloaded("MCP")
                elif op_id and self.mcp and self.mcp.op_id != op_id:
                    raise OperationUnloaded("MCP", op_id=op_id)
                
                return await self.mcp.get_configuration()
            case OpRoles.T2T:
                if not self.t2t:
                    raise OperationUnloaded("T2T")
                elif op_id and self.t2t and self.t2t.op_id != op_id:
                    raise OperationUnloaded("T2T", op_id=op_id)
                
                return await self.t2t.get_configuration()
            case OpRoles.TTS:
                if not self.tts:
                    raise OperationUnloaded("TTS")
                elif op_id and self.tts and self.tts.op_id != op_id:
                    raise OperationUnloaded("TTS", op_id=op_id)
                
                return await self.tts.get_configuration()
            case OpRoles.FILTER_AUDIO:
                assert op_id is not None
                
                for op in self.filter_audio:
                    if op.op_id == op_id:
                        return await op.get_configuration()
                raise OperationUnloaded("FILTER_AUDIO", op_id=op_id)
            case OpRoles.FILTER_TEXT:
                assert op_id is not None
                
                for op in self.filter_text:
                    if op.op_id == op_id:
                        return await op.get_configuration()
                raise OperationUnloaded("FILTER_AUDIO", op_id=op_id)
            case OpRoles.EMBEDDING:
                if not self.embedding:
                    raise OperationUnloaded("EMBEDDING")
                elif op_id and self.embedding and self.embedding.op_id != op_id:
                    raise OperationUnloaded("EMBEDDING", op_id=op_id)
                
                return await self.embedding.get_configuration()
            case _:
                # Should never get here if op_role is indeed OpRoles
                raise UnknownOpRole(op_role)
        
    async def load_operation(self, op_role: OpRoles, op_id: str, op_details: Dict[str, Any]) -> None:
        '''Load, start, and save an Operation in the OperationManager'''
        if op_role == OpRoles.FILTER_AUDIO:
            for op in self.filter_audio:
                if op.op_id == op_id: raise DuplicateFilter("FILTER_AUDIO", op_id)
        if op_role == OpRoles.FILTER_TEXT:
            for op in self.filter_text:
                if op.op_id == op_id: raise DuplicateFilter("FILTER_TEXT", op_id)
                
        new_op = load_op(role_to_type(op_role), op_id)
        await new_op.configure(op_details)
        await new_op.start()
        
        match op_role:
            case OpRoles.STT:
                if self.stt: await self.stt.close()
                self.stt = new_op
            case OpRoles.MCP:
                if self.mcp: await self.mcp.close()
                self.mcp = new_op
            case OpRoles.T2T:
                if self.t2t: await self.t2t.close()
                self.t2t = new_op
            case OpRoles.TTS:
                if self.tts: await self.tts.close()
                self.tts = new_op
            case OpRoles.FILTER_AUDIO:
                self.filter_audio.append(new_op)
            case OpRoles.FILTER_TEXT:
                self.filter_text.append(new_op)
            case OpRoles.EMBEDDING:
                if self.embedding: await self.embedding.close()
                self.embedding = new_op
            case _:
                # Should never get here if op_role is indeed OpRoles
                raise UnknownOpRole(op_role)
        
    async def load_operations_from_config(self) -> None:
        '''Load, start, and save all operations specified in config in the OperationManager'''
        config = Config()
        
        await self.close_operation_all()
        
        operations = Config().operations
        for op_details in operations:
            op_role = OpRoles(op_details['role'])
            op_id = op_details['id']
            await self.load_operation(op_role, op_id, op_details)
        
    async def close_operation(self, op_role: OpRoles, op_id: str = None) -> None:
        match op_role:
            case OpRoles.STT:
                if not self.stt:
                    raise OperationUnloaded("STT")
                elif op_id and self.stt and self.stt.op_id != op_id:
                    raise OperationUnloaded("STT", op_id=op_id)
                
                await self.stt.close()
                self.stt = None
            case OpRoles.T2T:
                if not self.mcp:
                    raise OperationUnloaded("MCP")
                elif op_id and self.mcp and self.mcp.op_id != op_id:
                    raise OperationUnloaded("MCP", op_id=op_id)
                
                await self.mcp.close()
                self.mcp = None
            case OpRoles.T2T:
                if not self.t2t:
                    raise OperationUnloaded("T2T")
                elif op_id and self.t2t and self.t2t.op_id != op_id:
                    raise OperationUnloaded("T2T", op_id=op_id)
                
                await self.t2t.close()
                self.t2t = None
            case OpRoles.TTS:
                if not self.tts:
                    raise OperationUnloaded("TTS")
                elif op_id and self.tts and self.tts.op_id != op_id:
                    raise OperationUnloaded("TTS", op_id=op_id)
                
                await self.tts.close()
                self.tts = None
            case OpRoles.FILTER_AUDIO:
                for op in self.filter_audio:
                    if op.op_id == op_id:
                        await op.close()
                        self.filter_audio.remove(op)
                        return
                raise OperationUnloaded("FILTER_AUDIO", op_id=op_id)
            case OpRoles.FILTER_TEXT:
                for op in self.filter_text:
                    if op.op_id == op_id:
                        await op.close()
                        self.filter_text.remove(op)
                        return
                raise OperationUnloaded("FILTER_TEXT", op_id=op_id)
            case OpRoles.EMBEDDING:
                if not self.embedding:
                    raise OperationUnloaded("EMBEDDING")
                elif op_id and self.embedding and self.embedding.op_id != op_id:
                    raise OperationUnloaded("EMBEDDING", op_id=op_id)
                
                await self.embedding.close()
                self.embedding = None
            case _:
                # Should never get here if op_role is indeed OpRoles
                raise UnknownOpRole(op_role)
            
    async def close_operation_all(self):
        if self.stt:
            await self.stt.close()
            self.stt = None
        if self.mcp:
            await self.mcp.close()
            self.mcp = None
        if self.t2t:
            await self.t2t.close()
            self.t2t = None
        if self.tts:
            await self.tts.close()
            self.tts = None
        for op in self.filter_audio:
            await op.close()
        self.filter_audio.clear()
        for op in self.filter_text:
            await op.close()
        self.filter_text.clear()
        if self.embedding:
            await self.embedding.close()
            self.embedding = None
        
    async def configure(self,
        op_role: OpRoles,
        config_d: Dict[str, Any],
        op_id: str = None
    ):
        '''Configure an operation that has already been loaded prior'''
        match op_role:
            case OpRoles.STT:
                if not self.stt:
                    raise OperationUnloaded("STT")
                elif op_id and self.stt and self.stt.op_id != op_id:
                    raise OperationUnloaded("STT", op_id=op_id)
                
                return await self.stt.configure(config_d)
            case OpRoles.MCP:
                if not self.mcp:
                    raise OperationUnloaded("MCP")
                elif op_id and self.mcp and self.mcp.op_id != op_id:
                    raise OperationUnloaded("MCP", op_id=op_id)
                
                return await self.mcp.configure(config_d)
            case OpRoles.T2T:
                if not self.t2t:
                    raise OperationUnloaded("T2T")
                elif op_id and self.t2t and self.t2t.op_id != op_id:
                    raise OperationUnloaded("T2T", op_id=op_id)
                
                return await self.t2t.configure(config_d)
            case OpRoles.TTS:
                if not self.tts:
                    raise OperationUnloaded("TTS")
                elif op_id and self.tts and self.tts.op_id != op_id:
                    raise OperationUnloaded("TTS", op_id=op_id)
                
                return await self.tts.configure(config_d)
            case OpRoles.FILTER_AUDIO:
                assert op_id is not None
                
                for op in self.filter_audio:
                    if op.op_id == op_id:
                        return await op.configure(config_d)
                raise OperationUnloaded("FILTER_AUDIO", op_id=op_id)
            case OpRoles.FILTER_TEXT:
                assert op_id is not None
                
                for op in self.filter_text:
                    if op.op_id == op_id:
                        return await op.configure(config_d)
                raise OperationUnloaded("FILTER_TEXT", op_id=op_id)
            case OpRoles.EMBEDDING:
                if not self.embedding:
                    raise OperationUnloaded("EMBEDDING")
                elif op_id and self.embedding and self.embedding.op_id != op_id:
                    raise OperationUnloaded("EMBEDDING", op_id=op_id)
                
                return await self.embedding.configure(config_d)
            case _:
                # Should never get here if op_role is indeed OpRoles
                raise UnknownOpRole(op_role)
        
    async def _use_filter(self, filter_list: List[Operation], filter_idx: int, chunk_in: Dict[str, Any]):
        if filter_idx == len(filter_list): yield chunk_in
        elif filter_idx < len(filter_list)-1: # Not last filter
            async for result_chunk in filter_list[filter_idx](chunk_in):
                async for chunk_out in self._use_filter(filter_list, filter_idx+1, result_chunk):
                    yield chunk_out
        else: # Is last filter
            async for chunk_out in filter_list[filter_idx](chunk_in):
                yield chunk_out
            
    def use_operation(
        self,
        op_role: OpRoles,
        chunk_in: Dict[str, Any],
        op_id: str = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        '''Use an operation that has already been loaded prior'''
        match op_role:
            case OpRoles.STT:
                if not self.stt:
                    raise OperationUnloaded("STT")
                elif op_id and self.stt and self.stt.op_id != op_id:
                    raise OperationUnloaded("STT", op_id=op_id)
                
                return self.stt(chunk_in)
            case OpRoles.MCP:
                if not self.mcp:
                    raise OperationUnloaded("MCP")
                elif op_id and self.mcp and self.mcp.op_id != op_id:
                    raise OperationUnloaded("MCP", op_id=op_id)
                
                return self.mcp(chunk_in)
            case OpRoles.T2T:
                if not self.t2t:
                    raise OperationUnloaded("T2T")
                elif op_id and self.t2t and self.t2t.op_id != op_id:
                    raise OperationUnloaded("T2T", op_id=op_id)
                
                return self.t2t(chunk_in)
            case OpRoles.TTS:
                if not self.tts:
                    raise OperationUnloaded("TTS")
                elif op_id and self.tts and self.tts.op_id != op_id:
                    raise OperationUnloaded("TTS", op_id=op_id)
                
                return self.tts(chunk_in)
            case OpRoles.FILTER_AUDIO:
                if op_id:
                    for op in self.filter_audio:
                        if op.op_id == op_id:
                            return op(chunk_in)
                    raise OperationUnloaded("FILTER_AUDIO", op_id=op_id)
                else:
                    return self._use_filter(self.filter_audio, 0, chunk_in)
            case OpRoles.FILTER_TEXT:
                if op_id:
                    for op in self.filter_text:
                        if op.op_id == op_id:
                            return op(chunk_in)
                    raise OperationUnloaded("FILTER_TEXT", op_id=op_id)
                else:
                    return self._use_filter(self.filter_text, 0, chunk_in)
            case OpRoles.EMBEDDING:
                if not self.embedding:
                    raise OperationUnloaded("EMBEDDING")
                elif op_id and self.embedding and self.embedding.op_id != op_id:
                    raise OperationUnloaded("EMBEDDING", op_id=op_id)
                
                return self.embedding(chunk_in)
            case _:
                # Should never get here if op_role is indeed OpRoles
                raise UnknownOpType(op_role)
