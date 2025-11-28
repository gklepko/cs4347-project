import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    # returns a raw MySQL connection
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("MYSQL_HOST"),
            user=os.environ.get("MYSQL_USER"),
            password=os.environ.get("MYSQL_PASS"),
            database=os.environ.get("MYSQL_DB"),
            autocommit=False 
        )
        if conn.is_connected():
            return conn
        else:
            print("[DB ERROR] Could not establish connection.")
            return None
    except Error as e:
        print(f"[DB ERROR] Failed to connect: {e}")
        return None

def close_connection(conn, cursor=None):
    """Safely closes connection and cursor."""
    if cursor:
        try:
            cursor.close()
        except Error:
            pass
    if conn and conn.is_connected():
        try:
            conn.close()
        except Error:
            pass

        