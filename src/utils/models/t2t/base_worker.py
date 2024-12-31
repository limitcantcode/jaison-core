'''
This class is the base class for all T2T AI models used by the bot to generate responses.
Primary usage is to call the main function, that is BaseT2TAIModel(new_msg, author) or whatever your new class is called.
This class isn't to be used as is, but rather implemeted by other classes such as the existing OpenAIModel.
'''

from .prompter import Prompter
from .filter import ResponseFilter
from utils.time import get_current_time
from utils.logging import create_sys_logger, save_dialogue, save_response
logger = create_sys_logger()

class BaseT2TAIModel():
    DEFAULT_RESPONSE_MSG = 'There is a problem with my AI...'
    def __init__(self, jaison):
        self.jaison= jaison
        self.prompter = Prompter(jaison)
        self.filter = ResponseFilter()

    '''
    Main function for interacting with AI T2T model.
    Called like BaseT2TAIModel(new_msg, author)

    Parameters:
    - time: String time when message started being said
    - name: Literal name of person who sent that message
    - message: New message to add to conversation
    Returns: (str) AI's generated response without any template
    '''
    def __call__(self, time, name, message):
        self.prompter.add_history(time, name, message)

        try:
            sys_prompt = self.prompter.get_sys_prompt()
            user_prompt = self.prompter.get_user_prompt()

            response = self.get_response(sys_prompt, user_prompt)
            response = response if response != self.prompter.NO_RESPONSE else None
        except Exception as err:
            logger.error(f"Failed to get response: {err}")
            response = self.DEFAULT_RESPONSE_MSG

        if response:
            try:
                response = self.filter(response) # Apply filtering
                self.prompter.add_history(
                    get_current_time(),
                    self.prompter.SELF_IDENTIFIER,
                    response
                )
                uncommited_messages = self.prompter.get_uncommited_history()
                for msg_o in uncommited_messages:
                    save_dialogue(self.prompter.convert_msg_o_to_line(msg_o))
                self.prompter.commit_history()
                save_response(sys_prompt, user_prompt, response)
            except Exception as err:
                logger.error(f"Failed to save conversation: {err}")
                return self.DEFAULT_RESPONSE_MSG
        else:
            try:
                self.prompter.rollback_history()
            except Exception as err:
                logger.error(f"Failed to rollback conversation: {err}")
                return self.DEFAULT_RESPONSE_MSG

        return response
        
    '''
    To be implemented. Functionality for interfacing with AI T2T model.

    Parameters:
    - sys_prompt: System message, ideally the generic prompt
    - user_prompt: User input, ideally the contexts
    Returns: (str) AI's generated response
    '''
    def get_response(self, sys_prompt, user_prompt):
        raise NotImplementedError

    def inject_one_time_request(self, message):
        return self.prompter.inject_one_time_request(message)