from .contexts import ContextBuilder
from .instructions import InstructionBuilder

class Prompter():
    def __init__(self, jaison):
        self.contexts = ContextBuilder(jaison)
        self.instructions = InstructionBuilder(jaison)

        # Pass up constants to be shared
        self.NO_RESPONSE = self.contexts.NO_RESPONSE
        self.SELF_IDENTIFIER = self.contexts.SELF_IDENTIFIER

    def get_sys_prompt(self):
        return "{}\n{}".format(
            self.contexts.get_context_instructions(),
            self.instructions.get_instructions()
        )

    def get_user_prompt(self):
        return self.contexts.get_context_final()

    def save_sys_prompt(self, prompt, filepath):
        self.instructions.update_instructions(prompt, filepath)

    def add_history(self, time, name, message):
        self.contexts.add_history(time, name, message)
    
    def rollback_history(self):
        self.contexts.rollback_history()

    def commit_history(self):
        self.contexts.commit_history()

    def get_uncommited_history(self):
        return self.contexts.get_uncommited_history()

    def convert_msg_o_to_line(self, o):
        return self.contexts.msg_o_to_line(o)

    def inject_one_time_request(self, message):
        return self.contexts.set_one_time_request_context(message)