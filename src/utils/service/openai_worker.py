'''
Class responsible for handling OpenAI API interactions

OpenAIWorker Functions:
get_response(query_str): Asks ChatGPT <query_str>, disregarding previous texts, returning its best answer whole
get_response_stream_generator(query_str): Asks ChatGPT <query_str>, disregarding previous texts, returning its best answer as an iterable stream of tokens
'''
from openai import OpenAI

class OpenAIWorker:
    client = OpenAI()

    def get_response(self, query_str: str) -> str:
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": query_str,
                    }
                ],
                model="gpt-3.5-turbo",
            )

            if len(chat_completion.choices) == 0:
                raise Exception("No response")
        except Exception as err:
            print("Tell Limit there is a problem with my AI")
            print(err)
            raise err

        return chat_completion.choices[0].message.content

    def get_response_stream_generator(self, query_str: str):
        # Example usage of get_response_stream_generator
        # result = ""
        # for content in get_response_stream_generator():
        #     result += content
        #     print(result)
        #     # feed into tts

        # print(f"Finished with message: {result}")

        stream = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": query_str}],
            stream=True,
        )
        for chunk in stream:
            yield chunk.choices[0].delta.content or ""