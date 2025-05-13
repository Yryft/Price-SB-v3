import json, requests
from typing import Dict
from datetime import datetime, timezone
from sqlalchemy import update
from db.session import SessionLocal
from db.models import Firesale
from utils.logging import get_logger
from utils.decode import resolve_name

firesale_logger = get_logger('firesales', 'firesales.log')

def process_firesales():
    try:
        http = requests.Session()
        session = SessionLocal()
        now = datetime.now(timezone.utc)
        try:
            resp=http.get('https://api.hypixel.net/v2/skyblock/firesales')
            firesale_logger.info(f"firesales status: {resp.status_code}, {resp.reason} : {resp.json()}")
            data=resp.json()
            with open('logs/firesales_response.json','w') as f:
                json.dump(data,f,indent=2)
            fs_list=data.get('sales',[])
            firesale_logger.info(f"Found {len(fs_list)} firesales : {fs_list}")
        except:
            firesale_logger.exception("Failed fetching firesales")
            fs_list=[]
        for f in fs_list:
            if not f:
                firesale_logger.warning(f"Invalid firesale entry: {f}")
                continue

            try:
                firesale_logger.debug(f"Processing firesale {f['item_id']} : {f}")
                session.merge(
                    Firesale(
                        item_id   = f['item_id'],
                        timestamp = datetime.fromtimestamp(f['start'] / 1000, timezone.utc),
                        data      = f
                    )
                )
                firesale_logger.info(f"Added firesale item={f['item_id']}")
            except Exception:
                session.rollback()                             # ← clear the failed transaction
                firesale_logger.exception(f"Error processing firesale {f['item_id']}")
        session.commit()
        session.close()
    except Exception:
        firesale_logger.exception("Error processing firesales")
