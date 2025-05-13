from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL",
    'postgresql://postgres:gRfHfgHAaccESTvudiIvHGEtPvcjWLpp@yamabiko.proxy.rlwy.net:25508/railway')

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)