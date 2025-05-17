import json
import requests
from typing import Dict
from datetime import datetime, timezone
from sqlalchemy import update
from db.session import SessionLocal
from db.models import ItemData
from utils.logging import get_logger

items_logger = get_logger('items', 'items.log')

API_URL = "https://api.hypixel.net/v2/resources/skyblock/items"

def fetch_items() -> Dict[str, str]:
    """
    Returns a dict mapping item_id -> pretty_name.
    """
    http = requests.Session()
    try:
        resp = http.get(API_URL)
        items_logger.info(f"items fetch status: {resp.status_code}, {resp.reason}")
        data = resp.json()
        # dump raw response for auditing
        with open('logs/items_response.json', 'w') as f:
            json.dump(data, f, indent=2)
        raw_items = data.get('items', [])
        return {item['id']: item['name'] for item in raw_items}
    except Exception:
        items_logger.exception("Failed fetching items")
        return {}

def process_items():
    session = SessionLocal()
    now = datetime.now(timezone.utc)
    try:
        items = fetch_items()
        items_logger.info(f"Fetched {len(items)} items at {now.isoformat()}")
        
        # Upsert each item via merge()
        for item_id, pretty_name in items.items():
            obj = ItemData(item_id=item_id, pretty_name=pretty_name)
            session.merge(obj)
        
        session.commit()
        items_logger.info("item_data table is up-to-date")
    except Exception:
        session.rollback()
        items_logger.exception("Error processing items")
    finally:
        session.close()