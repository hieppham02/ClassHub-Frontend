# Chặng 1 và 2 trên schema hiện có

Cập nhật 2026-10-12: tên bảng/cột database đã chuyển sang tiếng Anh theo `../database/english-names.md`. Các tên tiếng Việt dưới đây mô tả schema tại thời điểm triển khai chặng 1–2; Backend đã được cập nhật mapping, API giữ tương thích.

Không tạo, xóa hoặc sửa bảng/cột; không import SQL, chạy migration hoặc thay cấu hình kết nối.

## Đã triển khai

- API ca học và giao diện lấy tên/giờ từ `cau_hinh_ca_hoc`, không dùng lịch hardcode.
- API danh mục thiết bị cho Admin cập nhật số lượng, tình trạng và ghi chú; dùng nhật ký hiện có.
- API phòng bổ sung `equipmentDetails`, giữ nguyên trường `equipment` cũ.
- Chặn đăng ký bộ thiết bị phòng có thiết bị không tốt hoặc số lượng không hợp lệ. Đây là chính sách bảo thủ cho danh mục phòng hiện tại; chưa phân biệt tài sản cố định và đồ cho mượn.
- Người mượn/được ủy quyền báo tình trạng trả vào `tinh_trang_tra`, `ghi_chu_tra`.
- Tủ khóa không tự hoàn tất phiếu. Admin kiểm tra thực tế, xác nhận qua Dashboard khi tủ online và khóa. Thiếu đồ tiếp tục RETURNING; đã trả đủ nhưng hỏng thì hoàn tất và chuyển tủ ERROR để chặn cấp phát, cần kiểm tra bảo trì trước khi mở lại.
- API cảnh báo tính hạn theo ngày/ca cộng 15 phút, có xử lý ca qua nửa đêm. Chỉ hiện phiên đang mượn/đang trả; không đổi trạng thái DB sang OVERDUE.
- Cảnh báo theo phiếu, tải lại mỗi 30 giây. Không tạo bản ghi cảnh báo hoặc gửi email/push.
- Bỏ VaiTro khỏi DTO đặt phòng và payload; quyền vẫn lấy từ JWT.

## Giới hạn

- Danh mục phòng không phải snapshot bộ thiết bị đã giao. Không sử dụng bảng `phieu_muon_thiet_bi` chưa tồn tại.
- Chưa có lịch sử sự cố/bảo trì dạng riêng, ảnh bằng chứng, định danh tài sản, camera hoặc xác nhận vật lý cửa. Dữ liệu LOCKED là trạng thái firmware báo; Admin phải kiểm tra thực tế.
- Nhật ký ghi người xác nhận Admin; `ma_sv_tra` giữ người yêu cầu trả.
- API return-report là bước riêng trước return-room; nếu MQTT lỗi, giữ RETURNING và cho gửi lại lệnh khóa.
- Chưa có lưu command/ack chống lặp theo command_id. Xác nhận phiếu hoàn tất được kiểm soát bằng transaction và trạng thái.
- Thời gian hiện theo DateTime.Now của Backend hiện có; server triển khai cần dùng múi giờ Việt Nam.

## Kiểm tra cần thực hiện trên môi trường chạy

1. Ca trong giao diện khớp DB, bao gồm ca_id không liên tục.
2. Sinh viên không cập nhật thiết bị hoặc xác nhận trả; không xem cảnh báo của người khác.
3. Report thiếu/hỏng yêu cầu ghi chú; phiên PENDING không được trả.
4. Tủ khóa chỉ cập nhật trạng thái tủ, phiếu vẫn RETURNING; Admin xác nhận đủ mới COMPLETED.
5. Thiếu đồ giữ RETURNING; hỏng giữ tủ ERROR; cập nhật thiết bị TOT sau kiểm tra bảo trì.
6. Quá hạn chỉ xuất hiện sau giờ kết thúc +15 phút; không có cho phiếu đã hoàn tất.
7. Mất kết nối không báo hoàn tất; gửi lại yêu cầu khóa không ghi lại tình trạng trả.

Build không thay thế kiểm thử tích hợp với MariaDB/MQTT/phần cứng. Không dùng database thật để kiểm thử ghi dữ liệu khi chưa được yêu cầu.
