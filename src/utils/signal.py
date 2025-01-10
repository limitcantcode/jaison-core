import signal
import os
import psutil
from utils.logging import create_sys_logger

logger = create_sys_logger()

class GracefulKiller:
  kill_now = False
  def __init__(self, jaison):
    self.jaison = jaison
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, signum, frame):
    logger.info("Gracefully shutting down...")
    curr_process = psutil.Process(os.getpid())
    for child in curr_process.children(recursive=True):
      child.kill()
    self.jaison.cleanup()
    curr_process.kill()