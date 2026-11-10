# Wildfire Intelligence — Realtime Laptop Camera

Ứng dụng Streamlit dùng camera laptop để phân tích trực tiếp từng frame bằng mô hình hiện có trong `predict.py`.

## 1. Cấu trúc thư mục

Đặt các file trong cùng thư mục với `app.py` hiện tại:

```text
your_project/
├── app.py
├── app_camera_realtime.py
├── predict.py
├── requirements-camera.txt
├── run_camera.bat
└── checkpoints/
    └── best_model.pth
```

Không cần thay thế `app.py` hoặc `predict.py`.

## 2. Cài đặt trên Windows

Mở CMD tại thư mục dự án rồi chạy:

```bat
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-camera.txt
```

Cài PyTorch theo CPU hoặc CUDA phù hợp với máy tại trang chính thức:
https://pytorch.org/get-started/locally/

Nếu môi trường hiện tại đã cài đúng PyTorch và các thư viện mà `predict.py` cần, có thể dùng lại môi trường đó và chỉ cài:

```bat
pip install -r requirements-camera.txt
```

## 3. Chạy ứng dụng

```bat
python -m streamlit run app_camera_realtime.py
```

Hoặc nhấp đúp `run_camera.bat`.

Mở URL Streamlit hiển thị trong terminal (thường là `http://localhost:8501`), nhấn **START** và cho phép trình duyệt truy cập camera.

## 4. Cách hoạt động

1. Trình duyệt gửi video camera laptop đến Streamlit qua WebRTC.
2. `WildfireCameraProcessor.recv()` nhận frame.
3. Cứ mỗi `Inference interval` giây, frame được chuyển thành ảnh JPEG tạm.
4. Ứng dụng gọi đúng hàm `predict(image_path, checkpoint_path)` đang được `app.py` sử dụng.
5. Kết quả Fire / Smoke / Neutral, confidence và xác suất từng lớp được hiển thị trên luồng video và dashboard.
6. Lịch sử dự đoán có thể tải xuống CSV.

## 5. Lưu ý quan trọng

- `predict.py` phải có hàm `predict(image_path, checkpoint_path)` và trả về bộ ba `(label, confidence, probs)` giống `app.py`.
- `checkpoints/best_model.pth` phải là checkpoint tương thích với `predict.py`.
- Tên lớp trong model nên là `Fire`, `Smoke`, `Neutral` (không phân biệt chữ hoa/thường). Các nhãn chứa `flame` được xếp vào Fire; nhãn chứa `normal` hoặc `no_fire` được xếp vào Neutral.
- Mặc định ứng dụng phân tích mỗi 0.75 giây. Nếu máy chậm, tăng lên 1–2 giây; nếu GPU/CPU đủ mạnh, giảm xuống 0.2–0.5 giây.
- Hàm `predict()` hiện tại có thể tải model lại ở mỗi lần gọi. Nếu thấy độ trễ cao, nên sửa `predict.py` để nạp model một lần và tái sử dụng model trong bộ nhớ.
- Trình duyệt phải có quyền camera. Trên máy khác hoặc khi triển khai qua mạng, WebRTC có thể cần cấu hình STUN/TURN và HTTPS.
- Đây là hệ thống phân loại ảnh học thuật, không phải hệ thống phát hiện cháy được chứng nhận và không nên dùng làm cảnh báo an toàn duy nhất.

## 6. Nếu camera không hoạt động

- Đóng ứng dụng khác đang chiếm camera (Zoom, Teams, Camera...).
- Kiểm tra quyền Camera trong Windows Settings → Privacy & security → Camera.
- Cho phép quyền camera trong trình duyệt.
- Thử Chrome hoặc Edge mới.
- Chạy ứng dụng trên `localhost` trước khi triển khai ra mạng.
- Nếu lỗi import `av` hoặc `streamlit_webrtc`, kích hoạt đúng virtual environment rồi cài lại `requirements-camera.txt`.
