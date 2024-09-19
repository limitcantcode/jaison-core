from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
import argparse

args = argparse.ArgumentParser()
args.add_argument('--train_file', type=str, required=True)
args.add_argument('--test_file', type=str, required=True)
args.add_argument('--model', type=str, required=True)
args = args.parse_args()

client = OpenAI()

train_file = client.files.create(
  file=open(args.train_file, "rb"),
  purpose="fine-tune"
)
test_file = client.files.create(
  file=open(args.test_file, "rb"),
  purpose="fine-tune"
)

client.fine_tuning.jobs.create(
  training_file=train_file.id,
  validation_file=test_file.id,
  model=args.model,
  suffix='jaison',
  seed=123
)