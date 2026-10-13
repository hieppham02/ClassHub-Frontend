# Quản lý tài sản

Trang `/admin/assets` dành cho quản trị viên, lấy phòng học làm trung tâm, phân trang 20 dòng.

Luồng kho/tài sản đã cập nhật: xem [Kho thiết bị và tài sản phòng](warehouse-management.md). Tab Kho thiết bị quản lý chung, không chọn phòng; các thao tác cũ về phân bổ được thay bằng thêm/đổi số lượng trong tab Tài sản.

- **Giám sát IoT:** đọc node và dữ liệu đo đang lưu; xem dòng điện, nhiệt độ, độ ẩm, chất lượng không khí và lịch sử tối đa 200 mẫu. Dữ liệu mock được ghi rõ, không hiển thị kết nối trực tuyến giả. Giao diện làm mới mỗi 30 giây.
- **Tài sản:** thêm thiết bị từ kho hoặc đổi số lượng bằng cấp/thu hồi. Báo hoặc đổi tình trạng toàn bộ hay một phần số lượng; ví dụ 3/40 ghế bảo trì vẫn giữ tổng 40 ghế.
- **Kho thiết bị:** CRUD danh mục chung, nhập kho, điều chỉnh số lượng/tình trạng. Thiết bị theo mã riêng có số lượng 1 và mã duy nhất; tài sản theo nhóm quản lý số lượng.

## Dữ liệu

Script `database/assets-inventory.sql` mở rộng `equipment`, sử dụng `audit_log` cho lịch sử, không tạo bảng mới. `room_id = NULL` là kho; `usage_scope = ROOM` là tài sản phòng; dữ liệu cũ giữ `CABINET`. `catalog_code` liên kết các phần được tách theo tình trạng/vị trí. `version` và khóa giao dịch ngăn hai thao tác đồng thời làm sai số lượng.

Nhập số lượng thực tế bằng tab Kho thiết bị. Không tự tạo tài sản trong kho. Tài sản phòng bị hỏng không chặn nghiệp vụ mượn thiết bị tủ.

## API

Các endpoint `/api/admin/assets` yêu cầu vai trò `ADMIN`:

| Endpoint | Chức năng |
| --- | --- |
| GET `/` | Phòng, tài sản và thông số node mới nhất |
| GET `/nodes/{id}/history?hours=24` | Lịch sử node, 1–720 giờ |
| GET `/history?page=1&roomId=...` | Nhật ký, 20 dòng/trang |
| POST `/receipts` | Nhập kho |
| PATCH `/{id}/condition` | Đổi tình trạng, `affectedCount`, `version`, `condition`, `note`; không nhận trường `quantity` |
| POST `/{id}/move` | `ALLOCATE`, `RETURN`, `TRANSFER`; số lượng, phiên bản, phòng nhận và ghi chú |
| POST `/{id}/count` | Kiểm kê số lượng thực tế và lý do |

API cũ chỉnh sửa thiết bị cũng từ chối thay đổi số lượng trực tiếp. Sau cập nhật, khởi động lại backend để nạp endpoint mới. Chưa xác minh phần cứng IoT thực tế.

## Dòng điện tổng phòng

Cập nhật: luôn theo dõi phòng có hoặc không có lượt mượn; khi mất kết nối dùng số đo cuối cùng kèm thời điểm nhận, vẫn phân loại mức tiêu thụ dưới/từ 1A. Chỉ trường hợp chưa từng có số đo mới hiển thị chưa có dữ liệu. Cảnh báo kéo dài vẫn cần chuỗi mẫu mới liên tục.

`PATCH /api/admin/assets/nodes/{id}/status` nhận `ACTIVE` hoặc `DISABLED`. Bảo trì được lưu trong trạng thái node và ghi nhật ký; khôi phục hoạt động không tự coi node trực tuyến. Tổng node hoạt động là trực tuyến cộng ngoại tuyến, không bao gồm bảo trì. Không đổi schema.

`GET /api/admin/assets/nodes/{id}/power` đối chiếu các mẫu dòng điện với khoảng từ nhận đến trả của lượt mượn, theo thời gian Việt Nam. Dưới 1A là tiêu thụ thấp; từ 1A là có tiêu thụ điện, không xác định bật/tắt từng thiết bị. Ngoài thời gian mượn, dòng điện từ 1A liên tục ít nhất 5 phút mới tạo cảnh báo kiểm tra. Khoảng cách mẫu không vượt quá `max(90 giây, 3 × chu kỳ gửi)`; dữ liệu quá cũ, giá trị không hợp lệ hoặc chất lượng không GOOD trả về UNKNOWN. Không dùng màu ngẫu nhiên cho dòng điện. Tình trạng tài sản không bị thay đổi bởi dữ liệu đo. Không thay đổi schema.
