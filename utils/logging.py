import logging, os, shutil
from datetime import datetime

LOG_LEVEL = logging.DEBUG
ROOT_LOG_DIR = 'logs'

# 1) Pick a timestamp for this run
cycle_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
cycle_dir = os.path.join(ROOT_LOG_DIR, cycle_ts)
latest_dir = os.path.join(ROOT_LOG_DIR, 'latest')

# 2) Create the archive folder
os.makedirs(cycle_dir, exist_ok=True)

# 3) Reset the "latest" folder
if os.path.exists(latest_dir):
    shutil.rmtree(latest_dir)
os.makedirs(latest_dir, exist_ok=True)

# 4) Configure root logger to write both to archive and latest
handlers = [
    logging.FileHandler(os.path.join(cycle_dir, 'main.log'), mode='w'),
    logging.FileHandler(os.path.join(latest_dir, 'main.log'), mode='w'),
    logging.StreamHandler(),
]
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=handlers
)

def get_logger(name: str, filename: str) -> logging.Logger:
    """
    Create or reconfigure a logger that writes both to
      logs/<cycle_ts>/<filename>
      logs/latest/<filename>
    """
    log = logging.getLogger(name)
    log.setLevel(LOG_LEVEL)

    # Remove old handlers (if any)
    for h in list(log.handlers):
        log.removeHandler(h)

    # Add file handlers pointing to both dirs
    for target_dir in (cycle_dir, latest_dir):
        fh = logging.FileHandler(os.path.join(target_dir, filename), mode='w')
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
        log.addHandler(fh)

    # (Optionally) also echo to console:
    # if not any(isinstance(h, logging.StreamHandler) for h in log.handlers):
    #     log.addHandler(logging.StreamHandler())

    return log
