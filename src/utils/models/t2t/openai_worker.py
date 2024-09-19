'''
Class responsible for handling OpenAI API interactions

OpenAIWorker Functions:
get_response(query_str): Asks ChatGPT <query_str>, disregarding previous texts, returning its best answer whole
get_response_stream_generator(query_str): Asks ChatGPT <query_str>, disregarding previous texts, returning its best answer as an iterable stream of tokens
'''
from openai import OpenAI
from .base_worker import BaseT2TAIWorker

class OpenAIWorker(BaseT2TAIWorker):
    def __init__(self, prompt, model='gpt-3.5-turbo', **kwargs):
        super().__init__(prompt, **kwargs)
        self.client = OpenAI()
        self.model = model

    def get_response(self, prompt: str, msg: str, author: str):
        print("Sending request")
        print(prompt)
        print("===========")
        print(f"[{author}]: {msg}")
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": prompt,
                    },
                    {
                        "role": "user",
                        "name": author,
                        "content": msg,
                    }
                ],
                model=self.model,
            )

            if len(chat_completion.choices) == 0:
                raise Exception("No response")
        except Exception as err:
            print("Tell Limit there is a problem with my AI")
            print(err)
            raise err

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