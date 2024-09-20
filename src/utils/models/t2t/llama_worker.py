from .base_worker import BaseT2TAIWorker
from unsloth import FastLanguageModel

'''
Class implementing interface for locally-ran AI T2T models using unsloth.
NOTE: YOU MUST HAVE THE MODEL ON IN YOUR PROJECT (LoRa adapters is enough)

"model" name will either be an existing default, or a finetuned version using 
the name you specified during creation. For example, we want to use the 
"adapter_mode.safetensors" representing our model, found in "<project root>/models/lora_model/" 
directory. Therefore we would pass "models/lora_model" as our "model" in runtime.
'''
class LlamaAIWorker(BaseT2TAIWorker):
    def __init__(self, prompt, model="lora_model", **kwargs):
        super().__init__(prompt, **kwargs)
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name = model, # YOUR MODEL YOU USED FOR TRAINING
            max_seq_length = 2048,
            dtype = None,
            load_in_4bit = True
        )
        FastLanguageModel.for_inference(self.model)

    def get_response(self, prompt: str, msg: str):
        messages=[
            { "role": "system", "content": prompt},
            { "role": "user", "content": msg }
        ]

        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize = True,
            add_generation_prompt = True,
            return_tensors = "pt",
        ).to("cuda")
        
        output = self.model.generate(input_ids = inputs, max_new_tokens = 64, use_cache = True)
        output = self.tokenizer.batch_decode(output)[0].split('<|start_header_id|>assistant<|end_header_id|>\n\n')[1]
        output = output.removesuffix('<|eot_id|>')

        return output