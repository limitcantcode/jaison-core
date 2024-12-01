'''
This class is the base class for all T2T AI models used by the bot to generate responses.
Primary usage is to call the main function, that is BaseT2TAIWorker(new_msg, author) or whatever your new class is called.
This class isn't to be used as is, but rather implemeted by other classes such as the existing OpenAIWorker.
'''

from config import config
from utils.logging import system_logger, save_dialogue, save_response

class BaseT2TAIWorker():
    def __init__(self, **kwargs):
        with open(config['prompt_filepath'], 'r') as f:
            self.prompt = f.read() # prompt as it appears in the prompt file
        self.name = config['character_name'] # Character name associated with the AI
        self.msg_history = [] # Recent chat history. Each message is of format { "author": <speaker name string>, "message": <message string> }


    '''
    Main function for interacting with AI T2T model.
    Called like BaseT2TAIWorker(new_msg, author)

    Parameters:
    - new_msg: New message that was sent into chat triggering response
    - author: Name of person who sent that message
    Returns: (str) AI's generated response without any template
    '''
    def __call__(self, new_msg: str, author: str):
        self._add_history(new_msg, author)
        save_dialogue(new_msg, author)
        user_in = self._build_script()
        if user_in is None or len(user_in) == 1:
            raise EmptyScriptException()
        
        try:
            response = self.get_response(self.prompt, user_in)
        except Exception as err:
            system_logger.error(f"There is a problem with my AI: {err}")
            response = 'There is a problem with my AI...'
        
        save_dialogue(response, self.name)
        save_response(self.prompt, user_in, response)
        self._add_history(response, self.name)
        self._prune_history(30)

        return response
        
    '''
    To be implemented. Functionality for interfacing with AI T2T model.

    Parameters:
    - request: Message to be sent as a user to the model. This is by default the script of the dialogue.
    Returns: (str) AI's generated response without any template
    '''
    def get_response(self, request: str):
        raise NotImplementedError
    
    # Adds to the msg_history attribute with the given new_msg from author as default
    def _add_history(self, new_msg: str, author: str):
        self.msg_history.append({
            "author": author,
            "message": new_msg if new_msg is not None else ''
        })

    # Retains count most recent messages
    def _prune_history(self, count):
        if len(self.msg_history) > count:
            self.msg_history[-count:]

    # Generates script from current msg_history to be used as request to model by default
    def _build_script(self):
        script = ""
        for msg_obj in self.msg_history:
            script += f"\n[{msg_obj['author']}]: {msg_obj['message']}"

        return script

class EmptyScriptException(Exception):
    pass
