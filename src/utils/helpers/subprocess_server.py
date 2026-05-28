"""Helpers for operations that spawn local HTTP server binaries."""

from __future__ import annotations

import logging
import os
import platform
import socket
import subprocess

import psutil

from utils.helpers.path import portable_path


def bin_executable(name: str) -> str:
    """Path to a server binary installed under ``bin/`` by bootstrap."""
    if platform.system() == "Windows" and not name.endswith(".exe"):
        name = f"{name}.exe"
    return portable_path(os.path.join(os.getcwd(), "bin", name))


def allocate_port() -> int:
    sock = socket.socket()
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def start_shell_process(cmd: str, *, label: str) -> subprocess.Popen:
    from subprocess import DEVNULL

    logging.debug(f"Starting {label}: {cmd}")
    proc = subprocess.Popen(cmd, shell=True, stdout=DEVNULL, stderr=DEVNULL)
    logging.info(f"Started {label} (PID: {proc.pid})")
    return proc


def stop_process(proc: subprocess.Popen | None, *, label: str) -> None:
    if proc is None:
        return
    try:
        ps_process = psutil.Process(proc.pid)
        for child in ps_process.children(recursive=True):
            child.kill()
        ps_process.kill()
    except psutil.NoSuchProcess:
        pass
    logging.info(f"Stopped {label} (PID: {proc.pid})")
