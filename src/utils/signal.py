import signal
import os
import psutil
import sys
from utils.logging import create_sys_logger

logger = create_sys_logger()

class GracefulKiller:
  kill_now = False
  def __init__(self):
    self.to_cleanup = []
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def add_cleanup(self, o):
    self.to_cleanup.append(o)

  def exit_gracefully(self, signum, frame):
    logger.info("Gracefully shutting down...")
    for to_clean in self.to_cleanup:
      to_clean.cleanup()
    curr_process = psutil.Process(os.getpid())
    for child in curr_process.children(recursive=True):
      child.kill()
    sys.exit(0)