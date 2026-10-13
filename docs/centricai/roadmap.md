# Lộ trình hoàn thiện ClassHub CentricAI

Cập nhật 2026-10-12: schema đang chạy đã đổi tên tiếng Anh; xem `../database/english-names.md`. Script chuẩn bị chi tiết phiếu cũng đã chuyển sang tên mới; vẫn chưa tạo bảng chi tiết trong database.

## Mục tiêu

Hoàn thiện prototype nối Web, Backend, tủ thông minh, cảm biến phòng và AI. Bắt đầu bằng dữ liệu nghiệp vụ để các bước kiểm đếm, cảnh báo và phân tích có đầu vào rõ ràng.

## Các chặng

| Chặng | Đầu ra | Điều kiện hoàn thành |
| --- | --- | --- |
| 1. Dữ liệu thiết bị và phiếu mượn | Chi tiết bộ thiết bị dự kiến theo phiếu; quản lý thiết bị; sự cố và bảo trì | Lịch sử không thay đổi khi danh mục thiết bị được sửa; thiết bị hỏng được kiểm soát khi cấp phát |
| 2. Vòng mượn trả và cảnh báo | Xác nhận trả, quá hạn theo ca cộng 15 phút, xử lý mất kết nối và sự kiện lặp | Không hoàn tất chỉ dựa vào lệnh khóa; cảnh báo không tạo lặp |
| 3. Telemetry phòng | Một node phòng, lưu dữ liệu có thời gian, biểu đồ và ngưỡng cảnh báo | Phân biệt dữ liệu mới, dữ liệu cũ và mất kết nối |
| 4. Computer Vision | Camera một ngăn, bộ ảnh có nhãn, kiểm đếm và xác nhận thủ công | Kiểm thử trả đủ, thiếu, sai loại và ảnh không chắc chắn |
| 5. Phân tích và dự báo | Nhu cầu phòng, bất thường, pin khi đủ dữ liệu | Đánh giá trên dữ liệu độc lập, so sánh phương pháp đối chứng |
| 6. Prototype tích hợp | Kịch bản demo, kiểm thử toàn luồng, bằng chứng và tài liệu | Các thành phần phối hợp được trên phần cứng thực tế |

## Chặng 1 bước đầu

Cập nhật: phần triển khai trên schema hiện có được ghi trong `stages-1-2.md`. Bảng chi tiết dưới đây vẫn chỉ là chuẩn bị, chưa áp dụng vào database và chưa được API sử dụng.

Thêm bảng `phieu_muon_thiet_bi` và model EF tương ứng. Một dòng ghi nhận một nhóm thiết bị trong bộ dự kiến của phiếu: tên, số lượng và tình trạng danh mục tại thời điểm lập bộ. Đây chưa phải bằng chứng đã nhận đồ, chưa phải mã tài sản riêng lẻ và chưa phải kết quả camera.

- Giữ nguyên `thiet_bi` để tương thích với danh mục hiện tại.
- Lưu tên và tình trạng độc lập với danh mục để lịch sử không bị viết lại.
- `thiet_bi_id` có thể null; khi xóa danh mục, giữ dòng lịch sử và bỏ liên kết.
- Chặn xóa phiếu có chi tiết để bảo toàn lịch sử.
- Không tự điền phiếu cũ bằng danh mục hiện tại vì không biết bộ thiết bị lúc mượn.
- Bước này chỉ thêm nền tảng schema/model. Chưa thay đổi API đặt, trả, MQTT hoặc giao diện.

## Triển khai schema

Nguồn schema đã đối chiếu: `../others/classhub_db.sql`. Dump có database `classhub_db`, được xuất từ MariaDB 10.4.32; khóa `phieu_muon.id` và `thiet_bi.id` đều là `INT` signed, bảng dùng InnoDB. Chưa có bảng `phieu_muon_thiet_bi` trong dump.

Script `001-borrowing-equipment.sql` chuẩn bị theo cấu trúc trên, chưa kiểm chứng thực thi trên MariaDB. Trước khi chạy cần chọn đúng database thử nghiệm, đối chiếu `SHOW CREATE TABLE phieu_muon`, `SHOW CREATE TABLE thiet_bi`, phiên bản server thực tế và sao lưu theo quy trình triển khai. Nếu khóa thực tế khác kiểu, phải điều chỉnh khóa ngoại trước.

Script không xóa dữ liệu, không backfill và không tự chạy khi ứng dụng khởi động. Chưa áp dụng vào database thực tế. Nếu bảng đã tồn tại, không chạy lại; cần đối chiếu cấu trúc với bản định nghĩa.

## Bước tiếp theo

1. Áp dụng schema trên database thử nghiệm và kiểm tra khóa ngoại, số lượng dương, tính duy nhất trong phiếu và bảo toàn snapshot.
2. Ghi bộ thiết bị dự kiến cùng transaction tạo phiếu, chỉ gồm thiết bị được phép cấp phát. Xác định thiết bị cố định và thiết bị cho mượn trước khi dùng toàn bộ danh mục phòng.
3. Bổ sung trường `equipment` vào API lịch sử, không thay đổi các trường cũ; phiếu cũ phải biểu thị chưa có dữ liệu chi tiết, không được hiểu là không có thiết bị.
4. Hiển thị bộ thiết bị dự kiến trên phiên mượn và lịch sử.
5. Thêm quản trị danh mục và định danh từng tài sản khi cần truy vết pin, bảo trì hoặc cấp phát riêng lẻ.
6. Bổ sung báo cáo sự cố và lịch sử xử lý; sau đó chuyển sang xác nhận trả và cảnh báo.

## Kiểm chứng

Build chỉ xác nhận model và mapping biên dịch. Chưa chứng minh script chạy trên database thực tế, API lưu bộ thiết bị hoặc phần cứng vận hành. Các bước tích hợp cần kiểm thử riêng sau khi có schema thử nghiệm.
