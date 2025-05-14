import json, requests
from typing import Dict
from datetime import datetime, timezone
from sqlalchemy import update
from db.session import SessionLocal
from db.models import AuctionsSold, AuctionsLB, ItemSale
from utils.logging import get_logger
from utils.decode import resolve_name

auctions_ended_logger = get_logger('auction', 'auctions.log')

# implement fetch, resolve_name imported from utils.decode

def process_ended_auctions():
    session = SessionLocal()
    http = requests.Session()
    try:
        now = datetime.now(timezone.utc)
        resp = http.get('https://api.hypixel.net/v2/skyblock/auctions_ended')
        auctions_ended_logger.info(f"auctions_ended status: {resp.status_code}, {resp.reason}")
        data = resp.json()
        with open('logs/auctions_ended_response.json', 'w') as f:
            json.dump(data, f, indent=2)
        ended = data.get('auctions', [])
    except Exception:
        auctions_ended_logger.exception("Failed fetching auctions_ended")
        ended = []
    sales_counts: Dict[str, int] = {}
    for a in ended:
        try:
            if not a.get('bin'):
                continue
            if not a.get('item_bytes'):
                auctions_ended_logger.warning(f"No item_bytes for auction {a['auction_id']}, skipping")
                continue
            product_id, product_data = resolve_name(a)
            auctions_ended_logger.debug(f"Resolved auction item: {product_id}")
            if product_id == 'Unknown':
                auctions_ended_logger.warning(f"Unknown item for ended auction {a['auction_id']}")
            sales_counts[product_id] = sales_counts.get(product_id, 0) + 1
            
            a['data'] = product_data
            
            [a.pop(k, None) for k in ('bin','coop','start','end','bids','item_lore','last_updated','highest_bid_amount','claimed_bidders')]
            [a['data'].pop(k, None) for k in ('id','Count','Damage')]
            [a['data'].get('tag',{}).pop(k, None) for k in ('Unbreakable','HideFlags')]
            
            session.merge(AuctionsSold(product_id=product_id, timestamp=datetime.fromtimestamp(a['timestamp'] / 1000, timezone.utc), data=a))
            auctions_ended_logger.info(f"Stored auction {a['auction_id']} item={product_id}")
        except Exception:
            auctions_ended_logger.exception(f"Error processing ended auction {a.get('auction_id')}")
    session.flush()
    try:
        session.bulk_insert_mappings(ItemSale, [{'item_id': i, 'count': c, 'timestamp': now} for i,c in sales_counts.items()])
        auctions_ended_logger.info(f"Inserted ItemSale entries: {sales_counts}")
    except:
        auctions_ended_logger.exception("Failed bulk insert ItemSale")
    session.commit()
    session.close()