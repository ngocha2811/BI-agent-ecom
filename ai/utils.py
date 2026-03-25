from dotenv import load_dotenv
import os
from sqlalchemy import create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def connect_to_local_database():
    engine = create_engine(DATABASE_URL)
    return engine.connect()
