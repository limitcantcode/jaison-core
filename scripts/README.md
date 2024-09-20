# Training Scripts
The scripts found in this directory are aimed to help build datasets as shown in the video as well as finetune models, whether it be OpenAI models or local models ran using unsloth.

**Due to size restrictions and OpenAI's limitations, I won't be sharing any of my models or datasets in this repo**

(You can still make them using the scripts here and I show everything in my 2nd video)

## Datasets
Though I won't be sharing or uploading the exact datasets I used to train the models I show, you can still use the scripts here to make similar ones.

Scripts for making and formatting datasets are prefixed `ds_`. They will generally be following [OpenAI's format](https://platform.openai.com/docs/guides/fine-tuning/preparing-your-dataset)

### `ds_discord-data.py`
This script is converts the [discord-data dataset](https://www.kaggle.com/datasets/jef1056/discord-data) into a `jsonl` formatted dataset. It will be a single turn conversation containing a system prompt, a script as user input, and the expected assistant output following a format similar to `dataset-template.jsonl` or the one found on OpenAI's website.

Parameters:

- dir: Path to directory from downloaded discord-data dataset containing the `.txt` files you want to convert.
- out_file: Filepath to output `.jsonl` file.
- prompt_file: Filepath to generic prompt file similar to `<root>/prompts/datasets/ft_generic_prompt.txt`. At least one `{}` should be included to inject a name during runtime.
- script_len: OPTIONAL. Cap on how many messages can appear in the script. Defaults to 10.

### `ds_multi-to-single.py`
This script takes a [multi-turn conversation](https://platform.openai.com/docs/guides/fine-tuning/multi-turn-chat-examples) (like the one found in `dataset-template.jsonl`) and turns it into a single-turn, script format. It will add a system prompt to the conversation, and if the assistant speaks multiple times, the script will generate a new conversation for everytime the assistant speaks with all the messages in the history before then (will skip generation if a script is not long enough).

Parameters:

- in_file: Filepath to input `.jsonl` file
- out_file: Filepath to output `.jsonl` file
- prompt_file: Filepath to plaintext prompt

### `validate_jsonl_format.py`
This file is used to check for errors and such in your `.jsonl` files. It will also give you information about number of tokens and expected cost to train on OpenAI servers.

Parameters:

- file: Filepath to `.jsonl` to validate


## Fine-tuning
### `ft_openai.py`
This script is mainly an example of how to fine-tune OpenAI models programmatically. **If you are not automating the process, I would highly suggest using their [web-interface](https://platform.openai.com/finetune) instead.** This creates a fine-tuned version of any GPT model you choose, and can be used in the bot by using the checkpoint name (`ft:gpt-4o-mini-2024-07-18:lcc:kaggle-discord:A9KCPdty` for example) as the model in the parameters.

Unfortunately, as of writing this, we aren't able to share fine-tuned models with each other, so I can give you mine to play around with.

Parameters:

- train_file: `.jsonl` filepath to use for training.
- test_file: `.jsonl` filepath to use for testing.
- model: Name of model to start from. Can be one of your own checkpoints or a base model such as `gpt-40-mini-2024-07-18`.
- name: OPTIONAL. Name to give your model. Will be added into you checkpoint name.

### `ft_local.py`
**IF YOU GO THIS ROUTE, PLEASE USE LINUX OR WSL 2 TO AVOID DEPENDENCY ISSUES**

**YOU WILL NEED AN NVIDIA GPU WITH DRIVERS THAT SUPPORT CUDA**

If you can't do either of these, it will be cheaper, usable, and far less mind-rottening to use OpenAI.

This script uses [unsloth](https://unsloth.ai/) to train their models. Unsloth is also used by the bot to run local models on your machine.

I will also not be uploading models due to size restrictions on Github. But when making your own models, I would suggest prefixing the name with `model/` so it will save to the `models` directory. For example, to use or save to the model save in `<root>/models/lora_model`, you would simply use `models/lora_model` as the name.

Parameters:

- train_file: Filepath to `.jsonl` dataset to use for fine-tuning
- base_model: Name of model to start training from. Can be one of [Unsloth's conversational AI's](https://colab.research.google.com/drive/1Ys44kVvmeZtnICzWz0xgpRnrIOjZAuxp) or a local model like `models/lora_model`.
- model_name: Name of your model, like `models/lora_model`. What you name it will be where it's saved (directory and all).