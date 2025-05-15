from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

import requests
from sqlalchemy.orm import Session

from db.session import SessionLocal
from db.models import AuctionsLB
from utils.logging import get_logger
from utils.decode import resolve_name

# Configuration constants
MAX_WORKERS   = 10
AUCTIONS_API  = "https://api.hypixel.net/v2/skyblock/auctions"

auction_lb_logger = get_logger('auction', 'auctions_lb.log')

def fetch_json(url: str, params: Dict[str, Any] = None) -> Any: # type: ignore
    session = requests.Session()
    try:
        resp = session.get(url, params=params)
        auction_lb_logger.info(f"GET {url} page={params.get('page')} : {resp.status_code}")
        resp.raise_for_status()
        return resp.json()
    except Exception:
        auction_lb_logger.exception(f"Failed GET {url} page={params.get('page')}")
        return {}


def fetch_all_auctions() -> List[Dict[str, Any]]:
    auction_lb_logger.info("Fetching all auctions...\n")
    first = fetch_json(AUCTIONS_API, {'page': 0})
    total = first.get('totalPages', 0)
    auction_lb_logger.info(f"Total pages: {total}")

    all_auctions: List[Dict[str, Any]] = first.get('auctions', [])
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as exe:
        futures = [
            exe.submit(fetch_json, AUCTIONS_API, {'page': p})
            for p in range(1, total)
        ]
        for f in as_completed(futures):
            page = f.result()
            all_auctions.extend(page.get('auctions', []))

    auction_lb_logger.info(f"Fetched {len(all_auctions)} auctions total")
    return all_auctions


def _process_one(a: Dict[str, Any]) -> Optional[Tuple[str, float, Dict[str, Any]]]:
    """Return (product_id, price, cleaned_auction) or None if skip."""
    if not a.get('bin'):
        return None

    item_bytes = a.pop('item_bytes', None)
    

    if item_bytes is None:
        return None

    product_id, decoded = resolve_name(item_bytes)
    if product_id == 'Unknown':
        return None

    price = a.get('starting_bid')
    if price is None:
        return None

    # attach decoded data
    a['data'] = decoded
    [a.pop(k, None) for k in ('extra','bin','coop','start','end','bids','item_lore','last_updated','highest_bid_amount','claimed_bidders')]
    [a['data'].pop(k, None) for k in ('id','Count','Damage')] # type: ignore
    [a['data'].get('tag',{}).pop(k, None) for k in ('ench','SkullOwner','Unbreakable','HideFlags')] # type: ignore
    return product_id, price, a


def process_auctions_lb():
    auction_lb_logger.info("Processing auctions LB...")
    try:
        all_auctions = fetch_all_auctions()

        # 1) Parallel decode & filter
        results: List[Tuple[str, float, Dict[str, Any]]] = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as exe:
            futures = [exe.submit(_process_one, a) for a in all_auctions]
            for f in as_completed(futures):
                res = f.result()
                if res:
                    results.append(res)

        # 2) Pick lowest-BIN per product
        lowest: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        for pid, price, clean in results:
            current = lowest.get(pid)
            if current is None or price < current[0]:
                lowest[pid] = (price, clean)

        auction_lb_logger.info(f"Keeping {len(lowest)} lowest‐BIN auctions")
        session: Session = SessionLocal()
        # 3) Upsert winners
        for pid, (_, auction_dict) in lowest.items():
            lb = AuctionsLB(
                product_id=pid,
                timestamp = datetime.now(timezone.utc),
                data      = auction_dict
            )
            session.merge(lb)

        session.commit()
        auction_lb_logger.info(f"{len(lowest)} Lowest BIN auctions persisted.")
    except Exception:
        auction_lb_logger.exception("Error processing auctions_lb")
    finally:
        session.close() # type: ignore
