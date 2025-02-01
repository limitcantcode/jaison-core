'''
Main connecting layer between frontends and backend.

This class encapsulates the main functionality of this project. 
It manages the global configuration, orchestrates the AI models, 
and is the interface for the frontend. All components communicate 
through this layer.
'''

import os
import wave
import datetime
import asyncio
import uuid
import json

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

    def __init__(self):
        # J.A.I.son configuration
        self.config = Configuration()

        # Setup event broadcasting server
        # List of events:
        #   run_start: New response_pipeline run starts ({run_id})
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
        #   run_tts_chunk: TTS streamed result ({run_id, chunk, sample_rate, sample_width, channels, success})
        #   run_tts_stop: TTS stage completion ({run_id, success})
        #
        # Event parameter notes:
        # - "success" field indicates if event is part of normal generation (True) or some exception (False). If False, the unsuccessful chunks overwrite any of the older successful chunks of that stage.
        # - "runtime" is time for pipeline to finish in seconds
        self.broadcast_server = ObserverServer()

        # Components
        self.comp_manager = None
        self.comp_manager = ComponentManager(os.path.join(self.config.plugins_config_dir, self.config.plugins_config_file))
        self.comp_manager.load_components(self.config.active_plugins,reload=True)
        
        # Other response_pipeline helpers
        self.prompter = Prompter()
        self.filter = ResponseFilter()
        self.RESPONSE_ERROR_MSG = 'There is a problem with my AI...'

        self.active_runs = dict()

        logger.info("JAIson application layer initialized!")

    def cleanup(self):
        if self.comp_manager:
            self.comp_manager.cleanup()
        logger.info("JAIson application layer cleaned up")

    def create_run(self, **kwargs):
        new_run_id = uuid.uuid4()
        self.active_runs[new_run_id] = asyncio.create_task(self.response_pipeline(
                new_run_id,
                **kwargs
        ))
        return new_run_id
    
    def cancel_run(self, run_id: uuid.UUID, reason: str = None):
        run = self.active_runs.get(run_id)
        if run is None:
            raise NonexistantRunException(f"Run {run_id} does not exist or already finished")
        cancel_message = f"Run {run_id} cancelled"
        if reason: cancel_message += f" because {reason}"
        run.cancel(cancel_message)
        del self.active_runs[run_id]
        

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
    - run_id: (optional uuid.UUID): Unique run id
    - process_dialog: (optional bool) Process input as a line in conversation
    - process_request: (optional bool) Process input as a special request from anyone
    - input_user: (optional str) User in conversation input is associated with (if not a request)
    - input_time: (optional datetime.datetime) Time associated with line in conversation
    - input_audio_bytes: (optional bytes) Audio bytes to transcribe and use as input
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
        run_id: uuid.UUID,
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
        logger.debug(f"Starting response_pipeline for run {run_id}")
        self.broadcast_server.broadcast_event("run_start", {"run_id": run_id})
        try:
            # Basic request validation
            if (input_text is None) == (input_audio_bytes is None): raise Exception("Exactly one text of audio can be used as input")
            if not ((input_audio_bytes is None) or (input_audio_bytes and input_audio_sample_rate and input_audio_sample_width and input_audio_channels)): raise Exception("Audio needs to specify input_audio_bytes, input_audio_sample_rate, input_audio_sample_width, and input_audio_channels")
            if process_dialog == process_request: raise Exception("Exactly one of process_dialog and process_request must be True")
            if process_dialog and not input_user: raise Exception("input_user must be specified for processing dialog")

            # Generate textual response from input
            try:
                start_time = get_current_time(as_str=False)
                
                if input_time is None:
                    input_time = get_current_time(include_ms=False)
                    logger.debug(f"Run {run_id} default using current time {input_time}")

                self.broadcast_server.broadcast_event("run_stt_start", {"run_id": run_id})
                if input_audio_bytes:
                    logger.debug(f"Run {run_id} using STT")
                    input_text = ""
                    async for response_chunk in self.comp_manager.use(
                        "stt",
                        iter([{
                            "run_id": run_id,
                            "audio_chunk":input_audio_bytes,
                            "sample_rate": input_audio_sample_rate,
                            "sample_width": input_audio_sample_width,
                            "channels": input_audio_channels
                        },])
                    ):
                        input_text += response_chunk['content_chunk']
                        self.broadcast_server.broadcast_event("run_stt_chunk", {"run_id": run_id, "chunk": input_text, "success": True})
                    self.broadcast_server.broadcast_event("run_stt_stop", {"run_id": run_id, "result": input_text, "success": True})
                    logger.debug(f"Run {run_id} finished STT with result: {input_text:.50}")

                logger.debug(f"Run {run_id} using input text: {input_text:.50}")
                if process_dialog:
                    logger.debug(f"Run {run_id} adding to history under user {input_user}")
                    self.prompter.add_history(input_time, input_user, input_text) # TODO synchronize across pipelines with a queue in prompter
                elif process_request:
                    logger.debug(f"Run {run_id} adding to special requests")
                    self.prompter.add_special_request(input_text)
                else:
                    raise Exception("process_dialog and process_request are both false when exactly one should be true")
                
                if not output_text: return
                
                # TODO update optional contexts with component contexts
                # special requests are the only way for applications to add additional context to prompt
                logger.debug(f"Run {run_id} using contexts and getting prompts")
                self.broadcast_server.broadcast_event("run_context_start", {"run_id": run_id})
                sys_prompt = self.prompter.get_sys_prompt()
                user_prompt = self.prompter.get_user_prompt()
                self.broadcast_server.broadcast_event("run_context_chunk", {"run_id": run_id, "sys_chunk": sys_prompt, "user_chunk": user_prompt, "success": True})
                self.broadcast_server.broadcast_event("run_context_stop", {"run_id": run_id, "success": True})
                logger.debug(f"Run {run_id} got following prompts")
                logger.debug(f"Run {run_id} sys_prompt: {sys_prompt:.100}")
                logger.debug(f"Run {run_id} user_prompt: {user_prompt:.100}")

                logger.debug(f"Run {run_id} using T2T")
                self.broadcast_server.broadcast_event("run_t2t_start", {"run_id": run_id})
                t2t_result = "" # TODO figure out filtering in stream. Until then, generate full response before proceeding (tts will be streamed)
                async for response_chunk in self.comp_manager.use(
                    "t2t",
                    iter([{
                        "run_id": run_id, 
                        "system_input_chunk": sys_prompt, 
                        "user_input_chunk": user_prompt
                    },])
                ):
                    chunk = response_chunk['content_chunk']
                    t2t_result += chunk
                    if self.filter(t2t_result):
                        self.broadcast_server.broadcast_event("run_t2t_chunk", {"run_id": run_id, "chunk": chunk, "success": True})
                self.broadcast_server.broadcast_event("run_t2t_stop", {"run_id": run_id, "success": True})
            except asyncio.CancelledError:
                raise
            except FilteredException as err:
                logger.warning(f"Response was filtered with result so far: {t2t_result}")
                t2t_result = self.filter.FILTERED_MESSAGE
                self.broadcast_server.broadcast_event("run_t2t_chunk", {"run_id": run_id, "chunk": t2t_result, "success": False})
                self.broadcast_server.broadcast_event("run_t2t_stop", {"run_id": run_id, "success": False})
            except Exception as err:
                logger.error("Error occured during text response generation", exc_info=True, stack_info=True)
                t2t_result = self.RESPONSE_ERROR_MSG
                self.broadcast_server.broadcast_event("run_t2t_chunk", {"run_id": run_id, "chunk": t2t_result, "success": False})
                self.broadcast_server.broadcast_event("run_t2t_stop", {"run_id": run_id, "success": False})
            logger.debug(f"Run {run_id} finished T2T with result: {t2t_result}")
            
            logger.debug(f"Run {run_id} logging results of T2T")
            # Save response regardless of result # TODO synchronize across pipelines with a queue in prompter
            self.prompter.add_history(
                start_time,
                self.prompter.SELF_IDENTIFIER,
                t2t_result
            )
            save_response(sys_prompt, user_prompt, t2t_result)

            # Process audio if appropriate
            if t2t_result != self.prompter.NO_RESPONSE and output_audio:
                logger.debug(f"Run {run_id} using TTS")
                self.broadcast_server.broadcast_event("run_tts_start", {"run_id": run_id})
                audio_result, audio_sample_rate, audio_sample_width, audio_channels = None, None, None, None,
                ttsg_stream = self.comp_manager.use("ttsg",iter([{"run_id": run_id, "content_chunk":t2t_result},]))
                async for response_chunk in self.comp_manager.use("ttsc", ttsg_stream):
                    audio_result += response_chunk['audio_chunk']
                    audio_sample_rate, audio_sample_width, audio_channels = response_chunk['sample_rate'], response_chunk['sample_width'], response_chunk['channels']
                    self.broadcast_server.broadcast_event("run_tts_chunk", {"run_id": run_id, "chunk": chunk, "sample_rate": audio_sample_rate, "sample_width": audio_sample_width, "channels": audio_channels, "success": True})
                self.broadcast_server.broadcast_event("run_tts_stop", {"run_id": run_id, "success": True})
                logger.debug(f"Run {run_id} finished TTS")
                
                logger.debug(f"Run {run_id} saving result of TTS to {self.config.RESULT_TTSC}")
                # Saving results for debugging or caching
                f = wave.open(self.config.RESULT_TTSC, 'wb')
                f.setnchannels(audio_channels)
                f.setsampwidth(audio_sample_width)
                f.setframerate(audio_sample_rate)
                f.writeframes(audio_result)
                f.close()
            stop_time = get_current_time(as_str=False)
            duration = (stop_time-start_time).total_seconds()
            logger.info(f"Finished response_pipeline {run_id} generation in {duration} seconds", exc_info=True, stack_info=True)
            self.broadcast_server.broadcast_event("run_finish", {"run_id": run_id, "runtime": duration})
        except asyncio.CancelledError as err:
            logger.warning(f"Cancelled response_pipeline {run_id} generation", exc_info=True, stack_info=True)
            self.broadcast_server.broadcast_event('run_cancel', {"run_id": run_id, "reason": err.message})
        except Exception as err:
            logger.error(f"Something went wrong during response_pipeline {run_id} generation", exc_info=True, stack_info=True)
            self.broadcast_server.broadcast_event('run_cancel', {"run_id": run_id, "reason": err})
        finally:
            del self.active_runs[run_id]
