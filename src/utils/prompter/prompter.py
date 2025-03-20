
import os
from typing import AsyncGenerator
from utils.helpers.time import timestamp_to_str
from utils.helpers.singleton import Singleton
from .error import UnknownContext, InvalidContext
from utils.config import Config

class Prompter(metaclass=Singleton):
    def __init__(self):
        self.DISABLED_CONTEXT_MESSAGE = "This context isn't provided."
        self.SELF_IDENTIFIER = "You"
        self.MAIN_CONVERSATION_HEADER = "Main Conversation"
        self.REQUEST_HEADER = "Request"

        self.CONTEXT_INSTRUCTIONS_BASE = '''
You are taking the next turn in a given conversation. The user will give the conversation along with all the context. Of the contexts given, you must always follow the instructions in requests given under the header "{request_header}". The main conversation will be given under the header "{main_conversation_header}". The conversation will be formatted as a script where each line starts with time the line was spoken between [] followed the speaker's name between [] or the special <{self_identifier}> to represent what you said before. For example:

{main_conversation_header}
[2024-12-09 20:51:46,339][Jason]: Hey there!
[2024-12-09 20:51:50,459]<{self_identifier}>: Oh hi!
[2024-12-09 20:51:52,354][Nosaj]: Hey

In the above example, "Jason" said "Hey there!". Then you said "Oh hi!". Finally "Nosaj" said "Hey".
You are to only respond with your own response to the current conversation, such as "Oh hi!".

{custom_context_descriptions}Finally, you shall never break from the character described in the remainder of this system prompt:

{character_description}
'''

        self.convo_history = [] # will contain {time: str, name: str, message: str}
        self.request = None
        self.custom_contexts = {} # <context id>: {name, description, contents}

    def _header_builder(self, name):
        return f"=== {name} ==="
    
    def _get_character_description(self):
        with open(os.path.join(Config().PROMPT_DIR, Config().prompt_filename), 'r') as f:
            return f.read()

    def _translate_name(self, name: str):
        return Config().prompt_name_translations.get(name, name)

    def msg_o_to_line(self, o):
        time = "[{}]".format(o['time'])
        name = "<{}>".format(self.SELF_IDENTIFIER) if o['name'] == self.SELF_IDENTIFIER else "[{}]".format(self._translate_name(o['name']))
        message = o['message']

        return f"{time} {name}: {message}\n"

    def add_custom_context(self, context_id: str, context_name: str, context_description: str = None, initial_contents: str = None):
        if context_id is None or context_name is None: raise InvalidContext()
        self.custom_contexts[context_id] = {
            "name": context_name,
            "description": context_description,
            "contents": initial_contents
        }

    def remove_custom_context(self, context_id: str):
        del self.custom_contexts[context_id]

    def update_custom_context(self, context_id: str, contents: str):
        if context_id not in self.custom_contexts:
            raise UnknownContext(context_id)
        self.custom_contexts[context_id]['contents'] = contents

    def add_history(self, time: int, name: str, message: str):
        time_str = timestamp_to_str(time, include_ms=False)
        new_dialog = {
            "time": time_str,
            "name": name,
            "message": message
        }
        self.convo_history.append(new_dialog)
        self.convo_history = self.convo_history[-(Config().prompt_conversation_length):]
        
    async def listen_response(self, time: int, in_stream: AsyncGenerator):
        content = ''
        async for in_d in in_stream:
            content += in_d['content']
        
        self.add_history(time, self.SELF_IDENTIFIER, content)
            
    def clear_history(self):
        self.convo_history.clear()

    def add_request(self, message):
        if self.request is None: self.request = ""
        self.request += message + "\n"

    def clear_request(self):
        self.request = None

    def get_sys_prompt(self):
        custom_context_descriptions = ""
        if len(self.custom_contexts) > 0:
            custom_context_descriptions = "You will receive additional context under their own headers. Here is a description of each:\n\n"
            for context_id in self.custom_contexts:
                details = self.custom_contexts[context_id]
                header = self._header_builder(details['name'])
                description = self._header_builder(details['description'])
                custom_context_descriptions += f'''Context with header "{header}": \n{description}\n\n'''

        return self.CONTEXT_INSTRUCTIONS_BASE.format(
            request_header=self._header_builder(self.REQUEST_HEADER),
            main_conversation_header=self._header_builder(self.MAIN_CONVERSATION_HEADER),
            self_identifier=self.SELF_IDENTIFIER,
            custom_context_descriptions=custom_context_descriptions,
            character_description=self._get_character_description()
        )

    def get_user_prompt(self):
        full_custom_context = ""
        for context_id in self.custom_contexts:
            details = self.custom_contexts[context_id]
            full_custom_context += f'''=== {details['name']} ===\n{details['contents']}\n\n'''

        request_context = self.request or "There is no request."

        main_conversation_context = ""
        for o in self.convo_history:
            main_conversation_context += self.msg_o_to_line(o)

        user_prompt = '''
{custom_contexts}{main_conversation_header}
{main_conversation_context}

{request_header}
{request_context}

'''.format(
main_conversation_header=self._header_builder(self.MAIN_CONVERSATION_HEADER),
main_conversation_context=main_conversation_context,
request_header=self._header_builder(self.REQUEST_HEADER),
request_context=request_context,
custom_contexts=full_custom_context
)
        return user_prompt