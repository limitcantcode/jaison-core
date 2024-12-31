import os
'''
InstructionBuilder manages section in system prompt explaining what to do with the current information.
This class only handles the situation instruction as though instructing a person and not an AI.
This class does NOT build the whole system prompt. Instructions for how to read the context and how to
behave is done by the ContextBuilder.
'''
class InstructionBuilder():
    def __init__(self, jaison):
        self.jaison = jaison

    def get_instructions_raw(self):
        instruct_filepath = os.path.join(
            self.jaison.config.t2t_prompt_dir,
            self.jaison.config.t2t_current_prompt_file or self.jaison.config.t2t_default_prompt_file
        )

        with open(instruct_filepath, 'r') as f:
            instructions = f.read()

        return instructions

    def get_instructions(self):
        return self.get_instructions_raw().format(**self.jaison.config.t2t_prompt_params)
