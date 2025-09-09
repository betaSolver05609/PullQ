# -*- coding: utf-8 -*-
import psycopg2

def test_connection(host, port, dbName, username, password):
    try:
        connection = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbName,
            user=username,
            password=password,
            connect_timeout=5
            )
        connection.close()
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

        

def connect_postgres(host, port, dbName, username, password):
    try:
        connection = psycopg2.connect(
            host=host,
            port=port,
            dbname = dbName,
            user=username,
            password=password,
            connect_timeout=5
            )
        return connection
    except Exception as e:
        print(f"Connection to database failed {e}")
        return None
