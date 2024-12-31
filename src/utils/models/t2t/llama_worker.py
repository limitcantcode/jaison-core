from .base_worker import BaseT2TAIModel
from unsloth import FastLanguageModel
from utils.logging import create_sys_logger
logger = create_sys_logger()

'''
Class implementing interface for locally-ran AI T2T models using unsloth.
NOTE: YOU MUST HAVE THE MODEL ON IN YOUR PROJECT (LoRa adapters is enough)

"model" name will either be an existing default, or a finetuned version using 
the name you specified during creation. For example, we want to use the 
"adapter_mode.safetensors" representing our model, found in "<project root>/models/lora_model/" 
directory. Therefore we would pass "models/lora_model" as our "model" in runtime.
'''
class LlamaAIModel(BaseT2TAIModel):
    def __init__(self, jaison):
        super().__init__(jaison)
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name = self.jaison.config.t2t_model,
            max_seq_length = 2048,
            dtype = None,
            load_in_4bit = True
        )
        FastLanguageModel.for_inference(self.model)

    def get_response(self, sys_prompt, user_prompt):
        messages=[
            { "role": "system", "content": sys_prompt},
            { "role": "user", "content": user_prompt }
        ]

        logger.debug(f"Sending messages: {messages}")
        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize = True,
            add_generation_prompt = True,
            return_tensors = "pt",
        ).to("cuda")
        
        output = self.model.generate(input_ids = inputs, max_new_tokens = 64, use_cache = True)
        output = self.tokenizer.batch_decode(output)[0].split('<|start_header_id|>assistant<|end_header_id|>\n\n')[1]
        output = output.removesuffix('<|eot_id|>')

        logger.debug(f"Got output after parsing: {output}")
        return output