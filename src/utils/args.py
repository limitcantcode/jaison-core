import argparse

args = argparse.ArgumentParser()
args.add_argument('--t2t_ai', choices=['openai','local'], default='openai', type=str, help='Which T2T AI implementation to use. One of []')
args.add_argument('--prompt_file', type=str, help='Filepath to prompt for the T2T AI')
args.add_argument('--open_model', type=str, default='gpt-3.5-turbo')

args = args.parse_args()