
import os
import datetime
from typing import AsyncGenerator, Dict, List
from utils.helpers.time import get_current_time
from utils.helpers.singleton import Singleton
from utils.config import Config
from .context import ContextMetadata
from .message import Message, ChatMessage, RequestMessage, CustomMessage

class Prompter(metaclass=Singleton):
    def __init__(self):
        self.context_metadata: Dict[str, ContextMetadata] = dict()
        self.history: List[Message] = list()
        
    def clear_history(self):
        self.history = list()
        
    def insert_history(self, message: Message):
        self.history.append(message)
        self.history = self.history[-(Config().history_length):]
        
        with open(Config().history_filepath, 'a') as f:
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
        return Config().name_translations.get(name, name)
    
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
        with open(os.path.join(
            Config().PROMPT_DIR,
            Config().PROMPT_INSTRUCTION_SUBDIR,
            Config().instruction_prompt_filename
        ), 'r') as f:
            return f.read()
        
    def get_context_descriptions(self):
        result = ""
        for context_id in self.context_metadata:
            result += "{id}:{description}\n".format(
                id=context_id,
                description=self.context_metadata[context_id].description
            )
            
        return result
            
    def get_character_prompt(self):
        with open(os.path.join(
            Config().PROMPT_DIR,
            Config().PROMPT_CHARACTER_SUBDIR,
            Config().character_prompt_filename
        ), 'r') as f:
            return f.read()
        
    def get_scene_prompt(self):
        with open(os.path.join(
            Config().PROMPT_DIR,
            Config().PROMPT_SCENE_SUBDIR,
            Config().scene_prompt_filename
        ), 'r') as f:
            return f.read()
    
    def get_sys_prompt(self):
        return "{instructions}\n{contexts}\n### Character ###\n{character}\n### Scene ###\n{scene}".format(
            instructions = self.get_instructions_prompt(),
            contexts = self.get_context_descriptions(),
            character = self.get_character_prompt(),
            scene = self.get_scene_prompt(),
        )

    def get_user_prompt(self):
        prompt = ""
        
        for message in self.history:
            message_line = message.to_line()
            prompt += "\n{}".format(message_line)
            
        return prompt
