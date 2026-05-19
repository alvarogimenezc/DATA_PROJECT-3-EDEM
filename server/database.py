import psycopg2
import psycopg2.pool
import os
from dotenv import load_dotenv

load_dotenv()

_pool = None

def _get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            host=os.getenv("DB_HOST", "db"),
            port=5432,
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
    return _pool

def get_connection():
    return _get_pool().getconn()

def release_connection(conn):
    _get_pool().putconn(conn)
