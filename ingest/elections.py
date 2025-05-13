import json, requests
from typing import Dict
from datetime import datetime, timezone
from sqlalchemy import update
from db.session import SessionLocal
from db.models import Election
from utils.logging import get_logger
from utils.decode import resolve_name

election_logger = get_logger('election', 'elections.log')

def process_elections():
    try:
        http = requests.Session()
        session = SessionLocal()
        now = datetime.now(timezone.utc)
        resp = http.get('https://api.hypixel.net/v2/resources/skyblock/election')
        election_logger.info(f"election status: {resp.status_code}, {resp.reason}")
        data = resp.json()
        with open('logs/election_response.json', 'w') as f:
            json.dump(data, f, indent=2)
        mayor = data.get('mayor', {})
        name = mayor.get('name', None) 
        year = mayor.get('election').get('year', None)
        if year and name and not session.query(Election).filter_by(year=year,mayor=name).first():
            session.add(Election(year=year, mayor=name, timestamp=now))
            election_logger.info(f"Added election {year} mayor={name}")
        session.commit()
        session.close()
    except:
        election_logger.exception("Error processing elections")