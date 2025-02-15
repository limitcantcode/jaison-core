import os
import json
import asyncio
from utils.config import Configuration
from utils.logging import save_dialogue, save_response
from utils.time import get_current_time

class Prompter():
    def __init__(self):
        self.DISABLED_CONTEXT_MESSAGE = "This context isn't provided."
        self.NO_RESPONSE = "<no response>"
        self.SELF_IDENTIFIER = "You"
        self.MAIN_CONVERSATION_HEADER = "Main Conversation"
        self.REQUEST_HEADER = "Request"
        self.DEFAULT_CONVO_HISTORY_LENGTH = 5

        self.config = Configuration()

        self.CONTEXT_INSTRUCTIONS_BASE = '''
You are taking the next turn in a given conversation. The user will give the conversation along with all the context. Of the contexts given, you must always follow the instructions in requests given under the header "{request_header}". The main conversation will be given under the header "{main_conversation_header}". The conversation will be formatted as a script where each line starts with time the line was spoken between [] followed the speaker's name between [] or the special <{self_identifier}> to represent what you said before. For example:

{main_conversation_header}
[2024-12-09 20:51:46,339][Jason]: Hey there!
[2024-12-09 20:51:50,459]<{self_identifier}>: Oh hi!
[2024-12-09 20:51:52,354][Nosaj]: Hey

In the above example, "Jason" said "Hey there!". Then you said "Oh hi!". Finally "Nosaj" said "Hey".
You are to only respond with your own response to the current conversation, such as "Oh hi!". If you think you should not say anything, say "{no_response_token}". For example:

{main_conversation_header}
[2024-12-09 20:51:46,339][Jason]: Hey there!
[2024-12-09 20:51:50,459]<{self_identifier}>: Oh hi!
[2024-12-09 20:51:52,354][Jason]: I think I...

Here, you should respond with {no_response_token}.

{optional_context_descriptions}Finally, you shall never break from the character described in the remainder of this system prompt:

{character_description}
'''
        self.name_translations = {}
        self.convo_history = [] # will contain {time: str, name: str, message: str}
        self.special_request = None
        self.optional_contexts = {} # <context id>: {name, description, contents}

    def _header_builder(self, name):
        return f"=== {name} ==="
    
    def _get_character_description(self):
        with open(os.path.join(
            self.config.prompt_dir,
            self.config.prompt_current_file or self.config.prompt_default_file
        ), 'r') as f:
            return f.read().format(**self.config.prompt_params)

    def _translate_name(self, name: str):
        return self.name_translations.get(name, name)
    
    def reload_name_translations(self):
        with open(os.path.join(self.config.name_translation_dir, self.config.name_translation_file), 'r') as f:
            self.name_translations = json.load(f)

    def msg_o_to_line(self, o):
        time = "[{}]".format(o['time'])
        name = "<{}>".format(self.SELF_IDENTIFIER) if o['name'] == self.SELF_IDENTIFIER else "[{}]".format(self._translate_name(o['name']))
        message = o['message']

        return f"{time} {name}: {message}\n"

    def add_optional_context(self, context_id: str, context_name: str, context_description: str = None, initial_contents: str = None):
        if context_id is None or context_name is None: raise Exception("New context must have context_id and context_name")
        self.optional_contexts[context_id] = {
            "name": context_name,
            "description": context_description,
            "contents": initial_contents
        }

    def remove_optional_context(self, context_id: str):
        del self.optional_contexts[context_id]

    def update_optional_context(self, context_id: str, context_name: str = None, contents: str = None):
        if context_id not in self.optional_contexts:
            self.add_optional_context(context_id,context_name,initial_contents=contents)
            return
        if context_name: self.optional_contexts[context_id]['name'] = context_name
        if contents: self.optional_contexts[context_id]['contents'] = contents

    def add_history(self, time, name, message):
        new_dialog = {
            "time": time,
            "name": name,
            "message": message
        }
        self.convo_history.append(new_dialog)
        while len(self.convo_history) > self.config.convo_retention_length:
            self.convo_history.pop(0)
        save_dialogue(self.msg_o_to_line(new_dialog))

    def add_special_request(self, message):
        if self.special_request is None: self.special_request = ""
        self.special_request += message + "\n"
        save_dialogue(self.msg_o_to_line({
            "time": get_current_time(),
            "name": "Added Request",
            "message": message
        }))

    def get_sys_prompt(self):
        optional_context_descriptions = ""
        if len(self.optional_contexts) > 0:
            optional_context_descriptions = "You will receive additional context under their own headers. Here is a description of each:\n\n"
            for context_id in self.optional_contexts:
                details = self.optional_contexts[context_id]
                header = self._header_builder(details['name'])
                description = self._header_builder(details['description'])
                optional_context_descriptions += f'''Context with header "{header}": \n{description}\n\n'''

        return self.CONTEXT_INSTRUCTIONS_BASE.format(
            request_header=self._header_builder(self.REQUEST_HEADER),
            main_conversation_header=self._header_builder(self.MAIN_CONVERSATION_HEADER),
            no_response_token=self.NO_RESPONSE,
            self_identifier=self.SELF_IDENTIFIER,
            optional_context_descriptions=optional_context_descriptions,
            character_description=self._get_character_description()
        )

    def get_user_prompt(self, preserve_temp = False):
        full_optional_context = ""
        for context_id in self.optional_contexts:
            details = self.optional_contexts[context_id]
            full_optional_context += f'''=== {details['name']} ===\n{details['contents']}\n\n'''

        special_request_context = self.special_request or "There is no request."

        main_conversation_context = ""
        self.reload_name_translations()
        for o in self.convo_history:
            main_conversation_context += self.msg_o_to_line(o)

        user_prompt = '''
{optional_contexts}{main_conversation_header}
{main_conversation_context}

{request_header}
{request_context}

'''.format(
main_conversation_header=self._header_builder(self.MAIN_CONVERSATION_HEADER),
main_conversation_context=main_conversation_context,
request_header=self._header_builder(self.REQUEST_HEADER),
request_context=special_request_context,
optional_contexts=full_optional_context
)
        if not preserve_temp:
            self.special_request = None

        return user_prompt