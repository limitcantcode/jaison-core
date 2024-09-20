'''
Class implementing interface for AI T2T models running on OpenAI servers.

"model" will be one of OpenAI's models such as 'gpt-3.5-turbo' or a version
you've fine-tuned yourself (it will have a name like 'ft:gpt-4o-mini-2024-07-18:lcc:jaison:A92WIYvZ').
Please ensure you have your openai token in your ".env" as specified in the ".env-template"
'''
from openai import OpenAI
from .base_worker import BaseT2TAIWorker

class OpenAIWorker(BaseT2TAIWorker):
    def __init__(self, prompt, model='gpt-3.5-turbo', **kwargs):
        super().__init__(prompt, **kwargs)
        self.client = OpenAI()
        self.model = model

    def get_response(self, prompt: str, msg: str):
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
        
        if len(chat_completion.choices) == 0:
            raise Exception("No response")

        return chat_completion.choices[0].message.content

# class old_OpenAIWorker:
#     client = OpenAI()

#     def get_response(self, query_str: str) -> str:
#         try:
#             chat_completion = self.client.chat.completions.create(
#                 messages=[
#                     {
#                         "role": "user",
#                         "content": query_str,
#                     }
#                 ],
#                 model="gpt-3.5-turbo",
#             )

#             if len(chat_completion.choices) == 0:
#                 raise Exception("No response")
#         except Exception as err:
#             print("Tell Limit there is a problem with my AI")
#             print(err)
#             raise err

#         return chat_completion.choices[0].message.content

#     def get_response_stream_generator(self, query_str: str):
#         # Example usage of get_response_stream_generator
#         # result = ""
#         # for content in get_response_stream_generator():
#         #     result += content
#         #     print(result)
#         #     # feed into tts

#         # print(f"Finished with message: {result}")

#         stream = self.client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[{"role": "user", "content": query_str}],
#             stream=True,
#         )
#         for chunk in stream:
#             yield chunk.choices[0].delta.content or ""