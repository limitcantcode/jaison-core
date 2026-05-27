from utils.logging import setup_logger

setup_logger()

from dotenv import load_dotenv  # noqa: E402

from utils.args import args  # noqa: E402

load_dotenv(dotenv_path=args.env)

import os  # noqa: E402
from pathlib import Path  # noqa: E402

# Patch path for local binaries
project_root = Path(__file__).resolve().parents[1]
bin_dir = Path(__file__).resolve().parents[1] / "bin"
if bin_dir.is_dir():
    os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"

import asyncio  # noqa: E402

from utils.server import start_web_server  # noqa: E402

asyncio.run(start_web_server())
