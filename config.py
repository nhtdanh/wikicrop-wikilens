# config.py
import os
import psycopg2
import threading

# ================= BIẾN MÔI TRƯỜNG =================
from psycopg2.pool import ThreadedConnectionPool

# ================= BIẾN MÔI TRƯỜNG =================
# Thông số DB
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "adminpass")
DB_NAME = os.getenv("DB_NAME", "plant_knowledge_db")
DATABASE_URL = os.getenv("DATABASE_URL")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "")

# ================= KẾT NỐI DATABASE (CONNECTION POOL) =================
db_pool = None

def init_db_pool():
    global db_pool
    if db_pool is None:
        try:
            if DATABASE_URL:
                db_pool = ThreadedConnectionPool(2, 10, dsn=DATABASE_URL)
            else:
                db_pool = ThreadedConnectionPool(
                    2, 10,
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME
                )
            print("[+] Khoi tao Database Connection Pool thanh cong!")
        except Exception as e:
            print(f"[-] Loi khi khoi tao Database Connection Pool: {e}")
            raise e

def get_db_connection():
    global db_pool
    if db_pool is None:
        init_db_pool()
    return db_pool.getconn()

def release_db_connection(conn):
    global db_pool
    if db_pool and conn:
        db_pool.putconn(conn)

# ================= BIẾN CHIA SẺ (SHARED STATE) =================
predict_lock = threading.Lock()
last_api_call_time = [0.0]

# ================= CẤU HÌNH ĐƯỜNG DẪN MÔ HÌNH =================
LEAF_MODEL_PATH = os.getenv("LEAF_MODEL_PATH", "./models/MobileNetV3LargeModelEmbed.keras")
GENERAL_MODEL_PATH = os.getenv("GENERAL_MODEL_PATH", "./models/MobileNetV3LargeModelBaseLine.keras")