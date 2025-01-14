'''
Main connecting layer between frontends and backend.

This class encapsulates the main functionality of this project. 
It manages the global configuration, orchestrates the AI models, 
and is the interface for the frontend. All components communicate 
through this layer.
'''

import json
import os
from scipy.io import wavfile
import wave
import traceback

from utils.config import Configuration
from utils.vts import VTS
from utils.twitch import TwitchContextMonitor
from utils.time import get_current_time
from utils.logging import create_sys_logger, save_dialogue, save_response
from utils.observer import ObserverServer
from utils.components.component_manager import ComponentManager
from utils.prompter import Prompter
from utils.filter import ResponseFilter

logger = create_sys_logger(use_stdout=True)

class JAIson():
    def __init__(self):
        # J.A.I.son configuration
        self.config = Configuration()

        # VTube Studio integrations
        self.vts = None

        # Twitch integrations
        self.twitch = None

        # Models
        self.comp_manager = None
        self.DEFAULT_RESPONSE_MSG = 'There is a problem with my AI...'

    def setup(self, init_config_file: str = None):
        logger.debug("Setting J.A.I.son application layer...")
        
        logger.debug(f"Loading config {init_config_file}...")
        # Setup config
        if init_config_file:
            self.load_config(init_config_file)
            self.response_cancelled = False

        # Setup event broadcasting server
        # List of events:
        #   response_generated: Triggered when a new response if fully finished creation ({"response":text_result})
        #   request_stop_response: Triggered when a request to stop the response is made
        logger.debug("Booting event broadcasting server...")
        self.broadcast_server = ObserverServer()

        # Initialize core models
        logger.debug("Initializing core components...")
        self.comp_manager = ComponentManager("E:\\projects\\jaison-core\\configs\\test.yaml") # debug
        self.comp_manager.load_components([
            "stt-openai-whisper-lcc",
            "t2t-openai-api-lcc",
            "ttsc-rvc-project-lcc",
            "ttsg-openai-api-lcc"
        ],reload=True)

        # Frontend components will have one-way reference
        # Frontend components have own threads

        # Initialize vts plugins
        logger.debug("Booting VTube Studio plugins...")
        self.vts = VTS(self.config)
        # Initialize twitch plugins
        logger.debug("Connecting to twitch...")
        self.twitch = TwitchContextMonitor(self)
        
        self.prompter = Prompter(self)
        self.filter = ResponseFilter()

        logger.info("J.A.I.son Main Applications successfully initialized!")

    def cleanup(self):
        if self.comp_manager:
            self.comp_manager.cleanup()

    ## CONFIG #####################

    def update_config(self, config_d: dict) -> tuple[bool, str]:
        logger.debug("Updating config...")
        try:
            return self.config.update(config_d)
        except Exception as err:
            logger.error(f"Failed to update config: {err}")
            raise err

    def load_config(self, filename: str) -> tuple[bool, str]:
        logger.debug(f"Loading config from file {filename}...")
        try:
            return self.config.load(filename)
        except Exception as err:
            logger.error(f"Failed to load config: {err}")
            raise err
    
    def save_config(self, config_d: dict = None, filename: str = None) -> bool:
        logger.debug(f"Saving config to file {filename}...")
        try:
            return self.config.save(config_d=config_d, filename=filename)
        except Exception as err:
            logger.error(f"Failed to save config: {err}")
            raise err

    ## RESPONSES #####################

    '''
    Pipeline for responding to text with text and optionally audio

    Note: No exceptions

    Input:
    - name: Name of input user
    - message: Their message
    - time: (optional) datetime time object for when message started
    - include_audio: (optional) Whether to return with audio response
    - include_animation: (optional) Whether to send animation event on completion
    Output:
    - (str) Text response
    - (str) Filepath to audio version of text response
    '''
    async def get_response_from_text(
        self, 
        name: str,
        message: str, 
        time: str = None, 
        include_audio: bool = False,
        include_animation: bool = False,
        include_broadcast: bool = True
    ) -> tuple[str, str]:
        logger.debug("Generating response from text...")
        self.response_cancelled = False
        start_time = get_current_time(as_str=False)
        if time is None:
            time = get_current_time()
        text_result, audio_result = None, None

        # Main response pipeline
        try:
            self.prompter.add_history(time, name, message)

            try:
                sys_prompt = self.prompter.get_sys_prompt()
                user_prompt = self.prompter.get_user_prompt()

                response_stream = self.comp_manager.use("t2t", {"system_input": sys_prompt, "user_input": user_prompt})
                text_response = ""
                for run_id, chunk in response_stream:
                    text_response += chunk
                text_response = text_response if text_response != self.prompter.NO_RESPONSE else None
            except Exception as err:
                logger.error(f"Failed to get response: {err}")
                logger.error(traceback.format_exc())
                text_response = self.DEFAULT_RESPONSE_MSG

            if text_response:
                try:
                    text_response = self.filter(text_response) # Apply filtering
                    self.prompter.add_history(
                        get_current_time(),
                        self.prompter.SELF_IDENTIFIER,
                        text_response
                    )
                    uncommited_messages = self.prompter.get_uncommited_history()
                    async for msg_o in uncommited_messages:
                        save_dialogue(self.prompter.convert_msg_o_to_line(msg_o))
                    self.prompter.commit_history()
                    save_response(sys_prompt, user_prompt, text_response)
                except Exception as err:
                    logger.error(f"Failed to save conversation: {err}")
                    logger.error(traceback.format_exc())
                    text_response = self.DEFAULT_RESPONSE_MSG
            else:
                try:
                    self.prompter.rollback_history()
                except Exception as err:
                    logger.error(f"Failed to rollback conversation: {err}")
                    logger.error(traceback.format_exc())
                    text_response = self.DEFAULT_RESPONSE_MSG

            if text_response is None: # Skip audio if silent
                return None, None

            

            if include_audio :
                ttsg_stream = self.comp_manager.use("ttsg",{"content":text_response})
                tts_raw = b''
                async for run_id, chunk in ttsg_stream:
                    tts_raw += chunk
                ttsc_stream = self.comp_manager.use("ttsc",{"audio":tts_raw})
                tts_audio = b''
                async for run_id, chunk in ttsc_stream:
                    tts_audio += chunk
                wavfile.write(self.config.RESULT_TTSC, 48000, tts_audio)
                audio_result =  self.config.RESULT_TTSC
        except Exception as err:
            logger.error(f"Failed to get responses", exc_info=True)
            return None, None

        # VTS on results
        try:
            if include_animation:
                self.vts.play_hotkey_using_message(text_response)
        except Exception as err:
            logger.error(f"Failed to play animation: {err}")

        end_time = get_current_time(as_str=False)
        logger.debug(f"Finished generating response from text in time: {str(end_time-start_time)}...")
        if include_broadcast:
            self.broadcast_server.broadcast_event("response_generated", payload={"response":text_result})
        return text_result, audio_result

    '''
    Audio input version of get_response_from_text

    Note: No Exceptions

    Input:
    - name: Name of input user
    - filepath: filepath to recorded speech file
    - time: (optional) datetime time object for when message started
    - include_audio: (optional) Whether to return with audio response
    - include_animation: (optional) Whether to send animation event on completion
    Output:
    - (str) Text response
    - (str) Filepath to audio version of text response
    '''
    async def get_response_from_audio(
        self,
        name: str,
        filepath: str,
        time: str = None, 
        include_audio: bool = False,
        include_animation: bool = False
    ):
        if time is None:
            time = get_current_time()

        logger.debug("Generating response from audio...")
        try:
            with wave.open(filepath) as f:
                audio = f.readframes(1000000)
            stt_streamer = self.comp_manager.use("stt",{"audio":audio})
            stt_result = ""
            async for run_id, chunk in stt_streamer:
                stt_result += chunk
        except Exception as err:
            logger.error(f"Failed to get response from audio: {err}")
            logger.error(traceback.format_exc())
            return None, None

        return await self.get_response_from_text(
            name, 
            stt_result, 
            time=time, 
            include_audio=include_audio,
            include_animation=include_animation
        )
    
    def cancel_response(self):
        self.response_cancelled = True
        self.broadcast_server.broadcast_event("request_stop_response")
        return True

    ## CONTEXTS

    def twitch_get_chat_history(self):
        return self.twitch.get_chat_history()

    ## SPECIAL API ENDPOINTS

    def twitch_auth_code(self, code):
        self.twitch.set_tokens_from_code(code)

    def inject_one_time_request(self, request: str):
        return self.t2t.inject_one_time_request(request)

    def get_name_translations(self):
        with open(os.path.join(self.config.t2t_name_translation_dir, self.config.t2t_name_translation_file), 'r') as f:
            translations = json.load(f)

        result = []
        for name in translations:
            result.append({
                "name": name,
                "translation": translations[name]
            })
        return { "result": result }

    def save_name_translations(self, translations: list):
        translations_d = {}
        for o in translations:
            translations_d[o["name"]] = o["translation"]
        with open(os.path.join(self.config.t2t_name_translation_dir, self.config.t2t_name_translation_file), 'w') as f:
            json.dump(translations_d, f, indent=4)
        return True

    def get_prompt_filenames(self):
        all_files = os.listdir(self.config.t2t_prompt_dir)
        result = [file for file in all_files if file.endswith('.txt')]
        return { "result": result }

    def load_prompt_file(self, filename: str):
        self.update_config({ "t2t_current_prompt_file": filename })
        return True

    def get_current_prompt(self):
        filename = self.config.t2t_current_prompt_file or self.config.t2t_default_prompt_file
        filepath = os.path.join(self.config.t2t_prompt_dir, filename)
        with open(filepath, 'r') as f:
            prompt_raw = f.read()

        return { "filename": filename, "prompt": prompt_raw}

    def save_prompt_file(self, filename, contents):
        with open(os.path.join(self.config.t2t_prompt_dir,filename), 'w') as f:
            f.write(contents)
        is_ok = self.update_config({ "t2t_current_prompt_file": filename })
        return is_ok

    def get_context_toggles(self):
        result = {
            "script": self.config.t2t_enable_context_script,
            "twitch-chat": self.config.t2t_enable_context_twitch_chat,
            "twitch-events": self.config.t2t_enable_context_twitch_events,
            "rag": self.config.t2t_enable_context_rag,
            "av": self.config.t2t_enable_context_av
        }
        return { "result": result }

    def set_context_toggles(self, toggles):
        is_ok = self.update_config({
            "t2t_enable_context_script": toggles.get("script", self.config.t2t_enable_context_script),
            "t2t_enable_context_twitch_chat": toggles.get("twitch-chat", self.config.t2t_enable_context_twitch_chat),
            "t2t_enable_context_twitch_events": toggles.get("twitch-events", self.config.t2t_enable_context_twitch_events),
            "t2t_enable_context_rag": toggles.get("rag", self.config.t2t_enable_context_rag),
            "t2t_enable_context_av": toggles.get("av", self.config.t2t_enable_context_av)
        })
        return is_ok

    def get_config_from_file(self, filename):
        filepath = os.path.join(self.config.CONFIG_DIR, filename)
        with open(filepath, 'r') as f:
            return json.load(f)

    def get_config_files(self):
        all_files = os.listdir(self.config.CONFIG_DIR)
        result = [file for file in all_files if file.endswith('.json')]
        return { "config_files": result, "current": self.config.CURRENT_CONFIG_FILENAME }

    def set_config_file(self, filename):
        is_ok = self.load_config(filename)
        return is_ok

    def save_config_file(self, filename, config_d):
        is_ok = self.update_config(config_d)
        if is_ok:
            is_ok = self.save_config(filename=filename)
        return is_ok