import logging, os, shutil
from datetime import datetime

LOG_LEVEL      = logging.DEBUG
ROOT_LOG_DIR   = 'logs'

# Pick a timestamp for this run
cycle_ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
cycle_dir  = os.path.join(ROOT_LOG_DIR, cycle_ts)
latest_dir = os.path.join(ROOT_LOG_DIR, 'latest')

# Create the archive folder
os.makedirs(cycle_dir, exist_ok=True)

# Reset the "latest" folder
if os.path.exists(latest_dir):
    shutil.rmtree(latest_dir)
os.makedirs(latest_dir, exist_ok=True)

# Configure root logger: two file handlers + console
handlers = [
    logging.FileHandler(os.path.join(cycle_dir, 'main.log'), mode='w'),
    logging.FileHandler(os.path.join(latest_dir, 'main.log'), mode='w'),
    logging.StreamHandler(),  # writes to stdout
]
logging.basicConfig(
    level   = LOG_LEVEL,
    format  = "%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers= handlers
)

def get_logger(name: str, filename: str) -> logging.Logger:
    """
    Returns a logger that writes to:
      logs/<cycle_ts>/<filename>
      logs/latest/<filename>
      AND to stdout.
    """
    log = logging.getLogger(name)
    log.setLevel(LOG_LEVEL)
    # Remove any pre-existing handlers
    for h in list(log.handlers):
        log.removeHandler(h)

    # Add two file handlers
    for target in (cycle_dir, latest_dir):
        fh = logging.FileHandler(os.path.join(target, filename), mode='w')
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        log.addHandler(fh)

    # And one console handler if it’s not already there
    if not any(isinstance(h, logging.StreamHandler) for h in log.handlers):
        log.addHandler(logging.StreamHandler())

    return log
