'''
File of inputted file is to be formatted as jsonl.
Refer to dataset-template.jsonl in root for example.
'''

import argparse
import os
import json

args = argparse.ArgumentParser()
args.add_argument('--in_file', type=str, required=True, help='File to convert. Refer to comment at top of code for description of format.')
args.add_argument('--out_file', type=str, required=True, help='File to write to.')
args.add_argument('--prompt_file', type=str, required=True, help='File with prompt going to be used with AI.')
args = args.parse_args()

assert(os.path.isfile(args.in_file) and os.path.splitext(args.in_file)[1] == '.jsonl')

prompt = ""
with open(args.prompt_file, 'r') as f:
    prompt = f.read()

with open(args.in_file, 'rb') as f_in:
    with open(args.out_file, 'w') as f_out:
        while True:
            next_convo = f_in.readline()
            if next_convo is None or next_convo == b'':
                break
            # print(f"Processing string: {next_convo}") # debug
            msg_obj = json.loads(next_convo)
            if len(msg_obj["messages"]) < 2:
                continue
            msg_history = []
            msg_history.append(msg_obj["messages"].pop(0))
            while len(msg_obj["messages"]) > 0:
                msg_history.append(msg_obj["messages"].pop(0))
                if msg_history[-1]['role'] == 'assistant':
                    script = ""
                    for msg in msg_history[:-2]:
                        script += f"\n[{'friend' if msg['role'] == 'user' else 'J.A.I.son'}]: {msg['content']}"
                    new_msg_obj = {
                        "messages": [
                            {
                                "role": 'system',
                                "content": prompt + script
                            },
                            {
                                "role": 'user',
                                "name": 'friend',
                                "content": msg_history[-2]['content']
                            },
                            {
                                "role": 'assistant',
                                "content": msg_history[-1]['content']
                            }
                        ]
                    }
                    # print(f"Saving {next_convo}")
                    f_out.write(json.dumps(new_msg_obj)+'\n')

            
