import psycopg2
from src.config import DATABASE_URL


def get_conn():
    """Return a new psycopg2 connection. Caller is responsible for closing it."""
    return psycopg2.connect(DATABASE_URL)
