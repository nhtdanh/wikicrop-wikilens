# Hướng Dẫn Triển Khai Dịch Vụ Standalone Plant AI

Dịch vụ này được tách độc lập để deploy trực tiếp lên **Render** thông qua **Docker** và kết nối tới database **PostgreSQL Cloud** (có cài extension `pgvector`).

---

## 1. Chuẩn bị Cơ sở dữ liệu (PostgreSQL Cloud)

1. **Khởi tạo database:** Đảm bảo database của bạn hỗ trợ `pgvector`. Nếu sử dụng dịch vụ Managed Postgres (như Supabase, Neon, AWS RDS,...), extension này thường được hỗ trợ sẵn.
2. **Kích hoạt pgvector:**
   Kết nối vào database cloud của bạn và chạy lệnh SQL sau (nếu chưa bật):
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. **Import dữ liệu mẫu (`init.sql`):**
   Sử dụng công cụ quản trị (như pgAdmin, DBeaver) hoặc dòng lệnh `psql` để import tệp `init.sql` (nằm trong thư mục này) vào database của bạn:
   ```bash
   psql -h <your-db-host> -U <your-db-user> -d <your-db-name> -f init.sql
   ```
   *Lưu ý: Tệp `init.sql` đã chứa sẵn các bảng biểu cấu trúc dự án và dữ liệu vector mẫu.*

---

## 2. Triển khai lên Render (Web Service - Docker)

1. **Tạo Web Service mới:**
   * Truy cập vào Dashboard của Render -> Nhấp **New +** -> Chọn **Web Service**.
   * Kết nối với Repository Github chứa dự án này.
2. **Cấu hình thông tin cơ bản:**
   * **Name:** `plant-ai-service` (hoặc tên bất kỳ bạn thích).
   * **Root Directory:** `standalone-ai` *(Quan trọng: Để Render biết chỉ build thư mục này)*.
   * **Runtime:** `Docker`.
3. **Cấu hình Environment Variables (Biến môi trường):**
   * Nhấp chọn tab **Env Groups** hoặc **Environment**.
   * Thêm các biến sau:
     * `DATABASE_URL`: Đường dẫn kết nối Postgres Cloud của bạn.
       * *Dạng:* `postgresql://<user>:<password>@<host>:<port>/<db_name>?sslmode=require`
     * `R2_PUBLIC_URL`: (Tùy chọn) URL truy cập công khai của R2 Bucket của bạn.
       * *Dạng:* `https://pub-xxxxxx.r2.dev` hoặc custom domain. Nếu cài đặt, API sẽ tự động ghép tiền tố này thành link ảnh tuyệt đối.
     * `PORT`: `8000` (Render sẽ tự động ánh xạ cổng chạy cho bạn).
4. **Deploy:** Nhấp **Create Web Service**. Render sẽ tự động kéo code, build Docker image theo `Dockerfile` và start ứng dụng.

---

## 3. Kiểm tra API sau khi Deploy

Khi Render báo deploy thành công (`Live`), bạn có thể gọi API thông qua endpoint:
* **Địa chỉ:** `https://<ten-app-cua-ban>.onrender.com`

### Endpoint kiểm tra sức khỏe hệ thống (Health Check)
* **GET** `https://<ten-app-cua-ban>.onrender.com/`
* Trả về: Giao diện tài liệu Swagger/Redoc hiển thị các API có sẵn.

### Endpoint nhận dạng ảnh
* **POST** `https://<ten-app-cua-ban>.onrender.com/api/ai/search`
* **Body (JSON):**
  ```json
  {
    "imageBase64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "bbox": {
      "x": 0.0,
      "y": 0.0,
      "w": 100.0,
      "h": 100.0
    },
    "parts": ["Leaf"]
  }
  ```
