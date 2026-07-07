# api.py
import time
import base64
import psycopg2.extras
from io import BytesIO
from PIL import Image
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
from config import (
    get_db_connection,
    release_db_connection, 
    predict_lock, 
    last_api_call_time,
    R2_PUBLIC_URL)
from utils.models import preprocess_image

# Khởi tạo Router (thay vì app) để có thể gộp vào main.py
router = APIRouter()

class Bbox(BaseModel):
    x: float
    y: float
    w: float
    h: float

class SearchRequest(BaseModel):
    imageBase64: str
    bbox: Bbox
    parts: list[str]

# Dùng Dependency Injection mộc mạc: Biến toàn cục sẽ được set từ main.py
leaf_model_instance = None

def init_api_models(leaf):
    global leaf_model_instance
    leaf_model_instance = leaf

@router.post("/ai/search")
async def ai_search(request: SearchRequest):
    last_api_call_time[0] = time.time()
    
    try:
        # 1. Giải mã Base64
        header, encoded = request.imageBase64.split(",", 1)
        image_data = base64.b64decode(encoded)
        img = Image.open(BytesIO(image_data)).convert('RGB')
        
        # 2. Lấy kích thước ảnh gốc (pixel)
        img_w, img_h = img.size
        
        # ==================== LOGIC CẮT ẢNH AN TOÀN (SAFE CROP) ====================
        # Đảm bảo phần trưng bày gửi lên nằm trong khoảng 0 -> 100
        safe_x = max(0, min(100, request.bbox.x))
        safe_y = max(0, min(100, request.bbox.y))
        safe_w = max(0, min(100, request.bbox.w))
        safe_h = max(0, min(100, request.bbox.h))

        if safe_x == 0 and safe_y == 0 and safe_w == 100 and safe_h == 100:
            cropped_img = img
        else:
            left = (safe_x / 100) * img_w
            top = (safe_y / 100) * img_h
            right = left + ((safe_w / 100) * img_w)
            bottom = top + ((safe_h / 100) * img_h)
            
            left = int(left)
            top = int(top)
            right = int(right)
            bottom = int(bottom)
            
            if right > left and bottom > top:
                cropped_img = img.crop((left, top, right, bottom))
            else:
                cropped_img = img
        # ===========================================================================
    
        # 3. Đưa vào hàm tiền xử lý (Sẽ tự động Letterboxing chống méo)
        processed_img = preprocess_image(cropped_img) 
        
        # ... Phần query cơ sở dữ liệu và trả kết quả giữ nguyên như cũ ...
        conn = get_db_connection()
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) 
            final_results = {}
    
            for part in request.parts:
                # Luon su dung mo hinh La (Leaf) de tiet kiem RAM va tai nguyen
                model = leaf_model_instance
                db_part_type = 'Leaf' # So khop voi anh La trong DB de dam bao dung khong gian vector
                
                if model is None:
                    raise HTTPException(
                        status_code=500,
                        detail="Mo hinh nhan dang La chua duoc tai thanh cong tren Server."
                    )
                
                with predict_lock:
                    features = model.predict(processed_img, verbose=0)
                    
                vector_str = f"[{','.join(map(str, features.flatten().tolist()))}]" 
                
                query = """
                    WITH UniqueVarieties AS (
                        SELECT DISTINCT ON (v.variety_id)
                            v.variety_id, v.common_name, v.variety_name,
                            pi.url as thumbnail,
                            1 - (pi.cnn_feature_vector::vector <=> %s::vector) AS similarity
                        FROM plant_images pi
                        JOIN varieties v ON pi.variety_id = v.variety_id
                        WHERE pi.part_type = %s 
                          AND pi.is_standard = true
                          AND pi.cnn_feature_vector::vector IS NOT NULL
                        ORDER BY v.variety_id, pi.cnn_feature_vector::vector <=> %s::vector ASC
                    )
                    SELECT * FROM UniqueVarieties
                    ORDER BY similarity DESC
                    LIMIT 5;
                """
                cursor.execute(query, (vector_str, db_part_type, vector_str))
                rows = cursor.fetchall()
                
                # Neu cau hinh R2_PUBLIC_URL, tu dong ghep thanh URL tuyet doi de client hien thi luon
                if R2_PUBLIC_URL:
                    for row in rows:
                        if row.get('thumbnail') and not row['thumbnail'].startswith('http'):
                            row['thumbnail'] = R2_PUBLIC_URL.rstrip('/') + '/' + row['thumbnail'].lstrip('/')
                
                final_results[part] = rows
                
            cursor.close()
        finally:
            release_db_connection(conn)

        last_api_call_time[0] = time.time()
        return {"success": True, "results": final_results}

    except Exception as e:
        print(f"❌ Lỗi xử lý AI Search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import JSONResponse

@router.get("/health")
@router.head("/health")
async def health_check():
    db_status = "healthy"
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.fetchone()
        cursor.close()
        release_db_connection(conn)
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    model_status = "healthy" if leaf_model_instance is not None else "unhealthy"
    overall_status = "healthy" if (db_status == "healthy" and model_status == "healthy") else "unhealthy"

    return JSONResponse(
        status_code=200 if overall_status == "healthy" else 500,
        content={
            "status": overall_status,
            "database": db_status,
            "model": model_status
        }
    )