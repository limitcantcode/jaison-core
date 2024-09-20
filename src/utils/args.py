import argparse

args = argparse.ArgumentParser()
args.add_argument('--t2t_ai', choices=['openai','local'], default='openai', type=str, help='Which T2T AI implementation to use.')
args.add_argument('--prompt_file', type=str, required=True, help='Filepath to prompt for the T2T AI')
args.add_argument('--model', type=str, default='gpt-3.5-turbo', help='Name of openai or local unsloth model to use.')
args.add_argument('--name', type=str, default='J.A.I.son', help='Name of your bot and how it will be addressed.')

args = args.parse_args()