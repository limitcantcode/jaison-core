'''
This script is for turning the 'discord-data' dataset from Kaggle (https://www.kaggle.com/datasets/jef1056/discord-data)
into a basic dataset usable for finetuning OpenAI models and local models using the scripts here.

NOTE: I won't be providing datasets (for now at least). If you want to fine-tune like I did, you will
need to download the datasets yourself and run this script.
'''

import argparse
import os
import random
import json
from tqdm import tqdm

# Parse command line arguments
args = argparse.ArgumentParser()
args.add_argument('--dir', type=str, required=True, help='Directory containing txt files from https://www.kaggle.com/datasets/jef1056/discord-data/data')
args.add_argument('--out_file', type=str, required=True, help='Filepath to output to. While be ChatGPTs jsonl format')
args.add_argument('--prompt_file', type=str, required=True, help='Filepath to plaintext prompt.')
args.add_argument('--script_len', type=int, default=10, help='number of messages to be included in the script')
args = args.parse_args()

# Check and get list of all files in dataset directory specified
assert(args.script_len >= 0)
assert(os.path.isdir(args.dir))
files = [os.path.join(args.dir, f) for f in os.listdir(args.dir) if os.path.isfile(os.path.join(args.dir, f)) and f[-4:] == '.txt']
assert(len(files) > 0)

# Check and get prompt from specified file
assert(os.path.isfile(args.prompt_file))
f_prompt = open()
PROMPT = f_prompt.read()
f_prompt.close()
assert(len(PROMPT) > 0)

# Parse a conversation instance from dataset, finding name of sender and contents of message
def parse_message_str(s: str):
    SPLIT_STR = ': '
    split_ind = s.find(SPLIT_STR)
    name = s[:split_ind]
    msg = s[split_ind+len(SPLIT_STR):]
    return {"name": name, "content": msg}

# Read each file, one at a time
f_out = open(args.out_file, 'w')
for file in tqdm(files, total=len(files), desc='[Files processed]'):
    f_in = open(file, 'r')
    # Process every conversation in the file (1 conversation per line)
    while True:
        convo = f_in.readline()
        if convo is None or convo == '':
            break
        
        # Messages in a conversation are separated by this special whitespace character before each new username
        convo = convo.split('	')
        if len(convo) < 2: # We need more than 1 message to have a proper convo
            continue
        num_msg_included = random.randint(2,args.script_len+2)
        convo = convo[:min(num_msg_included, len(convo))] # use the first x amount of messages from convo, where x is random but within number of messages included in script prompts
        messages = list(map(parse_message_str, convo))

        # Assume AI is the last speaker for training purposes
        target_msg = messages.pop(-1)

        # Generate script from remainder of messages in history
        script = ""
        for msg in messages:
            script += f"\n[{msg['name']}]: {msg['content']}"

        # Format into a conversation-format json as OpenAI specifies
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": PROMPT.format(target_msg['name'])
                },
                {
                    "role": "user",
                    "content": script
                },
                {
                    "role": "assistant",
                    "content": target_msg['content']
                }
            ]
        }
        # Add to our jsonl output file
        f_out.write(json.dumps(data)+'\n')

    f_in.close()
f_out.close()