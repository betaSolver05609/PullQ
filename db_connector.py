# -*- coding: utf-8 -*-
import psycopg2
from contextlib import contextmanager


def test_connection(host, port, dbname, username, password):
    """Test a Postgres connection and return True/False."""
    try:
        connection = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=username,
            password=password,
            connect_timeout=5
        )
        connection.close()
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def connect_postgres(config):
    """
    Get a live Postgres connection from a saved config.
    Config must contain: host, port, dbname, username, password
    """
    try:
        connection = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            dbname=config["dbName"],
            user=config["username"],
            password=config["password"],
            connect_timeout=5
        )
        return connection
    except Exception as e:
        print(config)
        print(f"[ERROR] Connection to database failed: {e}")
        return None


@contextmanager
def get_connection(config):
    """
    Context manager to automatically close the connection after use.
    Example:
        with get_connection(config) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
    """
    conn = None
    try:
        conn = connect_postgres(config)
        if conn is None:
            raise RuntimeError("Failed to connect to database.")
        yield conn
    finally:
        if conn:
            conn.close()


def run_query(connection, query, params=None):
    """
    Run a query safely and return all rows.
    Returns [] on error.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            if cursor.description:  # Only fetch if query returns rows
                return cursor.fetchall()
            return []
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")
        return []
