from dotenv import load_dotenv
import os
from pymongo import *

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')

def open_connection():
    conn = MongoClient(mongo_uri)

    return conn

def close_connection(conn):
    conn.close()