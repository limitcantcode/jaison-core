import logging
import asyncio
import uuid
import base64
import datetime
from typing import Dict, Coroutine, List, Any, AsyncGenerator, Tuple
from enum import StrEnum

from utils.helpers.singleton import Singleton
from utils.helpers.iterable import list_to_agen
from utils.helpers.observer import ObserverServer
from utils.helpers.multiplexor import multiplexor

from utils.config import Config
from utils.prompter import Prompter
from utils.processes import ProcessManager
from utils.operations import (
    OperationManager,
    OpTypes,
    Operation,
    UnknownOpType,
    UnknownOpID,
    DuplicateFilter,
    OperationUnloaded
)

class NonexistantJobException(Exception):
    pass

class UnknownJobType(Exception):
    pass

class JobType(StrEnum):
    RESPONSE = 'response'
    CONTEXT_CLEAR = 'context_clear'
    CONTEXT_REQUEST_ADD = 'context_request_add'
    CONTEXT_CONVERSATION_ADD_TEXT = 'context_conversation_add_text'
    CONTEXT_CONVERSATION_ADD_AUDIO = 'context_conversation_add_audio'
    CONTEXT_CUSTOM_REGISTER = 'context_custom_register'
    CONTEXT_CUSTOM_REMOVE = 'context_custom_remove'
    CONTEXT_CUSTOM_ADD = 'context_custom_add'
    OPERATION_LOAD = 'operation_load'
    OPERATION_CONFIG_RELOAD = "operation_reload_from_config"
    OPERATION_UNLOAD = 'operation_unload'
    OPERATION_USE = 'operation_use'
    CONFIG_LOAD = 'config_load'
    CONFIG_UPDATE = 'config_update'
    CONFIG_SAVE = 'config_save'
    
class JAIson(metaclass=Singleton):
    def __init__(self): # attribute stubs
        self.job_loop: asyncio.Task = None
        self.job_queue: asyncio.Queue = None
        self.job_map: Dict[str, Tuple[JobType, Coroutine]] = None
        self.job_current_id: str = None
        self.job_current: asyncio.Task = None
        self.job_skips: dict = None
        
        # Any asyncio.Tasks in this list will be cancelled before the next job runs
        self.tasks_to_clean: List = list()
        
        self.event_server: ObserverServer = None
        
        self.prompter: Prompter = None
        self.process_manager: ProcessManager = None
        self.op_manager: OperationManager = None
    
    async def start(self):
        self.job_queue = asyncio.Queue()
        self.job_map = dict()
        self.job_skips = dict()
        self.job_loop = asyncio.create_task(self._process_job_loop())
        
        self.event_server = ObserverServer()
        
        self.prompter = Prompter()
        
        self.process_manager = ProcessManager()
        self.op_manager = OperationManager()
        await self.start_operations('start',JobType.OPERATION_LOAD,ops=Config().default_operations)
        await self.process_manager.reload()
        
    async def stop(self):
        logging.info("Shutting down JAIson application layer")
        await self.op_manager.close_operation_all()
        await self.process_manager.unload()
        logging.info("JAIson application layer has been shut down")
    
    ## Job Queueing #########################
    
    # Add async task to Queue to be ran in the order it was requested
    async def create_job(self, job_type: StrEnum, **kwargs):
        new_job_id = str(uuid.uuid4())
        
        job_type_enum = JobType(job_type)
        
        coro = None
        if job_type_enum == JobType.RESPONSE: coro = self.response_pipeline(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_REQUEST_ADD: coro = self.append_request_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CONVERSATION_ADD_TEXT: coro = self.append_conversation_context_text(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CONVERSATION_ADD_AUDIO: coro = self.append_conversation_context_audio(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CLEAR: coro = self.clear_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CUSTOM_REGISTER: coro = self.register_custom_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CUSTOM_REMOVE: coro = self.remove_custom_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CUSTOM_ADD: coro = self.add_custom_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.OPERATION_LOAD: coro = self.load_operations(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.OPERATION_CONFIG_RELOAD: coro = self.load_operations_from_config(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.OPERATION_UNLOAD: coro = self.unload_operations(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.OPERATION_USE: coro = self.use_operation(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONFIG_LOAD: coro = self.load_config(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONFIG_UPDATE: coro = self.update_config(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONFIG_SAVE: coro = self.save_config(new_job_id, job_type_enum, **kwargs)
        self.job_map[new_job_id] = (job_type_enum, coro)
        
        await self.job_queue.put(new_job_id)
        
        logging.info(f"Queued new job {new_job_id}")
        return new_job_id
    
    async def cancel_job(self, job_id: str, reason: str = None):
        if job_id not in self.job_map: raise NonexistantJobException(f"Job {job_id} does not exist or already finished")
        
        cancel_message = f"Setting job {job_id} to cancel"
        if reason: cancel_message += f" because {reason}"
        logging.info(cancel_message)

        if job_id == self.job_current_id:
            # If job is already running
            self._clear_current_job(reason=cancel_message)
        else: 
            # If job is still in Queue
            # Simply flag to skip. Unzipping queue can potentially process a job out of order 
            self.job_skips[job_id](cancel_message)
            
    def _clear_current_job(self, reason: str = None):
        self.job_map.pop(self.job_current_id, None)
        self.job_skips.pop(self.job_current_id, None)
        self.job_current_id = None
        
        for task in self.tasks_to_clean:
            task.cancel(reason)
        self.tasks_to_clean.clear()
        
        if self.job_current is not None:
            self.job_current.cancel(reason)
            self.job_current = None
        
    # Side loop responsible for processing the next job in the Queue
    async def _process_job_loop(self):
        while True:
            try:
                await self.process_manager.reload()
                await self.process_manager.unload()
                
                self.job_current_id = await self.job_queue.get()
                job_type, coro = self.job_map[self.job_current_id]
                
                if self.job_current_id in self.job_skips:
                    # Skip cancelled jobs
                    reason = self.job_skips[self.job_current_id]
                    await self._handle_broadcast_error(self.job_current_id, job_type, asyncio.CancelledError(reason))
                    self._clear_current_job(reason=reason)
                    del coro
                else:
                    # Run and wait for completion
                    self.job_current = asyncio.create_task(coro)
                    await asyncio.wait([self.job_current])
                    
                    # Handle finishing with error
                    err = self.job_current.exception() if self.job_current else None
                    if err is not None:
                        logging.warning(f"Job was cancelled due to an error: {err}", exc_info=err)
                        await self._handle_broadcast_error(self.job_current_id, job_type, err)
                    
                    # Cleanup
                    self._clear_current_job()
            except Exception as err:
                logging.error("Encountered error in main job processing loop", exc_info=True)
                await asyncio.sleep(1)
                
    ## Regular Request Handlers ###################
    
    def get_loaded_operations(self):
        op_d = self.op_manager.get_operations_all()
        for key in op_d:
            if isinstance(op_d[key], Operation):
                op_d[key] = op_d[key].id
            elif isinstance(op_d[key], list):
                op_d[key] = list(map(lambda x: x.id, op_d[key]))
            else:
                op_d[key] = "unknown"
                
        return op_d
                

    def get_current_config(self):
        return Config().get_config_dict()
            
    ## Async Job Handlers #########################
    
    '''
    Generate responses from the current contexts.
    This does not take an input. Context for what to repond to must be added prior to running this.
    '''
    async def response_pipeline(
        self,
        job_id: str,
        job_type: JobType,
        include_audio: bool = True
    ):
        
        # Adjust flags based on loaded ops
        if not self.op_manager.get_operation(OpTypes.STT): include_audio = False
        
        # Broadcast start conditions
        await self._handle_broadcast_start(job_id, job_type, {"include_audio": include_audio})
        
        # Get prompts
        system_prompt, user_prompt = self.prompter.get_sys_prompt(), self.prompter.get_user_prompt()
        text_chunk = {"system_prompt": system_prompt, "user_prompt": user_prompt}
        
        # Appy t2t
        t2t_result = ""
        async for chunk_out in self.op_manager.use(OpTypes.T2T, {"system_prompt": system_prompt, "user_prompt": user_prompt}):
            t2t_result += chunk_out["content"]
        
        # Broadcast raw result
        await self._handle_broadcast_event(job_id, job_type, text_chunk | {"raw_content": t2t_result})
        
        text_chunk = text_chunk | {"content": t2t_result} # Get full result
        
        # Apply text filters
        async for text_chunk_out in self.op_manager.use(OpTypes.FILTER_TEXT, text_chunk):
            if include_audio:
                # Apply tts
                async for audio_chunk_out in self.op_manager.use(OpTypes.TTS, text_chunk_out):
                    # Apply tts filters
                    async for final_audio_chunk_out in self.op_manager.use(OpTypes.FILTER_AUDIO, audio_chunk_out):
                        # boardcast results
                        await self._handle_broadcast_event(job_id, job_type, final_audio_chunk_out)
            else:
                await self._handle_broadcast_event(job_id, job_type, text_chunk_out)
                        
        # Broadcast completion
        await self._handle_broadcast_success(job_id, job_type)


    # Context modification
    async def clear_context(
        self,
        job_id: str,
        job_type: JobType
    ):
        await self._handle_broadcast_start(job_id, job_type, {})
        self.prompter.clear_history()
        await self._handle_broadcast_success(job_id, job_type)
        
    async def append_request_context(
        self, 
        job_id: str, 
        job_type: JobType, 
        content: str = None
    ):
        await self._handle_broadcast_start(job_id, job_type, {"content": content})
        self.prompter.add_request(content)
        last_line_o = self.prompter.history[-1]
        await self._handle_broadcast_event(job_id, job_type, {
            "timestamp": last_line_o.time.timestamp(),
            "content": last_line_o.message,
            "line": last_line_o.to_line()
        })
        await self._handle_broadcast_success(job_id, job_type)
        
    async def append_conversation_context_text(
        self, 
        job_id: str, 
        job_type: JobType, 
        user: str = None, 
        timestamp: int = None, 
        content: str = None
    ):
        await self._handle_broadcast_start(job_id, job_type, {"user": user, "timestamp": timestamp, "content": content})
        self.prompter.add_chat(
            user,
            content,
            time=(
                datetime.datetime.fromtimestamp(timestamp) \
                if not isinstance(timestamp, datetime.datetime) else timestamp
            )
        )
        last_line_o = self.prompter.history[-1]
        await self._handle_broadcast_event(job_id, job_type, {
            "user": last_line_o.user,
            "timestamp": last_line_o.time.timestamp(),
            "content": last_line_o.message,
            "line": last_line_o.to_line()
        })
        await self._handle_broadcast_success(job_id, job_type)
        
    async def append_conversation_context_audio(
        self,
        job_id: str,
        job_type: JobType,
        user: str = None,
        timestamp: int = None,
        audio_bytes: str = None,
        sr: int = None,
        sw: int = None,
        ch: int = None
    ):
        await self._handle_broadcast_start(job_id, job_type, {"user": user, "timestamp": timestamp, "sr": sr, "sw": sw, "ch": ch, "audio_bytes": (audio_bytes is not None)}) # Don't send full audio bytes over websocket, just flag as gotten
        audio_bytes: bytes = base64.b64decode(audio_bytes)
        content = ""
        async for out_d in self.op_manager.use_operation(OpTypes.STT, {"audio_bytes": audio_bytes, "sr": sr, "sw": sw, "ch": ch}):
            content += out_d['transcription']
      
        self.prompter.add_chat(
            user,
            content,
            time=(
                datetime.datetime.fromtimestamp(timestamp) \
                if isinstance(timestamp, int) else timestamp
            )
        )
        last_line_o = self.prompter.history[-1]
        await self._handle_broadcast_event(job_id, job_type, {
            "user": last_line_o.user,
            "timestamp": last_line_o.time.timestamp(),
            "content": last_line_o.message,
            "line": last_line_o.to_line()
        })
        await self._handle_broadcast_success(job_id, job_type)
        
    async def register_custom_context(
        self,
        job_id: str,
        job_type: JobType,
        context_id: str = None,
        context_name: str = None,
        context_description: str = None
    ):
        await self._handle_broadcast_start(job_id, job_type, {"context_id": context_id, "context_name": context_name, "context_description": context_description})
        self.prompter.register_custom_context(context_id, context_name, context_description=context_description)
        await self._handle_broadcast_success(job_id, job_type)
    
    async def remove_custom_context(self,
        job_id: str,
        job_type: JobType,
        context_id: str = None
    ):
        await self._handle_broadcast_start(job_id, job_type, {"context_id": context_id})
        self.prompter.remove_custom_context(context_id)
        await self._handle_broadcast_success(job_id, job_type)
    
    async def add_custom_context(
        self,
        job_id: str,
        job_type: JobType,
        context_id: str = None,
        context_contents: str = None,
        timestamp: int = None
    ):
        await self._handle_broadcast_start(job_id, job_type, {"context_id": context_id, "context_contents": context_contents, "timestamp": timestamp})
        if timestamp is not None: timestamp = datetime.datetime.fromtimestamp(timestamp)
        self.prompter.add_custom_context(context_id, context_contents)
        await self._handle_broadcast_success(job_id, job_type)
            
    # Operation management    
    async def load_operations(
        self,
        job_id: str,
        job_type: JobType,
        ops: List[Dict[str, str]] = []
    ):
        await self._handle_broadcast_start(job_id, job_type, {"ops": ops})
        for op_d in ops:
            await self._handle_op_manager(job_id, job_type, op_d['type'], op_d['id'])
        await self._handle_broadcast_success(job_id, job_type)
        
    async def load_operations_from_config(
        self,
        job_id: str,
        job_type: JobType,
    ):
        await self._handle_broadcast_start(job_id, job_type, {})
        await self.op_manager.load_operations_from_config()
        await self._handle_broadcast_success(job_id, job_type)
        
    async def unload_operations(
        self,
        job_id: str,
        job_type: JobType,
        ops: List[Dict[str, str]] = []
    ):
        await self._handle_broadcast_start(job_id, job_type, {"ops": ops})
        for op_d in ops:
            await self._handle_op_manager(job_id, job_type, op_d['type'], op_d['id'])
        await self._handle_broadcast_success(job_id, job_type)
    
    async def _handle_op_manager(self, job_id: str, job_type: JobType, op_type: str, op_id: str):
        op_enum = OpTypes(op_type)
        if job_type == JobType.OPERATION_LOAD: await self.op_manager.load_operation(op_enum,op_id)
        elif job_type == JobType.OPERATION_UNLOAD: await self.op_manager.close_operation(op_enum,op_id)
        else: raise UnknownJobType(f"No known operation management job called {job_type}")
            
        await self._handle_broadcast_event(job_id, job_type, {
            "type": op_type, 
            "id": op_id, 
        })
        
    async def use_operation(
        self,
        job_id: str,
        job_type: JobType,
        op_type: str = None,
        op_id: str = None,
        payload: Dict[str, Any] = None
    ):
        await self._handle_broadcast_start(job_id, job_type, {"op_type": op_type, "op_id": op_id})
        
        if 'audio_bytes' in payload:
            payload['audio_bytes'] = base64.b64decode(payload['audio_bytes'])
            
        try:
            async for chunk_out in self.op_manager.use_operation(OpTypes(op_type), payload, op_id=op_id):
                self._handle_broadcast_event(job_type, job_id, chunk_out)
        except OperationUnloaded:
            op = self.op_manager.loose_load_operation(OpTypes(op_type), op_id)
            await op.start()
            async for chunk_out in op(payload):
                self._handle_broadcast_event(job_type, job_id, chunk_out)
            await op.close()
            
        await self._handle_broadcast_success(job_id, job_type)
    
    # Configuration
    async def load_config(self, job_id: str, job_type: JobType, config_name: str):
        await self._handle_broadcast_start(job_id, job_type, {"config_name": config_name})
        Config().load_from_name(config_name)
        await self._handle_broadcast_success(job_id, job_type)
        
    async def update_config(self, job_id: str, job_type: JobType, config_d: str):
        await self._handle_broadcast_start(job_id, job_type, {"config_d": config_d})
        Config().load_from_dict(config_d)
        await self._handle_broadcast_success(job_id, job_type)
    
    async def save_config(self, job_id: str, job_type: JobType, config_name: str):
        await self._handle_broadcast_start(job_id, job_type, {"config_name": config_name})
        Config().save(config_name)
        await self._handle_broadcast_success(job_id, job_type)
    
    ## General helpers ###############################
    async def _handle_broadcast_start(self, job_id: str, job_type: JobType, payload: dict):
        await self.event_server.broadcast_event(job_type.value, {
            "job_id": job_id,
            "start": payload
        })
    
    async def _handle_broadcast_event(self, job_id: str, job_type: JobType, payload: dict):
        await self.event_server.broadcast_event(job_type.value, {
            "job_id": job_id,
            "finished": False,
            "result": payload
        })
    
    async def _handle_broadcast_success(self, job_id: str, job_type: JobType):
        await self.event_server.broadcast_event(job_type.value, {
            "job_id": job_id,
            "finished": True,
            "success": True
        })
        
    async def _handle_broadcast_cancelled(self, job_id: str, job_type: JobType, err: Exception):
        # TODO: extend with all errors
        error_type = "unknown"
        if isinstance(err, UnknownOpType): error_type = "operation_unknown_type"
        elif isinstance(err, UnknownOpID): error_type = "operation_unknown_id"
        elif isinstance(err, DuplicateFilter): error_type = "operation_duplicate"
        elif isinstance(err, OperationUnloaded): error_type = "operation_unloaded"
        elif isinstance(err, UnknownJobType): error_type = "job_unknown"
        elif isinstance(err, asyncio.CancelledError): error_type = "job_cancelled"
        
        await self.event_server.broadcast_event(job_type.value, {
            "job_id": job_id,
            "finished": True,
            "success": False,
            "result": {
                "type": error_type,
                "reason": str(err)
            }
        })