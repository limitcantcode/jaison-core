'''
Example script for fine-tuning OpenAI models programmatically.
Full tutorial on OpenAI's docs here: https://platform.openai.com/docs/guides/fine-tuning
'''

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
import argparse

# Parse command line arguments
args = argparse.ArgumentParser()
args.add_argument('--train_file', type=str, required=True)
args.add_argument('--test_file', type=str, required=True)
args.add_argument('--model', type=str, required=True)
args.add_argument('--name', type=str, default='J.A.I.son')
args = args.parse_args()

client = OpenAI()

# Upload dataset files for training and validation
train_file = client.files.create(
  file=open(args.train_file, "rb"),
  purpose="fine-tune"
)
test_file = client.files.create(
  file=open(args.test_file, "rb"),
  purpose="fine-tune"
)

# Start a finetuning job. You can see jobs here: https://platform.openai.com/finetune
client.fine_tuning.jobs.create(
  training_file=train_file.id,
  validation_file=test_file.id,
  model=args.model,
  suffix=args.name,
  seed=123
)