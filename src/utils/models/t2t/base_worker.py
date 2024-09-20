
'''
This class is the base class for all T2T AI models used by the bot to generate responses.
Primary usage is to call the main function, that is BaseT2TAIWorker(new_msg, author) or whatever your new class is called.
This class isn't to be used as is, but rather implemeted by other classes such as the existing OpenAIWorker.
'''

class BaseT2TAIWorker():
    def __init__(self, prompt, name='J.A.I.son', **kwargs):
        self.prompt = prompt # prompt as it appears in the prompt file
        self.name = name # Character name associated with the AI
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
        self._update_history(new_msg, author)
        user_in = self._build_script()
        if user_in is None or len(user_in) == 1:
            raise EmptyScriptException()
        
        try:
            response = self.get_response(self.prompt, user_in)
        except Exception as err:
            print("Tell Limit there is a problem with my AI")
            print(err)
            response = 'There is a problem with my AI...'
        
        self._update_history(response, self.name )
        return response
        
    '''
    To be implemented. Functionality for interfacing with AI T2T model.

    Parameters:
    - request: Message to be sent as a user to the model. This is by default the script of the dialogue.
    Returns: (str) AI's generated response without any template
    '''
    def get_response(self, request: str):
        raise NotImplementedError
    
    # Updates the msg_history attribute with the given new_msg from author as default
    def _update_history(self, new_msg: str, author: str):
        self.msg_history.append({
            "author": author,
            "message": new_msg if new_msg is not None else ''
        })
        if len(self.msg_history) > 10:
            self.msg_history.pop(0)

    # Generates script from current msg_history to be used as request to model by default
    def _build_script(self):
        script = ""
        for msg_obj in self.msg_history:
            script += f"\n[{msg_obj['author']}]: {msg_obj['message']}"

        return script

class EmptyScriptException(Exception):
    pass
