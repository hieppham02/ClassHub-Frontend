# Nhận và trả thiết bị bằng QR — tủ phòng và tủ tự do

## Phạm vi

Toàn bộ tủ phòng (`ROOM`) và tủ tự do (`CORRIDOR`) dùng QR. Camera điện thoại cần HTTPS và quyền camera; Vite hiện đã có cấu hình HTTPS và proxy `/api`, `/hub` do người dùng cài trước tác vụ này.

FE dùng `QrAccessPanel.vue` trong chi tiết tủ: quét camera → backend kiểm tra QR → xác nhận mở cửa. Thư viện quét tải khi mở camera, dừng camera khi đóng panel hoặc đọc được mã. Tham khảo [ZXing Browser](https://github.com/zxing-js/browser).

## Luồng trạng thái

**Chế độ kiểm thử hiện tại:** `QrAccessService.RequireReturnVerification=false`. Trả đồ chỉ cần quét QR, nhận OPENED và CLOSED đúng phiếu/mã lệnh; CLOSED chuyển thẳng COMPLETED. Không chờ RFID/camera và không tạo kết quả cảm biến giả. Tình trạng/ghi chú trả vẫn được lưu nhưng không chặn hoàn tất trong chế độ này. Có thể xử lý lại CLOSED đã lưu của phiếu đang chờ kiểm tra. Firmware dùng `CLASSHUB_REQUIRE_RETURN_VERIFICATION=0` trong `QrAccess.h` để giải phóng tủ sau đóng cửa, không phát VERIFIED. Bật lại cả hai công tắc và nội dung hướng dẫn UI khi kết thúc kiểm thử. Các mục về kiểm tra thiết bị bên dưới mô tả chế độ đầy đủ khi bật lại.

1. Đăng ký tủ phòng hoặc tủ tự do: tạo phiếu `PENDING`, chụp danh sách thiết bị tủ theo phiếu, sinh QR `RECEIVE` và gửi đến màn hình tủ.
2. Quét QR, xác nhận: QR dùng một lần, gửi lệnh mở; phiếu vẫn `PENDING`.
3. Phản hồi `OPENED`: ghi nhận cửa mở. Phản hồi `CLOSED` cùng lệnh: chuyển `IN_USE`, ghi giờ nhận.
4. Bấm trả: lưu tình trạng trả và sinh QR `RETURN`; phiếu chuyển `RETURNING`.
5. Quét và xác nhận: mở tủ, quét RFID/đặt đồ vào, camera kiểm tra, đóng cửa.
6. Chỉ khi nhận `OPENED` rồi `CLOSED`, cùng mã lệnh, và kết quả RFID/camera đều đạt mới chuyển `COMPLETED`. Kết quả kiểm tra có thể đến trước hoặc sau đóng cửa.
7. Thiếu đồ/kiểm tra thất bại giữ `RETURNING`, phase `RETURN_FAILED`. Có thể cấp QR trả mới để bổ sung hoặc admin kiểm tra theo chức năng hiện có. Báo cáo `MAT_DO` không tự hoàn tất dù cảm biến báo đạt.

QR hết hạn sau 3 phút. Giới hạn giờ nhận đồ theo ca đang được tạm comment với dấu `TEMP QR TEST` để kiểm thử; bật lại cả Validate và Retry khi kết thúc thử nghiệm. Mã QR cũ bị thu hồi khi cấp lại. Token ngẫu nhiên 32 byte, database chỉ lưu SHA-256; API cấp QR không trả token cho điện thoại.

Backend đối chiếu tài khoản hoạt động, người mượn/người được ủy quyền, loại vị trí, phiếu, thao tác, tình trạng tủ và lượt mượn đang chiếm tủ. Các API mở và trả kiểu cũ đã được gỡ. Heartbeat/status chỉ cập nhật tủ; chuyển trạng thái phiếu cần sự kiện QR đúng sessionId/commandId.

## API

Tất cả endpoint yêu cầu đăng nhập và quyền trên phiếu.

| Endpoint | Body | Kết quả |
| --- | --- | --- |
| POST `/api/cabinet/qr/{sessionId}/issue` | `{"purpose":"RECEIVE"}` hoặc `RETURN` | Gửi QR tới màn hình, trả mã yêu cầu và hạn QR |
| POST `/api/cabinet/qr/{sessionId}/preview` | `{"purpose":"RECEIVE","token":"<64 ký tự hex>"}` | Kiểm tra trước khi hiển thị nút xác nhận |
| POST `/api/cabinet/qr/{sessionId}/open` | Cùng body preview | HTTP 202, `commandId`, chờ tủ xác nhận |
| POST `/api/cabinet/qr/{sessionId}/retry` | Không cần body | Gửi lại cùng mã lệnh đang chờ; không tạo lệnh thứ hai |

`GET /api/history/get-history` trả `qrEnabled` và `qrPhase`. Đăng ký trả `qrEnabled=true`, `qrDelivered`.

## Hợp đồng MQTT với firmware/HMI

Backend gửi QR đến `backend/cabinet/{roomId}/qr`:

```json
{
  "sessionId": 123,
  "room": "DTD201",
  "purpose": "RECEIVE",
  "qrId": 1,
  "content": "classhub:qr:v1:<64 ký tự hex>",
  "expiresAt": "2026-10-14T07:03:00Z",
  "action": "display_qr"
}
```

HMI mã hóa chính chuỗi `content` thành QR, hiển thị thao tác nhận/trả và thời hạn; xóa mã hết hạn, bị thay thế hoặc khi nhận lệnh mở. Token chỉ chuyển tới đúng màn hình tủ, không broadcast qua SignalR.

Backend gửi lệnh mở đến `backend/cabinet/{roomId}/action`:

```json
{
  "id": "123",
  "sessionId": 123,
  "room": "DTD201",
  "action": "open",
  "purpose": "RETURN",
  "commandId": "<32 ký tự hex>",
  "expiresAt": "2026-10-14T07:03:30Z",
  "expectedEquipment": [{ "equipmentId": 12, "name": "Micro", "quantity": 1 }]
}
```

Firmware phải lưu và chống thực thi lặp `commandId` (kể cả sau reconnect/reboot), từ chối lệnh hết hạn. Nếu nhận lại cùng mã lệnh, gửi lại trạng thái thực tế của thao tác đó, không mở cửa lần nữa. Khi mạng lỗi, backend giữ QR đã dùng và mã lệnh để đối chiếu; người dùng có thể gửi lại cùng lệnh.

Firmware gửi phản hồi vào `iot/cabinet/{roomId}/qr-result`:

```json
{ "sessionId": 123, "commandId": "<mã lệnh>", "event": "OPENED" }
```

```json
{ "sessionId": 123, "commandId": "<mã lệnh>", "event": "CLOSED" }
```

```json
{
  "sessionId": 123,
  "commandId": "<mã lệnh>",
  "event": "VERIFIED",
  "rfidPassed": true,
  "cameraPassed": true,
  "sequence": 1
}
```

`sequence` là số tăng dần cho mỗi kết quả kiểm tra của một mã lệnh, bắt đầu từ 1. Phản hồi cũ/trùng không ghi đè kết quả mới. `rfidPassed` chỉ true khi đã đối chiếu đủ danh sách `expectedEquipment`; camera kiểm tra đạt mới gửi `cameraPassed=true`. Backend tiếp nhận kết quả từ hệ thống RFID/camera theo giả định đã thực hiện phần này; không triển khai thuật toán thị giác hoặc đọc RFID trong repo FE/BE.

Nếu chắc chắn không mở được, gửi `event: "OPEN_FAILED"` với cùng phiếu/mã lệnh; backend cho phép cấp QR mới khi cửa đang đóng. Nếu mất phản hồi mà chưa biết cửa có mở không, không tự báo thành công hoặc tạo lệnh khác. Gửi `OPENED` trước `CLOSED`; sau reconnect gửi lại các phản hồi theo thứ tự này. Heartbeat/status cũ vẫn cập nhật kết nối tủ.

Broker phải phân quyền thiết bị: chỉ subscribe lệnh của tủ mình và chỉ publish status/qr-result của tủ mình. Backend lấy mã tủ từ topic, đối chiếu phiếu và command; không cung cấp API công khai để điện thoại gửi kết quả cảm biến.

## Database và chạy

Migration [qr-borrowing.sql](database/qr-borrowing.sql) thêm `borrowing_session.qr_enabled`, `qr_phase`, bảng `cabinet_qr_access` và bảng snapshot `borrowing_equipment` nếu chưa có. Có thể chạy lại. QR và lệnh dùng UTC; thời gian ca/nhận/trả giữ quy ước giờ Việt Nam của backend hiện có.

Chạy tiếp [remove-otp.sql](database/remove-otp.sql) để chuyển các phiếu chưa dùng QR và bỏ hai cột truy cập cũ. Trước migration cần đóng/đối soát mọi phiếu cũ đang mở; không tự suy ra đã nhận/trả. Lượt QR đang chạy được giữ nguyên. Các phiếu cũ IN_USE/RETURNING lấy snapshot từ danh mục thiết bị hiện tại nên cần admin đối soát nếu danh mục đã đổi. Giữ nguyên lịch sử mượn trả và audit.

Sau migration, khởi động lại backend bằng mã mới và frontend, nạp firmware mới cho các tủ. GPIO 4 điều khiển khóa ON/OFF, GPIO 5 xác nhận đóng cửa. RFID/camera nối qua adapter trong tài liệu IoT.

## Kiểm chứng

47 kiểm tra tích hợp chế độ chỉ mở/đóng đã qua trên database riêng với MQTT giả lập: đăng ký QR cho cả hai loại tủ, phân quyền, delegate, hạn mã, sử dụng một lần/quét đồng thời, API cũ không còn tồn tại, chống truy cập tủ đang mở bởi phiếu khác, đối chiếu room/command, thứ tự cửa, hoàn tất không tạo kết quả cảm biến giả, phản hồi trễ/lặp và lỗi mạng. 19 host test firmware chế độ này và 34 host test chế độ cảm biến bật lại đã qua. Migration chạy lại hai lần thành công; đã sao lưu cột truy cập cũ và áp dụng lên database hiện tại, xác nhận lịch sử mượn trả và lượt QR đang chạy được giữ nguyên. Chưa xác minh camera điện thoại hoặc firmware/HMI thực tế.
