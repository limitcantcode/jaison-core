from utils.logging import setup_logger

setup_logger()

from utils.args import args
from dotenv import load_dotenv

load_dotenv(dotenv_path=args.env)

import os
from pathlib import Path

# Patch path for local binaries
project_root = Path(__file__).resolve().parents[1]
bin_dir = Path(__file__).resolve().parents[1] / "bin"
if bin_dir.is_dir():
    os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"

import asyncio
from utils.server import start_web_server

asyncio.run(start_web_server())
