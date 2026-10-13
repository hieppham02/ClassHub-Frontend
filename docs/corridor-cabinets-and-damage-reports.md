# Tủ hành lang và báo cáo hỏng hóc

- Mỗi tầng của mỗi tòa có một tủ tên **Tủ tự do**, nằm ở hành lang. Tủ ngoài đời lớn hơn; trên client dùng đồ họa hai cánh nhưng cùng kích thước với tủ phòng. Tên không kèm số thứ tự hoặc tầng.
- Bổ sung **5 tủ phòng mới mỗi tầng**, giữ các tủ/phòng đang có. Tên theo mã tòa–số phòng, ví dụ DTD-501, TT-501, VNB-501, EAUT-501 (PLC dùng PLC). Số phòng mới nối tiếp số lớn nhất của các phòng mẫu tại tầng đó để không trùng tên; ví dụ đã có DTD-401 thì các tủ mới là DTD-402 đến DTD-406. Tủ có vị trí mượn và bản ghi cabinet riêng, dùng API/quy trình mượn hiện có.
- Danh mục đồ dùng chung: ổ điện, cáp mạng LAN, phấn viết bảng.
- Giữ quy trình đăng ký theo ngày/ca, OTP, mở tủ, ủy quyền và trả đồ hiện có; mỗi người vẫn chỉ có một phiếu chưa hoàn tất.
- Sinh viên bấm **Báo hỏng hóc** ở góc trên bên phải panel danh sách tủ, cạnh chú thích, chọn phòng/tủ, nhập thiết bị và mô tả rồi gửi. Có thể báo khi tủ ngoại tuyến/bảo trì, không cần đang mượn.
- Admin xem ở **Quản lý tài sản → Tài sản**, chọn phòng hoặc tủ hành lang. Ba card Toàn bộ cảnh báo / Đã xử lý / Chưa xử lý lọc danh sách của vị trí được chọn; số trên card theo phạm vi tòa/tầng. Vị trí có báo cáo chưa xử lý được đánh dấu.
- Tổng quan tài sản dùng biểu đồ tròn theo tình trạng, với card cảnh báo bên cạnh. Xử lý báo cáo yêu cầu ghi kết quả; không tự đổi tình trạng/tồn kho thiết bị.

## Dữ liệu và triển khai

`database/corridor-cabinets.sql` thêm `room.location_type` và khởi tạo một vị trí CORRIDOR mỗi tầng. Bảng `room` được tái sử dụng làm bảng vị trí mượn để giữ khóa ngoại và hợp đồng API cũ; CORRIDOR không phải phòng học và được loại khỏi danh sách/phép đếm phòng học trong quản lý tòa nhà. Tủ hành lang có trong bộ chọn vị trí tài sản, không nằm trong bộ chọn phòng giám sát IoT.

Database hiện tại có **32 tủ tự do và 160 tủ thường mới / 32 tầng**, giữ các phòng/tủ cũ. Khóa duy nhất `(building_id, corridor_floor)` chặn tủ tự do thứ hai trên cùng tầng; `corridor_floor` là cột sinh chỉ có giá trị cho loại CORRIDOR. Các tủ thường dùng mã vị trí `STANDARD-...` riêng và loại ROOM để đi qua nghiệp vụ hiện có. Có thể chạy lại script khởi tạo khi thêm tòa/tầng; không tự xóa tủ hay đặt lại dữ liệu hiện có. Script hỗ trợ tầng 1–100.

Tủ mới ngoại tuyến, MAC có tiền tố `UNCONFIGURED-`; cần cấu hình MAC/topic và phần cứng thực tế trước khi mượn. Không tạo tồn kho giả. Admin nhập số lượng thực ở **Kho thiết bị → Nhập kho**, sau đó chọn tủ hành lang trong tab **Tài sản → Thêm thiết bị** để cấp đồ từ kho. Phấn vẫn tuân theo quy trình trả như yêu cầu hiện tại.

Báo cáo lưu trong `audit_log` với action `DAMAGE_REPORT`; khi xử lý, cập nhật trạng thái/kết quả và ghi thêm `DAMAGE_RESOLVE`. Không cần bảng báo cáo mới.

| API | Quyền | Chức năng |
| --- | --- | --- |
| POST `/api/damage-reports` | Đăng nhập, tài khoản hoạt động | `roomId`, `equipmentName`, `description` (10–2000 ký tự) |
| GET `/api/damage-reports` | ADMIN | Danh sách báo cáo và trạng thái |
| PATCH `/api/damage-reports/{id}/resolve` | ADMIN | `note` (3–1000 ký tự), chỉ xử lý một lần |

Khởi động backend bằng mã mới để nạp endpoint và trường loại vị trí. Không tự gửi email/thông báo ngoài ứng dụng.

## Kiểm tra

- `npm.cmd run build`: thành công; còn cảnh báo kích thước bundle hiện có.
- Backend `dotnet build --no-restore`: thành công; có cảnh báo nullable ở các file hiện có.
- Script xác minh số tủ, chạy lại không tạo trùng và database từ chối tủ tự do thứ hai trên cùng tầng.
- 18 kiểm tra API trên database riêng, gồm đúng 5 tủ phòng mới / 1 tủ tự do mỗi tầng, tên theo mã tòa và số phòng không trùng mẫu cũ, liên kết vị trí mượn, xác thực/phân quyền, dữ liệu nhập và xử lý báo hỏng.
- Chưa xác minh giao diện bằng trình duyệt hoặc phần cứng IoT thực tế.
