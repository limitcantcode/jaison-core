import logging
import os
import sys
import uuid

from rich.console import Console
from rich.logging import RichHandler

from utils.args import args
from utils.helpers.time import get_current_time

START_TIME = get_current_time(include_ms=False, as_str=False)

_LOG_TIME_FORMAT = "[%Y-%m-%d %H:%M:%S]"

# Uvicorn installs its own handlers/formatters unless log_config=None; route through root.
_UVICORN_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access", "uvicorn.asgi")


def _log_filename() -> str:
    now = get_current_time(include_ms=False, as_str=False)
    short_id = uuid.uuid4().hex[:8]
    # %f is 6-digit microseconds; drop the last 3 digits for padded milliseconds.
    return f"{now.strftime('%Y-%m-%d_%H-%M-%S-%f')}_{short_id}.log"


def _configure_uvicorn_loggers() -> None:
    level = getattr(logging, args.log_level)
    for name in _UVICORN_LOGGERS:
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
        uvicorn_logger.setLevel(level)


def _create_rich_handler(console: Console, *, enable_link_path: bool = True) -> RichHandler:
    return RichHandler(
        console=console,
        rich_tracebacks=True,
        show_time=True,
        show_level=True,
        show_path=True,
        enable_link_path=enable_link_path,
        log_time_format=_LOG_TIME_FORMAT,
        markup=False,
    )


def setup_logger():
    global START_TIME

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, args.log_level))

    log_path = os.path.join(args.log_dir, _log_filename())
    log_file = open(log_path, "a", encoding="utf-8")
    file_handler = _create_rich_handler(
        Console(file=log_file, width=200, force_terminal=True, color_system="standard"),
    )
    file_handler._log_file = log_file  # keep handle open for process lifetime
    logger.addHandler(file_handler)

    if not args.silent:
        console_handler = _create_rich_handler(Console(file=sys.stdout))
        logger.addHandler(console_handler)

    _configure_uvicorn_loggers()
