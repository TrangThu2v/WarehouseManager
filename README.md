# WarehouseManager

Giao diện mô phỏng màn hình **phiếu nhập** theo ảnh mẫu đã được thêm bằng HTML/CSS/JS thuần.

## Chạy nhanh

```bash
python3 -m http.server 8080
```

Sau đó mở `http://localhost:8080`.

## Kết nối với database thực tế

Hiện tại dữ liệu trong `app.js` là mock (`const receipts = [...]`).
Để dùng database của bạn:

1. Tạo API trả về danh sách phiếu nhập (JSON).
2. Thay `receipts` bằng dữ liệu từ `fetch('/api/receipts')`.
3. Map các cột tương ứng: trạng thái, ngày nhập, người nhập, số lượng, tổng tiền, nợ.
