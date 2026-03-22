import psycopg
import pymysql
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine

# Load environment variables
load_dotenv()

# Get the connection string from environment
LOCAL_CONNECTION_STRING = os.getenv("LOCAL_CONNECTION_STRING")
CLOUD_CONNECTION_STRING = os.getenv("CLOUD_CONNECTION_STRING")

def connect_to_local_database():
    # Create the engine
    engine = create_engine(LOCAL_CONNECTION_STRING)

    return engine.connect()

def connect_to_cloud_database():
    """
    Connect to either MySQL or PostgreSQL database based on the connection string.
    
    Supports connection strings:
    - PostgreSQL: postgresql://user:password@host:port/database
    - MySQL: mysql://user:password@host:port/database or mysql+pymysql://...
    
    Returns:
        Connection object for the respective database
    """
    try:
        if CLOUD_CONNECTION_STRING is None:
            raise ValueError("CONNECTION_STRING not found in environment variables")
        # PostgreSQL connection
        conn = psycopg.connect(CLOUD_CONNECTION_STRING)
        print("✅ Successfully connected to PostgreSQL database!")
        
        # Get server version
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"Server version: {version[:50]}...")
        return conn
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None