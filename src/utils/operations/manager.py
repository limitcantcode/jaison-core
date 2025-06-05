from enum import Enum
from typing import Dict, List, AsyncGenerator, Any

from .error import UnknownOpType, UnknownOpID, DuplicateFilter, OperationUnloaded
from .base import Operation
from utils.config import Config

class OpTypes(Enum):
    STT = "stt"
    T2T = "t2t"
    TTS = "tts"
    FILTER_AUDIO = "filter_audio"
    FILTER_TEXT = "filter_text"
    
class OperationManager:
    def __init__(self):
        self.stt = None
        self.t2t = None
        self.tts = None
        self.filter_audio = list()
        self.filter_text = list()
        
        self.loose_loaded_ops = dict()
        
    def get_operation(self, op_type: OpTypes) -> Operation:
        match op_type:
            case OpTypes.STT:
                return self.stt
            case OpTypes.T2T:
                return self.t2t
            case OpTypes.TTS:
                return self.tts
            case OpTypes.FILTER_AUDIO:
                return self.filter_audio
            case OpTypes.FILTER_TEXT:
                return self.filter_text
            case _:
                # Should never get here if op_type is indeed OpTypes
                raise UnknownOpType(op_type)
            
    def get_operation_all(self) -> Dict[str, Operation | List[Operation]]:
        return {
            "stt": self.get_operation(OpTypes.STT),
            "t2t": self.get_operation(OpTypes.T2T),
            "tts": self.get_operation(OpTypes.TTS),
            "filter_audio": self.get_operation(OpTypes.FILTER_AUDIO),
            "filter_text": self.get_operation(OpTypes.FILTER_TEXT),
        }
        
    def _loose_load_operation(
        self,
        op_type: OpTypes,
        op_id: str = None
    ) -> Operation:
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
            case _:
                # Should never get here if op_type is indeed OpTypes
                raise UnknownOpType(op_type)
    
    async def loose_load_operation(self, op_type: OpTypes, op_id: str, loose_key: str):
        if loose_key in self.loose_loaded_ops:
            await self.loose_loaded_ops[loose_key].close()
        self.loose_loaded_ops[loose_key] = self._loose_load_operation(op_type, op_id)
        
    async def load_operation(self, op_type: OpTypes, op_id: str) -> None:
        '''Load, start, and save an Operation in the OperationManager'''
        if op_type == OpTypes.FILTER_AUDIO:
            for op in self.filter_audio:
                if op.op_id == op_id: raise DuplicateFilter("FILTER_AUDIO", op_id)
        if op_type == OpTypes.FILTER_TEXT:
            for op in self.filter_text:
                if op.op_id == op_id: raise DuplicateFilter("FILTER_TEXT", op_id)
                
        new_op = self._loose_load_operation(op_type, op_id)
        await new_op.start()
        
        match op_type:
            case OpTypes.STT:
                if self.stt: await self.stt.close()
                self.stt = new_op
            case OpTypes.T2T:
                if self.t2t: await self.t2t.close()
                self.t2t = new_op
            case OpTypes.TTS:
                if self.tts: await self.tts.close()
                self.tts = new_op
            case OpTypes.FILTER_AUDIO:
                self.filter_audio.append(new_op)
            case OpTypes.FILTER_TEXT:
                self.filter_text.append(new_op)
            case _:
                # Should never get here if op_type is indeed OpTypes
                raise UnknownOpType(op_type)
        
    async def load_operations_from_config(self) -> None:
        '''Load, start, and save all operations specified in config in the OperationManager'''
        config = Config()
        
        await self.close_operation_all()
        
        if config.op_stt_id: self.load_operation(OpTypes.STT, config.op_stt_id)
        if config.op_t2t_id: self.load_operation(OpTypes.T2T, config.op_t2t_id)
        if config.op_tts_id: self.load_operation(OpTypes.TTS, config.op_tts_id)
        for op_id in config.op_filter_audio_id:
            self.load_operation(OpTypes.FILTER_AUDIO, op_id)
        for op_id in config.op_filter_text_id:
            self.load_operation(OpTypes.FILTER_TEXT, op_id)
        
    async def close_loose_operation(self, loose_key: str) -> None:
        if loose_key in self.loose_loaded_ops:
            await self.loose_loaded_ops[loose_key].close()
        else:
            raise OperationUnloaded("LOOSE", op_id=loose_key)
        
    async def close_operation(self, op_type: OpTypes, op_id: str = None) -> None:
        match op_type:
            case OpTypes.STT:
                if not self.stt:
                    raise OperationUnloaded("STT")
                elif op_id and self.stt and self.stt.op_id != op_id:
                    raise OperationUnloaded("STT", op_id=op_id)
                
                await self.stt.close()
                self.stt = None
            case OpTypes.T2T:
                if not self.t2t:
                    raise OperationUnloaded("T2T")
                elif op_id and self.t2t and self.t2t.op_id != op_id:
                    raise OperationUnloaded("T2T", op_id=op_id)
                
                await self.t2t.close()
                self.t2t = None
            case OpTypes.TTS:
                if not self.tts:
                    raise OperationUnloaded("TTS")
                elif op_id and self.tts and self.tts.op_id != op_id:
                    raise OperationUnloaded("TTS", op_id=op_id)
                
                await self.tts.close()
                self.tts = None
            case OpTypes.FILTER_AUDIO:
                for op in self.filter_audio:
                    if op.op_id == op_id:
                        await op.close()
                        self.filter_audio.remove(op)
                        return
                raise OperationUnloaded("FILTER_AUDIO", op_id=op_id)
            case OpTypes.FILTER_TEXT:
                for op in self.filter_text:
                    if op.op_id == op_id:
                        await op.close()
                        self.filter_text.remove(op)
                        return
                raise OperationUnloaded("FILTER_TEXT", op_id=op_id)
            case _:
                # Should never get here if op_type is indeed OpTypes
                raise UnknownOpType(op_type)
            
    async def close_operation_all(self):
        if self.stt:
            await self.stt.close()
            self.stt = None
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
        
        for loose_key in self.loose_loaded_ops:
            await self.loose_loaded_ops[loose_key].close()
        self.loose_loaded_ops = dict()
        
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
        op_type: OpTypes,
        chunk_in: Dict[str, Any],
        op_id: str = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        '''Use an operation that has already been loaded prior'''
        match op_type:
            case OpTypes.STT:
                if not self.stt:
                    raise OperationUnloaded("STT")
                elif op_id and self.stt and self.stt.op_id != op_id:
                    raise OperationUnloaded("STT", op_id=op_id)
                
                return self.stt(chunk_in)
            case OpTypes.T2T:
                if not self.t2t:
                    raise OperationUnloaded("T2T")
                elif op_id and self.t2t and self.t2t.op_id != op_id:
                    raise OperationUnloaded("T2T", op_id=op_id)
                
                return self.t2t(chunk_in)
            case OpTypes.TTS:
                if not self.tts:
                    raise OperationUnloaded("TTS")
                elif op_id and self.tts and self.tts.op_id != op_id:
                    raise OperationUnloaded("TTS", op_id=op_id)
                
                return self.tts(chunk_in)
            case OpTypes.FILTER_AUDIO:
                if op_id:
                    for op in self.filter_audio:
                        if op.op_id == op_id:
                            return op(chunk_in)
                    raise OperationUnloaded("FILTER_AUDIO", op_id=op_id)
                else:
                    return self._use_filter(self.filter_audio, 0, chunk_in)
            case OpTypes.FILTER_TEXT:
                if op_id:
                    for op in self.filter_text:
                        if op.op_id == op_id:
                            return op(chunk_in)
                    raise OperationUnloaded("FILTER_TEXT", op_id=op_id)
                else:
                    return self._use_filter(self.filter_text, 0, chunk_in)
            case _:
                # Should never get here if op_type is indeed OpTypes
                raise UnknownOpType(op_type)

    def use_loose_operation(self, loose_key, payload):
        op = self.loose_loaded_ops.get(loose_key, None)
        if op:
            return op(payload)
        else :
            raise OperationUnloaded("LOOSE", op_id=loose_key)