import faulthandler
faulthandler.enable()

import psycopg2 # BẮT BUỘC: Import psycopg2 trước Keras/TensorFlow để tránh xung đột thư viện OpenSSL gây lỗi Segmentation Fault (Exit code 139)
import os
# Tối ưu hóa bộ nhớ TensorFlow trên môi trường CPU/RAM thấp (như Render Free Tier)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['TF_NUM_INTRA_OP_THREADS'] = '1'
os.environ['TF_NUM_INTEROP_THREADS'] = '1'

import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

# Import các thành phần đã tách
from utils.models import get_leaf_model
from api import router as api_router, init_api_models
from config import init_db_pool


# 2. Định nghĩa hàm lifespan thay cho @app.on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- PHẦN CODE CHẠY TRƯỚC YIELD TƯƠNG ĐƯƠNG VỚI "STARTUP" ---
    print("⏳ Đang khởi động hệ thống...")
    print("⏳ Đang nạp các mô hình AI vào RAM/GPU (Chỉ nạp 1 lần)...")
    leaf_model_global = get_leaf_model()
    print("✅ Nạp mô hình thành công!")
    
    # Tiêm (Inject) model vào API module
    init_api_models(leaf_model_global)

    print("ℹ️ RabbitMQ Worker bị tắt trong phiên bản Standalone-AI.")
    init_db_pool()

    # Nhường quyền cho ứng dụng FastAPI chạy (nhận request)
    yield 

    # --- PHẦN CODE CHẠY SAU YIELD TƯƠNG ĐƯƠNG VỚI "SHUTDOWN" ---
    # Khi bạn tắt server (Ctrl+C), code ở đây sẽ chạy.
    # Rất hữu ích nếu sau này bạn muốn clean up RAM, tắt kết nối DB an toàn.
    print("🛑 FastAPI server đang tắt. Dọn dẹp tài nguyên...")


# 3. Truyền hàm lifespan vào tham số khi khởi tạo app
app = FastAPI(title="Plant AI Service", lifespan=lifespan)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Cho phép tất cả các nguồn (có thể điều chỉnh sau)
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Gắn router từ api.py vào app (đặt tiền tố là /api)
app.include_router(api_router, prefix="/api")

# API Documentation
# POST /api/ai/reindex-features
# POST /api/ai/search

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    print(f"🌐 Bắt đầu chạy Uvicorn Server trên cổng {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False) 
    # reload=False RẤT QUAN TRỌNG, nếu True nó sẽ load lại model nhiều lần gây sập RAM