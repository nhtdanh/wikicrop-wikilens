# Sử dụng image Python chuẩn (3.10 slim gọn nhẹ, độ tương thích cao với các lib AI)
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Copy file requirements.txt vào trước để tận dụng Docker Cache cho các packages
COPY requirements.txt .

# Cài đặt các thư viện Python (Thêm --no-cache-dir để giảm dung lượng image)
# Nâng cấp pip trước để cài đặt các binary wheels mượt mà nhất
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn ứng dụng vào container
COPY . .

# Expose port 8000 (khớp với Render)
EXPOSE 8000

# Lệnh khởi chạy ứng dụng (Mặc định chạy main.py để nhận diện cổng động từ Render)
CMD ["python", "main.py"]