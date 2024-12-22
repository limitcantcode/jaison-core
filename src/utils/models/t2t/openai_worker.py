'''
Class implementing interface for AI T2T models running on OpenAI servers.

"model" will be one of OpenAI's models such as 'gpt-3.5-turbo' or a version
you've fine-tuned yourself (it will have a name like 'ft:gpt-4o-mini-2024-07-18:lcc:jaison:A92WIYvZ').
Please ensure you have your openai token in your ".env" as specified in the ".env-template"
'''
from openai import OpenAI
from .base_worker import BaseT2TAIModel
from utils.logging import create_sys_logger
logger = create_sys_logger()

class OpenAIModel(BaseT2TAIModel):
    def __init__(self, config):
        super().__init__(config)
        self.client = OpenAI()

    def get_response(self, sys_prompt, user_prompt):
        messages=[
            { "role": "system", "content": sys_prompt },
            { "role": "user", "content": user_prompt }
        ]

        logger.debug(f"Sending messages: {messages}")
        chat_completion = self.client.chat.completions.create(
            messages=messages,
            model=self.config.t2t_model,
        )

        logger.debug(f"Got results: {chat_completion}")

        if len(chat_completion.choices) == 0:
            raise Exception("No response")

        return chat_completion.choices[0].message.content