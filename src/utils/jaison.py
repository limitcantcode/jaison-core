import logging
import asyncio
import uuid
import base64
import datetime
from typing import Dict, Coroutine, List, Any, Tuple
from enum import Enum

from utils.helpers.singleton import Singleton
from utils.helpers.iterable import chunk_buffer
from utils.helpers.observer import ObserverServer

from utils.config import Config, UnknownField, UnknownFile
from utils.prompter import Prompter
from utils.prompter.message import (
    RawMessage,
    RequestMessage,
    ChatMessage,
    MCPMessage,
    CustomMessage
)
from utils.processes import ProcessManager
from utils.operations import (
    OperationManager,
    OpRoles,
    Operation,
    UnknownOpType,
    UnknownOpRole,
    UnknownOpID,
    DuplicateFilter,
    OperationUnloaded,
    StartActiveError,
    CloseInactiveError,
    UsedInactiveError
)
from utils.mcp import MCPManager

class NonexistantJobException(Exception):
    pass

class UnknownJobType(Exception):
    pass

class JobType(Enum):
    RESPONSE = 'response'
    CONTEXT_CLEAR = 'context_clear'
    CONTEXT_CONFIGURE = "context_configure"
    CONTEXT_REQUEST_ADD = 'context_request_add'
    CONTEXT_CONVERSATION_ADD_TEXT = 'context_conversation_add_text'
    CONTEXT_CONVERSATION_ADD_AUDIO = 'context_conversation_add_audio'
    CONTEXT_CUSTOM_REGISTER = 'context_custom_register'
    CONTEXT_CUSTOM_REMOVE = 'context_custom_remove'
    CONTEXT_CUSTOM_ADD = 'context_custom_add'
    OPERATION_LOAD = 'operation_load'
    OPERATION_CONFIG_RELOAD = "operation_reload_from_config"
    OPERATION_UNLOAD = 'operation_unload'
    OPERATION_CONFIGURE = 'operation_configure'
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
        self.mcp_manager: MCPManager = None
    
    async def start(self):
        logging.info("Starting JAIson application layer.")
        self.job_queue = asyncio.Queue()
        self.job_map = dict()
        self.job_skips = dict()
        self.job_loop = asyncio.create_task(self._process_job_loop())
        
        self.event_server = ObserverServer()
        
        self.prompter = Prompter()
        await self.prompter.configure(Config().prompter)
        
        self.process_manager = ProcessManager()
        self.op_manager = OperationManager()
        self.mcp_manager = MCPManager()
        await self.mcp_manager.start()
        self.prompter.add_mcp_usage_prompt(self.mcp_manager.get_tooling_prompt(), self.mcp_manager.get_response_prompt())
        await self.op_manager.load_operations_from_config()
        await self.process_manager.reload()
        logging.info("JAIson application layer has started.")
        
    async def stop(self):
        logging.info("Shutting down JAIson application layer")
        await self.op_manager.close_operation_all()
        await self.mcp_manager.close()
        await self.process_manager.unload()
        logging.info("JAIson application layer has been shut down")
    
    ## Job Queueing #########################
    
    # Add async task to Queue to be ran in the order it was requested
    async def create_job(self, job_type: Enum, **kwargs):
        new_job_id = str(uuid.uuid4())
        
        job_type_enum = JobType(job_type)
        
        coro = None
        if job_type_enum == JobType.RESPONSE: coro = self.response_pipeline(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_REQUEST_ADD: coro = self.append_request_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CONVERSATION_ADD_TEXT: coro = self.append_conversation_context_text(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CONVERSATION_ADD_AUDIO: coro = self.append_conversation_context_audio(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CLEAR: coro = self.clear_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CONFIGURE: coro = self.configure_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CUSTOM_REGISTER: coro = self.register_custom_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CUSTOM_REMOVE: coro = self.remove_custom_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONTEXT_CUSTOM_ADD: coro = self.add_custom_context(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.OPERATION_LOAD: coro = self.load_operations(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.OPERATION_CONFIG_RELOAD: coro = self.load_operations_from_config(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.OPERATION_UNLOAD: coro = self.unload_operations(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.OPERATION_CONFIGURE: coro = self.configure_operations(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.OPERATION_USE: coro = self.use_operation(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONFIG_LOAD: coro = self.load_config(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONFIG_UPDATE: coro = self.update_config(new_job_id, job_type_enum, **kwargs)
        elif job_type_enum == JobType.CONFIG_SAVE: coro = self.save_config(new_job_id, job_type_enum, **kwargs)
        self.job_map[new_job_id] = (job_type_enum, coro)
        
        await self.job_queue.put(new_job_id)
        
        logging.info("Queued new {} job {}".format(job_type_enum.value, new_job_id))
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
        op_d = self.op_manager.get_operation_all()
        for key in op_d:
            if isinstance(op_d[key], Operation):
                op_d[key] = op_d[key].op_id
            elif isinstance(op_d[key], list):
                op_d[key] = list(map(lambda x: x.op_id, op_d[key]))
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
        if not self.op_manager.get_operation(OpRoles.TTS): include_audio = False
        
        # Broadcast start conditions
        await self._handle_broadcast_start(job_id, job_type, {"include_audio": include_audio})
    
        # Handle MCP stuff
        if self.op_manager.get_operation(OpRoles.MCP):
            self.prompter.add_mcp_usage_prompt(self.mcp_manager.get_tooling_prompt(), self.mcp_manager.get_response_prompt())
            mcp_sys_prompt, mcp_user_prompt = self.prompter.generate_mcp_system_context(), self.prompter.generate_mcp_user_context()
            tooling_response = ""
            async for chunk in self.op_manager.use_operation(OpRoles.MCP, {"instruction_prompt": mcp_sys_prompt, "messages": [RawMessage(mcp_user_prompt)]}):
                tooling_response += chunk['content']

            ## Perform MCP tool calls
            tool_call_results = await self.mcp_manager.use(tooling_response)
            
            ## Add results and usage prompt to prompter
            self.prompter.add_mcp_results(tool_call_results)

        # Get prompts
        instruction_prompt, history = self.prompter.get_sys_prompt(), self.prompter.get_history()
        
        # Appy t2t
        t2t_result = ""
        async for chunk_out in self.op_manager.use_operation(OpRoles.T2T, {"instruction_prompt": instruction_prompt, "messages": history}):
            t2t_result += chunk_out["content"]
        
        # Broadcast raw results
        await self._handle_broadcast_event(job_id, job_type, {"instruction_prompt": instruction_prompt})
        await self._handle_broadcast_event(job_id, job_type, {"history": [msg.to_dict() for msg in history]})
        await self._handle_broadcast_event(job_id, job_type, {"raw_content": t2t_result})

        # Apply text filters
        async for text_chunk_out in self.op_manager.use_operation(OpRoles.FILTER_TEXT, {"content": t2t_result}):
            self.prompter.add_chat(self.prompter.character_name, text_chunk_out['content'])
            await self._handle_broadcast_event(job_id, job_type, text_chunk_out)
            if include_audio:
                # Apply tts
                async for audio_chunk_out in self.op_manager.use_operation(OpRoles.TTS, text_chunk_out):
                    # Apply tts filters
                    async for final_audio_chunk_out in self.op_manager.use_operation(OpRoles.FILTER_AUDIO, audio_chunk_out):
                        # Broadcast results (only the audio data for now)
                        for ws_chunk in chunk_buffer(base64.b64encode(final_audio_chunk_out['audio_bytes']).decode('utf-8')):
                            await self._handle_broadcast_event(job_id, job_type, {
                                "audio_bytes": ws_chunk,
                                "sr": final_audio_chunk_out['sr'],
                                "sw": final_audio_chunk_out['sw'],
                                "ch": final_audio_chunk_out['ch']
                            })
                        
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
        
    async def configure_context(
        self,
        job_id: str,
        job_type: JobType,
        name_translations: Dict[str, str] = None,
        character_name: str = None,
        history_length: int = None,
        instruction_prompt_filename: str = None,
        character_prompt_filename: str = None,
        scene_prompt_filename: str = None
    ):
        await self._handle_broadcast_start(job_id, job_type, {
            "name_translations": name_translations,
            "character_name": character_name,
            "history_length": history_length,
            "instruction_prompt_filename": instruction_prompt_filename,
            "character_prompt_filename": character_prompt_filename,
            "scene_prompt_filename": scene_prompt_filename
        })
        payload = dict()
        if name_translations: payload |= {"name_translations": name_translations}
        if character_name: payload |= {"character_name": character_name}
        if history_length: payload |= {"history_length": history_length}
        if history_length: payload |= {"history_length": history_length}
        if instruction_prompt_filename: payload |= {"instruction_prompt_filename": instruction_prompt_filename}
        if character_prompt_filename: payload |= {"character_prompt_filename": character_prompt_filename}
        if scene_prompt_filename: payload |= {"scene_prompt_filename": scene_prompt_filename}
        
        self.prompter.configure(payload)
        
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
        prompt = self.prompter.get_history_text() or "You're name is {}".format(self.prompter.character_name)
        content = ""
        async for out_d in self.op_manager.use_operation(OpRoles.STT, {"prompt": prompt, "audio_bytes": audio_bytes, "sr": sr, "sw": sw, "ch": ch}):
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
        last_line_o = self.prompter.history[-1]
        await self._handle_broadcast_event(job_id, job_type, {
            "timestamp": last_line_o.time.timestamp(),
            "content": last_line_o.message,
            "line": last_line_o.to_line()
        })
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
            await self.op_manager.load_operation(OpRoles(op_d.get('role', None)), op_d.get('id', None), op_d.get('config', dict()))
            await self._handle_broadcast_event(job_id, job_type, {
                "role": op_d.get('role', None), 
                "id": op_d.get('id', None),
                "loose_key": op_d.get("loose_key", None)
            })
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
            await self.op_manager.close_operation(OpRoles(op_d.get('role', None)), op_d.get('id', None))
            await self._handle_broadcast_event(job_id, job_type, {
                "role": op_d.get('role', None), 
                "id": op_d.get('id', None)
            })
        await self._handle_broadcast_success(job_id, job_type)
        
    async def configure_operations( # TODO document and add endpoint
        self,
        job_id: str,
        job_type: JobType,
        ops: List[Dict[str, str]] = []
    ):
        await self._handle_broadcast_start(job_id, job_type, {"ops": ops})
        for op_d in ops:
            await self.op_manager.configure(OpRoles(op_d.get('role', None)), op_d, op_id=op_d.get('id', None))
            await self._handle_broadcast_event(job_id, job_type, op_d)
        await self._handle_broadcast_success(job_id, job_type)
        
    async def use_operation(
        self,
        job_id: str,
        job_type: JobType,
        role: str = None,
        id: str = None,
        payload: Dict[str, Any] = None
    ):
        await self._handle_broadcast_start(job_id, job_type, {"role": role, "id": id})
        
        if 'audio_bytes' in payload:
            payload['audio_bytes'] = base64.b64decode(payload['audio_bytes'])

        if 'messages' in payload:
            msg_list = list()
            for msg in payload['messages']:
                assert 'type' in msg
                if msg['type'] == "raw":
                    msg_list.append(RawMessage(msg['message']))
                elif msg['type'] == "request":
                    msg_list.append(RequestMessage(msg['message'], datetime.datetime.fromtimestamp(msg['time'])))
                elif msg['type'] == "chat":
                    msg_list.append(ChatMessage(msg['user'], msg['message'], datetime.datetime.fromtimestamp(msg['time'])))
                elif msg['type'] == "tool":
                    msg_list.append(MCPMessage(msg['tool'], msg['message'], datetime.datetime.fromtimestamp(msg['time'])))
                elif msg['type'] == "custom":
                    msg_list.append(CustomMessage(msg['id'], msg['message'], datetime.datetime.fromtimestamp(msg['time'])))
                else:
                    raise Exception("Invalid message type")
            payload['messages'] = msg_list

        try:
            async for chunk_out in self.op_manager.use_operation(OpRoles(role), payload, op_id=id):
                await self._handle_broadcast_event(job_id, job_type, chunk_out)
        except OperationUnloaded:
            op = self.op_manager.loose_load_operation(OpRoles(role), id)
            await op.start()
            async for chunk_out in op(payload):
                if "audio_bytes" in chunk_out: chunk_out["audio_bytes"] = base64.b64encode(chunk_out['audio_bytes']).decode('utf-8')
                await self._handle_broadcast_event(job_id, job_type, chunk_out)
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
        to_broadcast = {
            "job_id": job_id,
            "start": payload
        }
        logging.debug("Broadcasting start ({}) {} {:.500}".format(job_id, job_type.value, str(to_broadcast)))
        await self.event_server.broadcast_event(job_type.value, to_broadcast)
    
    async def _handle_broadcast_event(self, job_id: str, job_type: JobType, payload: dict):
        to_broadcast = {
            "job_id": job_id,
            "finished": False,
            "result": payload
        }
        logging.debug("Broadcasting event ({}) {} {:.500}".format(job_id, job_type.value, str(to_broadcast)))
        await self.event_server.broadcast_event(job_type.value, to_broadcast)
    
    async def _handle_broadcast_success(self, job_id: str, job_type: JobType):
        to_broadcast = {
            "job_id": job_id,
            "finished": True,
            "success": True
        }
        logging.debug("Broadcasting success ({}) {} {}".format(job_id, job_type.value, str(to_broadcast)))
        await self.event_server.broadcast_event(job_type.value, to_broadcast)
        
    async def _handle_broadcast_error(self, job_id: str, job_type: JobType, err: Exception):
        # TODO: extend with all errors
        error_type = "unknown"
        if isinstance(err, UnknownOpType): error_type = "operation_unknown_type"
        if isinstance(err, UnknownOpRole): error_type = "operation_unknown_role"
        elif isinstance(err, UnknownOpID): error_type = "operation_unknown_id"
        elif isinstance(err, DuplicateFilter): error_type = "operation_duplicate"
        elif isinstance(err, OperationUnloaded): error_type = "operation_unloaded"
        elif isinstance(err, StartActiveError): error_type = "operation_active"
        elif isinstance(err, CloseInactiveError): error_type = "operation_inactive"
        elif isinstance(err, UsedInactiveError): error_type = "operation_inactive"
        elif isinstance(err, UnknownField): error_type = "config_unknown_field"
        elif isinstance(err, UnknownFile): error_type = "config_unknown_file"
        elif isinstance(err, UnknownJobType): error_type = "job_unknown"
        elif isinstance(err, asyncio.CancelledError): error_type = "job_cancelled"
        
        to_broadcast = {
            "job_id": job_id,
            "finished": True,
            "success": False,
            "result": {
                "type": error_type,
                "reason": str(err)
            }
        }
        
        logging.debug("Broadcasting error ({}) {} {}".format(job_id, job_type.value, str(to_broadcast)))
        await self.event_server.broadcast_event(job_type.value, to_broadcast)