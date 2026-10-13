# Kho thiết bị và tài sản phòng

Trang `/admin/assets` có ba tab: Giám sát IoT, Tài sản, Kho thiết bị. URL cũ `tab=allocation` chuyển sang Kho thiết bị.

## Kho thiết bị

Không chọn phòng; quản lý chung danh mục và số lượng toàn hệ thống. Danh mục có tên, phân loại, cách quản lý theo số lượng/từng chiếc, trạng thái sử dụng. Tổng số lượng = đã cấp cho phòng + còn trong kho; khả dụng là thiết bị sử dụng tốt trong kho. Có lọc danh mục, phân loại và tình trạng, phân trang 20 dòng.

Thêm danh mục trước, rồi nhập kho chọn danh mục. Thiết bị riêng lẻ phải có mã duy nhất, mỗi lần nhập một chiếc. Sửa tên/phân loại cập nhật các bản ghi kho và phòng liên kết. Ngừng sử dụng chặn nhập/cấp thêm nhưng vẫn cho phép thu hồi. Không xóa danh mục còn số lượng; danh mục không còn thiết bị có thể xóa. Điều chỉnh tồn kho cần lý do; xóa thiết bị riêng lẻ đưa số lượng về 0 và lưu lịch sử.

## Tài sản

Chọn phòng, bấm Thêm thiết bị, chọn một bản ghi kho khả dụng và số lượng. Kho giảm, phòng tăng trong cùng giao dịch. Thay đổi số lượng tại mỗi nhóm: tăng lấy thêm từ kho cùng danh mục, giảm trả về kho, giữ tình trạng. Chỉ tăng nhóm sử dụng tốt; thiết bị riêng lẻ nhập 0 để trả về kho. Báo/đổi tình trạng không đổi tổng số lượng. Mọi cập nhật số lượng đều kiểm tra phiên bản và khóa giao dịch chống vượt tồn kho/cập nhật trùng.

## Database và API

Migration `database/equipment-catalog.sql` thêm duy nhất bảng `equipment_catalog` và khóa ngoại `equipment.catalog_id`. Dữ liệu cũ được gom theo tên/phân loại/cách quản lý/phạm vi; số lượng, vị trí và tình trạng giữ nguyên. Bản ghi `equipment.room_id = NULL` là kho; `audit_log` lưu lịch sử. Các trường tên/phân loại cũ được đồng bộ để giữ API mượn trả hiện có.

- `POST /api/admin/assets/catalogs`: tạo danh mục.
- `PATCH /api/admin/assets/catalogs/{id}`: sửa tên/phân loại/trạng thái, có `version`.
- `DELETE /api/admin/assets/catalogs/{id}?version=...`: xóa danh mục không còn thiết bị.
- `POST /api/admin/assets/receipts`: nhập kho theo `catalogId`.
- `POST /api/admin/assets/rooms/{roomId}/equipment`: thêm từ kho, `equipmentId`, `quantity`, `version`, `note`.
- `POST /api/admin/assets/{id}/room-quantity`: số lượng mới `actualCount`, `version`, `note`.
- `POST /api/admin/assets/{id}/count`: điều chỉnh tồn kho, không được chỉnh tài sản tại phòng qua endpoint này.

Các API yêu cầu ADMIN. Khởi động lại backend sau cập nhật code. Luồng IoT giữ nguyên.
