'''
Main connecting layer between frontends and backend.

This class encapsulates the main functionality of this project. 
It manages the global configuration, orchestrates the AI models, 
and is the interface for the frontend. All components communicate 
through this layer.
'''

import os
import datetime
import asyncio
import uuid
import base64
from itertools import chain

from utils.helpers.singleton import Singleton
from utils.config import Configuration
from utils.time import get_current_time
from utils.logging import create_sys_logger, save_response
from utils.observer import ObserverServer
from utils.components.component_manager import ComponentManager
from utils.prompter import Prompter
from utils.filter import ResponseFilter, FilteredException

logger = create_sys_logger(use_stdout=True)

class NonexistantRunException(Exception):
    pass

class JAIson(metaclass=Singleton):
    RESPONSE_PIPELINE_DEFAULT = {
        'process_dialog': False,
        'process_request': False,
        'input_user': None,
        'input_time': None,
        'input_audio_bytes': None,
        'input_audio_sample_rate': None,
        'input_audio_sample_width': None,
        'input_audio_channels': None,
        'input_text': None,
        'output_text': True,
        'output_audio': True
    }
    MAX_CHUNK_BROADCAST_SIZE = 4096 # There is a size limit for websockets and http

    def __init__(self):
        # J.A.I.son configuration
        self.config = Configuration()

        # Manage runs
        self.active_runs = None
        self.run_queue = None

        # Setup event broadcasting server
        # List of events:
        #   run_start: New response_pipeline run starts ({run_id, output_text, output_audio})
        #   run_finish: response_pipeline run finishes successfully ({run_id, runtime})
        #   run_cancel: response_pipeline cancelled for some reason and didn't finish successfully ({run_id, reason})
        #   run_stt_start: STT stage began ({run_id})
        #   run_stt_chunk: STT streamed result ({run_id, chunk, success})
        #   run_stt_stop: STT stage completion ({run_id, success})
        #   run_context_start: Context generation stage began ({run_id})
        #   run_context_chunk: Context generation streamed result ({run_id, sys_chunk, user_chunk, success})
        #   run_context_stop: Context generation stage completion ({run_id, success})
        #   run_t2t_start: T2T stage began ({run_id})
        #   run_t2t_chunk: T2T streamed result ({run_id, chunk, success})
        #   run_t2t_stop: T2T stage completion ({run_id, success})
        #   run_tts_start: TTS stage began ({run_id})
        #   run_tts_chunk: TTS streamed result ({run_id, chunk, sample_rate, sample_width, channels, success}) (chunk is bytes in base64 utf-8)
        #   run_tts_stop: TTS stage completion ({run_id, success})
        #
        # Event parameter notes:
        # - "success" field indicates if event is part of normal generation (True) or some exception (False). If False, the unsuccessful chunks overwrite any of the older successful chunks of that stage.
        # - "runtime" is time for pipeline to finish in seconds
        self.broadcast_server = ObserverServer()

        # Components
        self.comp_manager = None
        
        # Other response_pipeline helpers
        self.prompter = None
        self.filter = None
        self.RESPONSE_ERROR_MSG = 'There is a problem with my AI...'

        logger.info("JAIson application layer initialized!")

    async def setup(self):
        self.comp_manager = ComponentManager()
        await self.comp_manager.reload_config(os.path.join(self.config.plugins_config_dir, self.config.plugins_config_file))
        self.comp_manager.load_components(self.config.active_plugins,reload=True)
        self.prompter = Prompter()
        self.filter = ResponseFilter()
        self.active_runs = dict() # for tracking actively processing runs
        self.run_queue_d = dict() # for tracking all runs
        self.run_queue = asyncio.Queue() # for queueing up runcs to be processed
        asyncio.create_task(self._process_run_loop())
        logger.info("JAIson application layer setup!")

    def cleanup(self):
        logger.debug("JAIson application layer cleaning up")
        if self.comp_manager:
            self.comp_manager.cleanup()
        logger.info("JAIson application layer cleaned up")

    ## Response Run Management #################

    # Add async task to Queue to be ran in the order it was requested
    async def create_run(self, **kwargs):
        new_run_id = str(uuid.uuid4())
        assert(new_run_id not in self.run_queue_d)
        logger.debug(f"Creating new run {new_run_id}")
        self.run_queue_d[new_run_id] = self.response_pipeline(new_run_id, **kwargs)
        await self.run_queue.put(self.run_queue_d[new_run_id])
        return new_run_id
    
    async def cancel_run(self, run_id: uuid.UUID, reason: str = None):
        if self.run_queue_d.get(run_id) is None: raise NonexistantRunException(f"Run {run_id} does not exist or already finished")
        
        logger.debug(f"Cancelling run {run_id}")
        cancel_message = f"Run {run_id} cancelled"
        if reason: cancel_message += f" because {reason}"
        logger.debug(cancel_message)

        run = self.active_runs.get(run_id)
        if run is not None: # If run is outside of Queue and already running as a Task
            run.cancel(cancel_message)
        else: # If run is still in Queue
            temp_queue = asyncio.Queue()
            while not self.run_queue.empty(): # Transfer contents 1 by 1, skipping target
                coro = await self.run_queue.get()
                if coro is self.run_queue_d[run_id]: continue
                await temp_queue.put(coro)
            self.run_queue.shutdown(immediate=True) # Replace with new queue
            self.run_queue = temp_queue
            del self.run_queue_d[run_id]

    # Side loop responsible for running the next run in the Queue
    async def _process_run_loop(self):
        while True:
            try:
                coro = await self.run_queue.get()
                run_id = list(self.run_queue_d.keys())[list(self.run_queue_d.values()).index(coro)]
                self.active_runs[run_id] = asyncio.create_task(coro)
                await asyncio.wait([self.active_runs[run_id]])
            except Exception as err:
                logger.error("Encountered error in main run processing loop", exc_info=True)
                asyncio.sleep(1)

    # Helper for streaming contents to fix websocket size constraints
    def _generate_iterable(self, base_d: dict, chunk_key: str, slicable_chunk: bytes | str):
        iterable = []
        while len(slicable_chunk) > 0:
            iterable.append(base_d | { chunk_key: slicable_chunk[:self.MAX_CHUNK_BROADCAST_SIZE] })
            slicable_chunk = slicable_chunk[self.MAX_CHUNK_BROADCAST_SIZE:]
        return iter(iterable)
            
    '''
    Main response generating pipeline

    Note:

    If process_dialog is True, inputs will be added to the main conversation history 
    and new conversation history will be used to prompt JAIson.

    If process_request is True, inputs will not be added to main conversation history.
    These inputs will not be stored between generations. (So like a one time request)

    If output_text if False, no text OR AUDIO is generated. This is simply for adding to
    the conversation/context without trying to generate a response, effectively queuing it 
    for the next response generation

    Requirements:
    - Exactly one of process_dialog and process_request must be set
    - Audio inputs include all kwargs starting with 'input_audio_...'. Either all of these are set, or 'input_text' is set, but not both
    
    Input:
    - run_id: (str): Unique uuid.UUID run id as string
    - process_dialog: (optional bool) Process input as a line in conversation
    - process_request: (optional bool) Process input as a special request from anyone
    - input_user: (optional str) User in conversation input is associated with (if not a request)
    - input_time: (optional datetime.datetime) Time associated with line in conversation
    - input_audio_bytes: (optional bytes | str) Audio bytes (or str representing bytes in base64 utf-8) to transcribe and use as input
    - input_audio_sample_rate: (optional int) Audio sample rate if audio bytes is used
    - input_audio_sample_width: (optional int) Audio sample width if audio bytes is used
    - input_audio_channels: (optional int) Audio channels if audio bytes is used
    - input_text: (optional str) Text to use as input
    - output_text: (optional bool) Whether to consume inputs to generate up to end of T2T generation
    - output_audio: (optional bool) Whether to consume inputs to generate up to end of TTS generation (all)
    Output:
    - broadcasts: [
        run_start,
        run_finish,
        run_cancel,
        run_stt_start,
        run_stt_chunk,
        run_stt_stop,
        run_context_start,
        run_context_chunk,
        run_context_stop,
        run_t2t_start,
        run_t2t_chunk,
        run_t2t_stop,
        run_tts_start,
        run_tts_chunk,
        run_tts_stop
    ]
    '''
    async def response_pipeline(
        self,
        run_id: str,
        input_user: str = None,
        input_time: datetime.datetime = None,
        input_audio_bytes: bytes = None,
        input_audio_sample_rate: int = None,
        input_audio_sample_width: int = None,
        input_audio_channels: int = None,
        input_text: str = None,
        process_dialog: bool = False,
        process_request: bool = False,
        output_text: bool = True,
        output_audio: bool = True
    ) -> None:
        try:
            logger.debug(f"Starting response_pipeline for run {run_id}")
            await self.broadcast_server.broadcast_event("run_start", {"run_id": run_id, "output_text": output_text or output_audio, "output_audio": output_audio})
            
            # Basic request validation
            if (input_text is None) == (input_audio_bytes is None): raise Exception("Exactly one text of audio can be used as input")
            if not ((input_audio_bytes is None) or (input_audio_bytes and input_audio_sample_rate and input_audio_sample_width and input_audio_channels)): raise Exception("Audio needs to specify input_audio_bytes, input_audio_sample_rate, input_audio_sample_width, and input_audio_channels")
            if process_dialog == process_request: raise Exception("Exactly one of process_dialog and process_request must be True")
            if process_dialog and not input_user: raise Exception("input_user must be specified for processing dialog")

            # Generate textual response from input
            try:
                start_time = get_current_time(as_str=False) # For metrics

                if input_time is None:
                    input_time = get_current_time(include_ms=False)
                    logger.debug(f"Run {run_id} default using current time {input_time}")

                # STT Generation
                if input_audio_bytes:
                    await self.broadcast_server.broadcast_event("run_stt_start", {"run_id": run_id})
                    logger.debug(f"Run {run_id} using STT")
                    if isinstance(input_audio_bytes, str): input_audio_bytes = base64.b64decode(input_audio_bytes)
                    input_text = ""
                    async for response_chunk in self.comp_manager.use("stt", self._generate_iterable(
                        {
                            "run_id": run_id,
                            "sample_rate": input_audio_sample_rate,
                            "sample_width": input_audio_sample_width,
                            "channels": input_audio_channels
                        },
                        "audio_chunk", input_audio_bytes
                    )):
                        chunk = response_chunk['content_chunk']
                        input_text += chunk
                        for msg in self._generate_iterable({"run_id": run_id, "success": True}, "chunk", chunk):
                            await self.broadcast_server.broadcast_event("run_stt_chunk", msg)
                    await self.broadcast_server.broadcast_event("run_stt_stop", {"run_id": run_id, "success": True})
                    logger.debug(f"Run {run_id} finished STT with result: {input_text:.50}")

                # Save to conversation or request context
                logger.debug(f"Run {run_id} using input text: {input_text:.50}")
                if process_dialog:
                    logger.debug(f"Run {run_id} adding to history under user {input_user}")
                    self.prompter.add_history(input_time, input_user, input_text)
                elif process_request:
                    logger.debug(f"Run {run_id} adding to special requests")
                    self.prompter.add_special_request(input_text)
                else:
                    raise Exception("process_dialog and process_request are both false when exactly one should be true")
                
                if not (output_text or output_audio): # Skip all generation if just adding to contexts
                    stop_time = get_current_time(as_str=False)
                    duration = (stop_time-start_time).total_seconds()
                    logger.info(f"Finished response_pipeline {run_id} generation in {duration} seconds", exc_info=True, stack_info=True)
                    await self.broadcast_server.broadcast_event("run_finish", {"run_id": run_id, "runtime": duration})
                    return
                
                # Getting prompts
                # special requests are the only way for applications to add additional context to prompt
                logger.debug(f"Run {run_id} using contexts and getting prompts")
                await self.broadcast_server.broadcast_event("run_context_start", {"run_id": run_id})
                sys_prompt = self.prompter.get_sys_prompt()
                user_prompt = self.prompter.get_user_prompt()
                for msg in self._generate_iterable({"run_id": run_id, "user_chunk": "", "success": True}, "sys_chunk", sys_prompt):
                    await self.broadcast_server.broadcast_event("run_context_chunk", msg)
                for msg in self._generate_iterable({"run_id": run_id, "sys_chunk": "", "success": True}, "user_chunk", user_prompt):
                    await self.broadcast_server.broadcast_event("run_context_chunk", msg)
                logger.debug(f"Run {run_id} got following prompts")
                logger.debug(f"Run {run_id} sys_prompt: {sys_prompt:.200}")
                logger.debug(f"Run {run_id} user_prompt: {user_prompt:.200}")

                # T2T Generation
                logger.debug(f"Run {run_id} using T2T")
                await self.broadcast_server.broadcast_event("run_t2t_start", {"run_id": run_id})
                t2t_result = ""
                async for response_chunk in self.comp_manager.use(
                    "t2t",
                    chain(
                        self._generate_iterable({"run_id": run_id, "user_input_chunk": ""}, "system_input_chunk", sys_prompt),
                        self._generate_iterable({"run_id": run_id, "system_input_chunk": ""}, "user_input_chunk", user_prompt)
                    )
                ):
                    chunk = response_chunk['content_chunk']
                    t2t_result += chunk
                    if self.filter(t2t_result):
                        for msg in self._generate_iterable({"run_id": run_id, "success": True}, "chunk", chunk):
                            await self.broadcast_server.broadcast_event("run_t2t_chunk", msg)
                await self.broadcast_server.broadcast_event("run_t2t_stop", {"run_id": run_id, "success": True})
            except asyncio.CancelledError:
                raise
            except FilteredException as err:
                logger.warning(f"Response was filtered with result so far: {t2t_result}")
                t2t_result = self.filter.FILTERED_MESSAGE
                await self.broadcast_server.broadcast_event("run_t2t_chunk", {"run_id": run_id, "chunk": t2t_result, "success": False})
                await self.broadcast_server.broadcast_event("run_t2t_stop", {"run_id": run_id, "success": False})
            except Exception as err:
                logger.error("Error occured during text response generation", exc_info=True, stack_info=True)
                t2t_result = self.RESPONSE_ERROR_MSG
                await self.broadcast_server.broadcast_event("run_t2t_chunk", {"run_id": run_id, "chunk": t2t_result, "success": False})
                await self.broadcast_server.broadcast_event("run_t2t_stop", {"run_id": run_id, "success": False})
            logger.debug(f"Run {run_id} finished T2T with result: {t2t_result}")

            # Process audio if appropriate
            if output_audio:
                # TTSG and TTSC generation (streaming continuous streaming)
                logger.debug(f"Run {run_id} using TTS")
                await self.broadcast_server.broadcast_event("run_tts_start", {"run_id": run_id})
                ttsg_stream = self.comp_manager.use("ttsg",iter([{"run_id": run_id, "content_chunk":t2t_result},]))
                async for response_chunk in self.comp_manager.use("ttsc", ttsg_stream):
                    chunk = response_chunk['audio_chunk']
                    for msg in self._generate_iterable(
                        {"run_id": run_id, "sample_rate": response_chunk['sample_rate'], "sample_width": response_chunk['sample_width'], "channels": response_chunk['channels'], "success": True},
                        "chunk", base64.b64encode(chunk).decode('utf-8')
                    ):
                        await self.broadcast_server.broadcast_event("run_tts_chunk", msg)
                await self.broadcast_server.broadcast_event("run_tts_stop", {"run_id": run_id, "success": True})
                logger.debug(f"Run {run_id} finished TTS")
            stop_time = get_current_time(as_str=False)
            duration = (stop_time-start_time).total_seconds()
            logger.info(f"Finished response_pipeline {run_id} generation in {duration} seconds")
            await self.broadcast_server.broadcast_event("run_finish", {"run_id": run_id, "runtime": duration})

            # Add response to contexts
            self.prompter.add_history(
                start_time,
                self.prompter.SELF_IDENTIFIER,
                t2t_result
            )
            # Log result
            save_response(sys_prompt, user_prompt, t2t_result)
        except asyncio.CancelledError as err:
            logger.warning(f"Cancelled response_pipeline {run_id} generation", exc_info=True, stack_info=True)
            await self.broadcast_server.broadcast_event('run_cancel', {"run_id": run_id, "reason": str(err)})
        except Exception as err:
            logger.error(f"Something went wrong during response_pipeline {run_id} generation", exc_info=True, stack_info=True)
            await self.broadcast_server.broadcast_event('run_cancel', {"run_id": run_id, "reason": str(err)})
        finally:
            del self.active_runs[run_id]
            del self.run_queue_d[run_id]

    ## Context Management #################

    def register_context(self, context_id, context_title, context_description):
        self.prompter.add_optional_context(context_id, context_title, context_description=context_description)

    def update_context(self, context_id, context_contents):
        self.prompter.update_optional_context(context_id, contents=context_contents)

    def unregister_context(self, context_id):
        self.prompter.remove_optional_context(context_id)