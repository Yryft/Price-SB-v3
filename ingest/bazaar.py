import json, requests
from typing import Dict
from datetime import datetime, timezone
from sqlalchemy import update
from db.session import SessionLocal
from db.models import Bazaar
from utils.logging import get_logger
from utils.decode import resolve_name

bazaar_logger = get_logger('bazaar', 'bazaar.log')

def process_bazaar_snapshot():
    try:
        http = requests.Session()
        session = SessionLocal()
        now = datetime.now(timezone.utc)
        try:
                resp = http.get('https://api.hypixel.net/v2/skyblock/bazaar')
                bazaar_logger.info(f"bazaar status: {resp.status_code}, {resp.reason}")
                data = resp.json()
                with open('logs/bazaar_response.json', 'w') as f:
                    json.dump(data, f, indent=2)
                products = data.get('products', {})
        except:
            bazaar_logger.exception("Failed fetching bazaar")
            products = {}
        baz_entries=[]
        for pid,info in products.items():
            try:
                try:
                    info['quick_status']['sellPrice'] = info['sell_summary'][0]['pricePerUnit']
                except:
                    info['quick_status']['sellPrice'] = 0
                try:
                    info['quick_status']['buyPrice'] = info['buy_summary'][0]['pricePerUnit']
                except:
                    info['quick_status']['buyPrice'] = 0
                baz_entries.append({'product_id': pid, 'timestamp': now, 'data': info['quick_status']})
                bazaar_logger.info(f"Added bazaar product {pid}")
            except Exception as e:
                bazaar_logger.exception(f"Error processing bazaar entry {pid}, {e}")
        try:
            session.bulk_insert_mappings(Bazaar, baz_entries)
        except:
            bazaar_logger.exception("Failed bulk insert Bazaar")
        session.commit()
        session.close()
    except Exception:
        bazaar_logger.exception("Error processing bazaar")