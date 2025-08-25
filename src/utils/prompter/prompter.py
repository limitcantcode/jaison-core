
import os
import datetime
from typing import AsyncGenerator, Dict, List, Any
from utils.helpers.time import get_current_time
from utils.helpers.singleton import Singleton
from utils.helpers.path import portable_path
from utils.config import Config
from .context import ContextMetadata
from .message import Message, ChatMessage, RequestMessage, MCPMessage, CustomMessage

class Prompter(metaclass=Singleton):
    def __init__(self):
        self.context_metadata: Dict[str, ContextMetadata] = dict()
        self.history: List[Message] = list()
        
        self.instruction_prompt_filename: str = 'example.txt'
        self.character_prompt_filename: str = 'example.txt'
        self.scene_prompt_filename: str = 'example.txt'

        self.character_name: str = "J.A.I.son"
        self.name_translations: Dict[str, str] = {"old name": "new:name"}
        self.history_length: int = 50
        
        self.tooling_prompt = ""
        self.response_template = ""
        
    async def configure(self, config_d: Dict[str, Any]):
        if "instruction_prompt_filename" in config_d: self.instruction_prompt_filename = str(config_d["instruction_prompt_filename"])
        if "character_prompt_filename" in config_d: self.character_prompt_filename = str(config_d["character_prompt_filename"])
        if "scene_prompt_filename" in config_d: self.scene_prompt_filename = str(config_d["scene_prompt_filename"])
        if "character_name" in config_d: self.character_name = str(config_d["character_name"])
        if "name_translations" in config_d: self.name_translations = dict(config_d["name_translations"])
        if "history_length" in config_d: self.history_length = int(config_d["history_length"])
        
        assert (
            self.instruction_prompt_filename is not None and 
            len(self.instruction_prompt_filename) > 0 and 
            os.path.isfile(portable_path(os.path.join(
                Config().PROMPT_DIR,
                Config().PROMPT_INSTRUCTION_SUBDIR,
                self.instruction_prompt_filename
            )))
        )
        assert (
            self.character_prompt_filename is not None and 
            len(self.character_prompt_filename) > 0 and 
            os.path.isfile(portable_path(os.path.join(
                Config().PROMPT_DIR,
                Config().PROMPT_CHARACTER_SUBDIR,
                self.character_prompt_filename
            )))
        )
        assert (
            self.scene_prompt_filename is not None and 
            len(self.scene_prompt_filename) > 0 and 
            os.path.isfile(portable_path(os.path.join(
                Config().PROMPT_DIR,
                Config().PROMPT_SCENE_SUBDIR,
                self.scene_prompt_filename
            )))
        )
        assert self.character_name is not None and len(self.character_name)
        assert self.history_length > 0
        
        
    def clear_history(self):
        self.history = list()
        
    def insert_history(self, message: Message):
        self.history.append(message)
        self.history = self.history[-(self.history_length):]
        
        with open(Config().history_filepath, 'a', encoding="utf-8") as f:
            f.write(message.to_line())
            f.write("\n")
    
    # Custom context
    def register_custom_context(self, context_id: str, context_name: str, context_description: str = None):
        
        self.context_metadata[context_id] = ContextMetadata(context_id, context_name, context_description)

    def remove_custom_context(self, context_id: str):
        assert context_id in self.context_metadata
        
        del self.context_metadata[context_id]

    def add_custom_context(self, context_id: str, contents: str, time: datetime.datetime = None):
        assert context_id in self.context_metadata
        assert contents and len(contents) > 0
        
        if time is None: time = get_current_time(include_ms=False, as_str=False)
        self.insert_history(CustomMessage(self.context_metadata[context_id], contents, time))

    # Main conversation
    def translate_name(self, name: str):
        return self.name_translations.get(name, name)
    
    def add_chat(self, name: str, message: str, time: datetime.datetime = None):
        assert name and len(name) > 0
        assert message and len(message) > 0
        
        if time is None: time = get_current_time(include_ms=False, as_str=False)
        self.insert_history(ChatMessage(self.translate_name(name), message, time))
        
    async def add_chat_stream(self, name: str, in_stream: AsyncGenerator, time: datetime.datetime = None):
        if time is None: time = get_current_time(include_ms=False, as_str=False)
        
        message = ''
        async for in_d in in_stream:
            message += in_d['content']
        
        self.insert_history(ChatMessage(self.translate_name(name), message, time))

    # Requests
    def add_request(self, message: str, time: datetime.datetime = None):
        assert message and len(message) > 0
        
        if time is None: time = get_current_time(include_ms=False, as_str=False)
        
        self.insert_history(RequestMessage(message, time))
        
    # Prompt generators
    def get_instructions_prompt(self):
        with open(portable_path(os.path.join(
            Config().PROMPT_DIR,
            Config().PROMPT_INSTRUCTION_SUBDIR,
            self.instruction_prompt_filename
        )), 'r') as f:
            return f.read()
        
    def get_context_descriptions(self):
        result = ""
        for context_id in self.context_metadata:
            result += "{name}: {description}\n".format(
                name=self.context_metadata[context_id].name,
                description=self.context_metadata[context_id].description
            )
            
        return result
            
    def get_character_prompt(self):
        with open(portable_path(os.path.join(
            Config().PROMPT_DIR,
            Config().PROMPT_CHARACTER_SUBDIR,
            self.character_prompt_filename
        )), 'r') as f:
            return f.read()
        
    def get_scene_prompt(self):
        with open(portable_path(os.path.join(
            Config().PROMPT_DIR,
            Config().PROMPT_SCENE_SUBDIR,
            self.scene_prompt_filename
        )), 'r') as f:
            return f.read()
    
    def get_sys_prompt(self):
        return "{instructions}\n{mcp_usage}\n{contexts}\n### Character ###\n{character}\n### Scene ###\n{scene}".format(
            instructions = self.get_instructions_prompt(),
            contexts = self.get_context_descriptions(),
            mcp_usage = self.response_template,
            character = self.get_character_prompt(),
            scene = self.get_scene_prompt(),
        )

    def get_history_text(self):
        prompt = ""
        
        for message in self.history:
            message_line = message.to_line()
            prompt += "\n{}".format(message_line)
            
        return prompt
    
    def get_history(self):
        return self.history

    def add_mcp_usage_prompt(self, tooling_prompt: str, response_template: str):
        self.tooling_prompt = tooling_prompt
        self.response_template = response_template
        
    def generate_mcp_system_context(self):
        return self.tooling_prompt
    
    def generate_mcp_user_context(self):
        user_prompt = self.get_history_text()
        character = self.get_character_prompt()
        scene = self.get_scene_prompt()
        
        return f"<CHARACTER>{character}<SCENE>{scene}<SCRIPT>{user_prompt}\n"

    def add_mcp_results(self, results):
        for result in results:
            tool_name = result[0]
            tool_result = result[1]
            time = get_current_time(include_ms=False, as_str=False)
            
            self.insert_history(MCPMessage(tool_name, tool_result, time))
            
            