'''
Class implementing interface for AI T2T models running on OpenAI servers.

"model" will be one of OpenAI's models such as 'gpt-3.5-turbo' or a version
you've fine-tuned yourself (it will have a name like 'ft:gpt-4o-mini-2024-07-18:lcc:jaison:A92WIYvZ').
Please ensure you have your openai token in your ".env" as specified in the ".env-template"
'''
from openai import OpenAI
from .base_worker import BaseT2TAIWorker
from config import config
from utils.logging import system_logger

class OpenAIWorker(BaseT2TAIWorker):
    def __init__(self, t2t_model='gpt-3.5-turbo', **kwargs):
        super().__init__(**kwargs)
        self.client = OpenAI()
        self.model = config['t2t_model']

        system_logger.debug(f"OpenAIWorker loaded with model: {config['t2t_model']}")


    def get_response(self, prompt: str, msg: str):
        system_logger.debug(f"OpenAIWorker called with prompt: \"{prompt}\" and message: \"{msg}\"")
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": msg,
                }
            ],
            model=self.model,
        )

        system_logger.debug(f"OpenAIWorker finished with raw output: {chat_completion}")

        if len(chat_completion.choices) == 0:
            raise Exception("No response")
        output = chat_completion.choices[0].message.content
        system_logger.debug(f"OpenAIWorker responding with final output: {output}")
        
        return output