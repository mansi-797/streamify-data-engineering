import os
import psycopg2


def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5433,
        database="streamify",
        user="streamify",
        password=os.getenv("STREAMIFY_PG_PASSWORD", "streamify"),
    )
