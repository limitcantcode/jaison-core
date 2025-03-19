import logging
import asyncio
import uuid
import base64
from typing import Dict, Coroutine, Set, List, Any, AsyncGenerator, Tuple
from enum import StrEnum
from utils.helpers.singleton import Singleton
from utils.helpers.iterable import list_to_agen
from utils.config import Config

from utils.helpers.observer import ObserverServer
from utils.helpers.multiplexor import multiplexor
from utils.prompter import Prompter, UnknownContext

from utils.processes import ProcessManager
from utils.operations import OperationManager
from utils.operations import (
    STT_TYPE, T2T_TYPE, TTSG_TYPE, TTSC_TYPE, 
    CHUNKER_TYPE, FILTER_TYPE, EMOTION_TYPE
)
from utils.operations.error import (
    InvalidOperationID,
    InvalidOperationType,
    UnloadedOperationError,
    CompatibilityModeEnabled
)

class NonexistantJobException(Exception):
    pass

class UnknownJobType(Exception):
    pass

class JobType(StrEnum):
    RESPONSE = 'response'
    CONTEXT_REQUEST_ADD = 'context_request_add'
    CONTEXT_REQUEST_CLEAR = 'context_request_clear'
    CONTEXT_CONVERSATION_ADD_TEXT = 'context_conversation_add_text'
    CONTEXT_CONVERSATION_ADD_AUDIO = 'context_conversation_add_audio'
    CONTEXT_CONVERSATION_CLEAR = 'context_conversation_clear'
    CONTEXT_CUSTOM_ADD = 'context_custom_add'
    CONTEXT_CUSTOM_REMOVE = 'context_custom_remove'
    CONTEXT_CUSTOM_UPDATE = 'context_custom_update'
    OPERATION_START = 'operation_start'
    OPERATION_RELOAD = 'operation_reload'
    OPERATION_UNLOAD = 'operation_unload'
    OPERATION_USE = 'operation_use'
    CONFIG_LOAD = 'config_load'
    CONFIG_SAVE = 'config_save'
    
class JAIson(metaclass=Singleton):
    def __init__(self): # attribute stubs
        self.job_loop: asyncio.Task = None
        self.job_queue: asyncio.Queue = None
        self.job_map: Dict[str, Tuple[JobType, Coroutine]] = None
        self.job_current_id: str = None
        self.job_current: asyncio.Task = None
        self.job_skips: Set = None
        
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
        await self.start_operations('start',JobType.OPERATION_START,ops=Config().default_operations)
        
    async def stop(self):
        logging.info("Shutting down JAIson application layer")
        await self.op_manager.unload_all()
        await self.process_manager.unload()
        logging.info("JAIson application layer has been shut down")
        
    
    async def reload(self):
        logging.info("Reloading JAIson application layer")
        await self.op_manager.reload_all()
        await self.process_manager.reload()
        logging.info("JAIson application layer has been reloaded")
    
    ## Job Queueing #########################
    
    # Add async task to Queue to be ran in the order it was requested
    async def create_job(self, job_type: StrEnum, **kwargs):
        new_job_id = str(uuid.uuid4())
        
        job_type_enum = JobType(job_type)
        
        coro = None
        if job_type_enum == JobType.RESPONSE: coro = self.response_pipeline(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_REQUEST_ADD: coro = self.append_request_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_REQUEST_CLEAR: coro = self.clear_request_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CONVERSATION_ADD_TEXT: coro = self.append_conversation_context_text(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CONVERSATION_ADD_AUDIO: coro = self.append_conversation_context_text(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CONVERSATION_CLEAR: coro = self.clear_conversation_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CUSTOM_ADD: coro = self.add_custom_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CUSTOM_REMOVE: coro = self.remove_custom_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CUSTOM_UPDATE: coro = self.update_custom_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.OPERATION_START: coro = self.start_operations(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.OPERATION_RELOAD: coro = self.reload_operations(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.OPERATION_UNLOAD: coro = self.unload_operations(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.OPERATION_USE: coro = self.use_operation(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONFIG_LOAD: coro = self.load_config(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONFIG_SAVE: coro = self.save_config(new_job_id, job_type_enum, **kwargs)
        self.job_map[new_job_id] = (job_type_enum, coro)
        
        await self.job_queue.put(new_job_id)
        
        logging.debug(f"Queued new job {new_job_id}")
        return new_job_id
    
    async def cancel_job(self, job_id: str, reason: str = None):
        if job_id not in self.job_map: raise NonexistantJobException(f"Job {job_id} does not exist or already finished")
        
        cancel_message = f"Setting job {job_id} to cancel"
        if reason: cancel_message += f" because {reason}"
        logging.debug(cancel_message)

        if job_id == self.job_current_id:
            # If job is already running
            self._clear_current_job(reason=cancel_message)
        else: 
            # If job is still in Queue
            # Simply flag to skip. Unzipping queue can potentially process a job out of order 
            self.job_skips[job_id](cancel_message)
            
    def _clear_current_job(self, reason: str = None):
        self.job_map.pop(self.job_current_id, None)
        self.job_skips.discard(self.job_current_id)
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
                self.job_current_id = await self.job_queue.get()
                job_type, coro = self.job_map[self.job_current_id]
                
                if self.job_current_id in self.job_skips:
                    # Skip cancelled jobs
                    reason = self.job_skips[self.job_current_id]
                    self._handle_broadcast_error(self.job_current_id, job_type, asyncio.CancelledError(reason))
                    self._clear_current_job(reason=reason)
                    del coro
                else:
                    # Run and wait for completion
                    self.job_current = asyncio.create_task(coro)
                    await asyncio.wait([self.job_current])
                    
                    # Handle finishing with error
                    err = self.job_current.exception()
                    if err is not None:
                        self._handle_broadcast_error(self.job_current_id, job_type, err)
                    
                    # Cleanup
                    self._clear_current_job()
            except Exception as err:
                logging.error("Encountered error in main job processing loop", exc_info=True)
                asyncio.sleep(1)
                
    ## Regular Request Handlers ###################
    
    def get_loaded_operations(self):
        return self.op_manager.get_loaded_operations()

    def get_current_config(self):
        return Config().get_config_dict()    
            
    ## Async Job Handlers #########################
    
    # Universal response pipeline
    # TODO: consider the following
    # Is it a good idea to omit input text/audio for this?
    # Might include for simple overrides
    # API options can be expanded to have those later, for now omit until decided to be a good decision
    # Multi prompting? Have different prompting profiles and select which one? Idk, not for now.
    # TODO: error handling, look into making a skip operation or no-op operation
    '''
    Generate responses from the current contexts.
    This does not take an input. Context for what to repond to must be added prior to running this.
    '''
    async def response_pipeline(
        self,
        job_id: str,
        job_type: JobType,
        skip_ttsc: bool = None,
        output_audio: bool = None
    ):
        config = Config()
        if output_audio is None: output_audio = config.default_skip_ttsc
        if output_audio and self.op_manager.ttsg is None: raise UnloadedOperationError(TTSG_TYPE)
        if skip_ttsc is None: skip_ttsc = config.default_skip_ttsc
        
        # Prompting
        system_prompt, user_prompt = self.prompter.get_sys_prompt(), self.prompter.get_user_prompt()
        
        # T2T Generation
        next_stream = list_to_agen([{"system_prompt":system_prompt,"user_prompt":user_prompt}])
        t2t_stream_d, t2t_stream_task = multiplexor({
            'broadcast': (lambda stream: self._handle_broadcast_stream(job_id, job_type, stream, base_payload={"output_type": "prompt"})),
            T2T_TYPE: (lambda stream: self.op_manager.use(T2T_TYPE,in_stream=stream))
        }, next_stream)
        self.tasks_to_clean += [t2t_stream_task, asyncio.create_task(t2t_stream_d['broadcast'])]
        next_stream = t2t_stream_d[T2T_TYPE]
        
        # Enforce sentence chunking
        next_stream = self.op_manager.use(CHUNKER_TYPE, in_stream=next_stream)
        
        # Filters and emotions
        t2t_consumers = {
            'broadcast': (lambda stream: self._handle_broadcast_stream(job_id, job_type, stream, base_payload={"output_type": 'text_raw'})),
            FILTER_TYPE: (lambda stream: self.op_manager.use(FILTER_TYPE,in_stream=stream))
        }
        if not config.default_skip_emotions: t2t_consumers | {EMOTION_TYPE: (lambda stream: self.op_manager.use(EMOTION_TYPE,in_stream=next_stream))}
        t2t_post_stream_d, t2t_post_stream_task = multiplexor(t2t_consumers, next_stream)
        self.tasks_to_clean += [t2t_post_stream_task, asyncio.create_task(t2t_post_stream_d['broadcast'])]
        if not config.default_skip_emotions: await self._handle_broadcast_stream(job_id, job_type, t2t_post_stream_d[EMOTION_TYPE], base_payload={"output_type": 'emotion'})
        
        if not output_audio:
            # Omit audio generation steps and just broadcast final text
            await self._handle_broadcast_stream(job_id, job_type, t2t_post_stream_d[FILTER_TYPE], base_payload={"output_type": 'text_final'})
        else:
            # TTSG
            next_stream = t2t_post_stream_d[FILTER_TYPE]
            t2t_post_consumers = {
                'broadcast': (lambda stream: self._handle_broadcast_stream(job_id, job_type, stream, base_payload={"output_type": 'text_final'})),
                TTSG_TYPE: (lambda stream: self.op_manager.use(TTSG_TYPE,in_stream=stream))
            }
            ttsg_stream_d, ttsg_stream_task = multiplexor(t2t_post_consumers, next_stream)
            self.tasks_to_clean += [ttsg_stream_task, asyncio.create_task(ttsg_stream_d['broadcast'])]
            next_stream = ttsg_stream_d[TTSG_TYPE]
            
            if not skip_ttsc:
                # TTSC
                ttsg_consumers = {
                    'broadcast': (lambda stream: self._handle_broadcast_stream(job_id, job_type, stream, base_payload={"output_type": 'tts_raw'})),
                    TTSC_TYPE: (lambda stream: self.op_manager.use(TTSC_TYPE,in_stream=stream))
                }
                ttsc_stream_d, ttsc_stream_task = multiplexor(t2t_post_consumers, next_stream)
                self.tasks_to_clean += [ttsc_stream_task, asyncio.create_task(ttsc_stream_d['broadcast'])]
                next_stream = ttsc_stream_d[TTSC_TYPE]
            
            # Signal finish
            await self._handle_broadcast_stream(job_id, job_type, next_stream, base_payload={"output_type": 'tts_final'})
            await asyncio.wait(self.tasks_to_clean)
        
    # Base context modification
    async def append_request_context(
        self, 
        job_id: str, 
        job_type: JobType, 
        content: str = None
    ):
        self.prompter.add_request(content)
        await self._handle_broadcast_event(job_id, job_type, {"content": content})
        
    async def append_conversation_context_text(
        self, 
        job_id: str, 
        job_type: JobType, 
        user: str = None, 
        timestamp: int = None, 
        content: str = None
    ):
        self.prompter.add_history(timestamp, user, content)
        await self._handle_broadcast_event(job_id, job_type, {
            "user": user,
            "timestamp": timestamp,
            "content": content,
            "line": self.prompter.msg_o_to_line(self.prompter.convo_history[-1])
        })
        
    async def append_conversation_context_audio(
        self,
        job_id: str,
        job_type: JobType,
        user: str = None,
        timestamp: int = None,
        audio_bytes: bytes = None,
        sr: int = None,
        sw: int = None,
        ch: int = None
    ):
        content = ""
        next_stream = list_to_agen([{"audio_bytes": audio_bytes, "sr": sr, "sw": sw, "ch": ch}])
        async for out_d in self.op_manager.use(STT_TYPE, in_stream=next_stream):
            content += out_d['transcription']
      
        self.prompter.add_history(timestamp, user, content)
        await self._handle_broadcast_event(job_id, job_type, {
            "user": user,
            "timestamp": timestamp,
            "content": content,
            "line": self.prompter.msg_o_to_line(self.prompter.convo_history[-1])
        })

    async def clear_request_context(
        self,
        job_id: str,
        job_type: JobType
    ):
        self.prompter.clear_request()
        await self._handle_broadcast_event(job_id, job_type, {})
        
    async def clear_conversation_context(
        self,
        job_id: str,
        job_type: JobType
    ):
        self.prompter.clear()
        await self._handle_broadcast_event(job_id, job_type, {})
        
    # Custom context management
    async def add_custom_context(
        self,
        job_id: str,
        job_type: JobType,
        context_id: str = None,
        context_name: str = None,
        context_description: str = None,
        initial_contents: str=None
    ):
        self.prompter.add_custom_context(context_id, context_name, context_description=context_description, initial_contents=initial_contents)
        await self._handle_broadcast_event(job_id, job_type, {"id": context_id, "name": context_name, "description": context_description, "content":initial_contents})
    
    async def remove_custom_context(self,
        job_id: str,
        job_type: JobType,
        context_id: str = None
    ):
        self.prompter.remove_custom_context(context_id)
        await self._handle_broadcast_event(job_id, job_type, {"id": context_id})
    
    async def update_custom_context(
        self,
        job_id: str,
        job_type: JobType,
        context_id: str = None,
        context_contents: str = None
    ):
        self.prompter.update_custom_context(context_id, context_contents)
        await self._handle_broadcast_event(job_id, job_type, {"id":context_id})
            
    # Operation management
    async def start_operations(
        self,
        job_id: str,
        job_type: JobType,
        ops: List[Dict[str, str]] = []
    ):
        for op_d in ops:
            await self._handle_op_manager(job_id, job_type, op_d['type'], op_d['id'])
        await self.process_manager.reload()
        
    async def reload_operations(
        self,
        job_id: str,
        job_type: JobType,
        ops: List[Dict[str, str]] = []
    ):
        for op_d in ops:
            await self._handle_op_manager(job_id, job_type, op_d['type'], op_d['id'])
        await self.process_manager.reload()
        
    async def unload_operations(
        self,
        job_id: str,
        job_type: JobType,
        ops: List[Dict[str, str]] = []
    ):
        for op_d in ops:
            await self._handle_op_manager(job_id, job_type, op_d['type'], op_d['id'])
        await self.process_manager.unload()
    
    async def _handle_op_manager(self, job_id: str, job_type: JobType, op_type: str, op_id: str):
        if job_type == JobType.OPERATION_START: await self.op_manager.start_operation(op_type,op_id)
        elif job_type == JobType.OPERATION_RELOAD: await self.op_manager.reload_operation(op_type,op_id)
        elif job_type == JobType.OPERATION_UNLOAD: await self.op_manager.unload_operation(op_type,op_id)
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
        payload: Dict[str, Any] = None
    ):
        if op_type not in self.op_manager.op_collection:
            raise InvalidOperationType(op_type)
        
        if 'audio_bytes' in payload:
            payload['audio_bytes'] = base64.b64decode(payload['audio_bytes'])
            
        out_stream = self.op_manager.use(op_type, in_stream=list_to_agen([payload]))
        await self._handle_broadcast_stream(job_id, job_type, out_stream, base_payload={"type": op_type})
        self._handle_broadcast_event(job_id, job_type, base_payload={"finish": True})
            
    
    # Configuration
    async def load_config(self, job_id: str, job_type: JobType, config_name: str): # TODO: handle non-existant configs
        Config().load_from_name(config_name)
        await self._handle_broadcast_event(job_id, job_type, {})
    
    async def save_config(self, job_id: str, job_type: JobType, config_name: str, config_d: Dict[str, Any]): # TODO: handle non-existant configs
        Config().load_from_dict(config_d)
        Config().save(config_name)
        await self._handle_broadcast_event(job_id, job_type, {})
    
    ## General helpers ###############################
    async def _handle_broadcast_event(self, job_id: str, job_type: JobType, base_payload: dict):
        payload = base_payload | {"job_id": job_id, "success": True}
        await self.event_server.broadcast_event(job_type.value, payload)
    
    async def _handle_broadcast_stream(self, job_id: str, job_type: JobType, base_payload_stream: AsyncGenerator, base_payload: dict = {}):
        async for out_d in base_payload_stream:
            payload = out_d | {"job_id": job_id, "success": True}
            self.event_server.broadcast_event(job_type.value, payload)
    
    async def _handle_broadcast_error(self, job_id: str, job_type: JobType, err: Exception):
        error_type = "unknown"
        # TODO: extend with all errors
        if isinstance(err, InvalidOperationType): error_type = "type_error"
        elif isinstance(err, InvalidOperationID): error_type = "type_error"
        elif isinstance(err, CompatibilityModeEnabled): error_type = "compatibility"
        elif isinstance(err, UnloadedOperationError): error_type = "unloaded"
        elif isinstance(err, UnknownJobType): error_type = "job_error"
        elif isinstance(err, UnknownContext): error_type = "context_missing"
        
        payload = {
            "job_id": job_id,
            "success": False, 
            "error": error_type, 
            "reason": str(err)
        }
        await self.event_server.broadcast_event(job_type.value, payload)