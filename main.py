import time
from ingest.auctions_ended import process_ended_auctions
from ingest.auctions_lb import process_auctions_lb
from ingest.bazaar import process_bazaar_snapshot
from ingest.elections import process_elections
from ingest.firesales import process_firesales

POLL_INTERVAL = 1200 # seconds

def run_once():
    # call each ingest module
    process_ended_auctions()
    process_auctions_lb()
    process_bazaar_snapshot()
    process_firesales()
    process_elections()

if __name__ == '__main__':
    while True:
        run_once()
        time.sleep(POLL_INTERVAL)