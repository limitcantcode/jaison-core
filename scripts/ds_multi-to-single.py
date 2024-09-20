'''
This script takes a valid jsonl file (in OpenAI's format)
that contains multi-turn conversations, and converts it into
a single-turn conversation where the user input to the model
is a script of the multi-turn conversation.

File of inputted file is to be formatted as jsonl.
Refer to dataset-template.jsonl in this dir for example.
'''

import argparse
import os
import json

# Parse command line arguments
args = argparse.ArgumentParser()
args.add_argument('--in_file', type=str, required=True, help='File to convert. Refer to comment at top of code for description of format.')
args.add_argument('--out_file', type=str, required=True, help='File to write to.')
args.add_argument('--prompt_file', type=str, required=True, help='File with prompt going to be used with AI.')
args = args.parse_args()

# ensure the input file is a jsonl file
assert(os.path.isfile(args.in_file) and os.path.splitext(args.in_file)[1] == '.jsonl')

# Get prompt from specified file
PROMPT = ""
with open(args.prompt_file, 'r') as f:
    PROMPT = f.read()

# Read from input jsonl
with open(args.in_file, 'rb') as f_in:
    # Prepare to write to output jsonl
    with open(args.out_file, 'w') as f_out:
        # Take one multi-turn convo at a time
        while True:
            next_convo = f_in.readline()
            if next_convo is None or next_convo == b'':
                break
            msg_obj = json.loads(next_convo)

            # Ignore conversations that are too short
            if len(msg_obj["messages"]) < 2:
                continue

            # Track conversation history
            msg_history = []
            msg_history.append(msg_obj["messages"].pop(0))
            while len(msg_obj["messages"]) > 0:
                msg_history.append(msg_obj["messages"].pop(0))

                # When most recent message in conversation is the model's output,
                #   generate a new conversation instance
                if msg_history[-1]['role'] == 'assistant':
                    # Generate script from current history
                    script = ""
                    for msg in msg_history[:-1]:
                        script += f"\n[{'friend' if msg['role'] == 'user' else 'J.A.I.son'}]: {msg['content']}"
                    # Create new single-turn instance
                    new_msg_obj = {
                        "messages": [
                            {
                                "role": 'system',
                                "content": PROMPT
                            },
                            {
                                "role": 'user',
                                "content": script
                            },
                            {
                                "role": 'assistant',
                                "content": msg_history[-1]['content']
                            }
                        ]
                    }
                    # Save convo instance to output file
                    f_out.write(json.dumps(new_msg_obj)+'\n')

            
