# Database English names

Name-only changes. Status values and API payloads remain unchanged.

Applied to `classhub_db` on 2026-10-12. Ten tables, 328 existing rows preserved; sorted row checksums match before and after. Foreign keys and check constraints were restored. Forward and rollback scripts were rehearsed on an isolated database, which was removed after verification.

Backend model attributes and EF physical column/table mappings use the new names. Existing CLR identifiers, routes and JSON contracts remain compatible with the frontend. New `IotNode` and `IotSensor` models use English properties. The future `borrowing_equipment` model has no live table and is not queried.

Backend build passed with zero errors and 14 pre-existing warnings. Read-only EF verification covered mapped columns for all ten live tables and room/equipment/cabinet/account relationships. Full HTTP/MQTT/hardware workflows were not exercised during the rename.

`rename-to-english.sql` is already applied; do not run it again. `rollback-english-names.sql` restores database names only; restore the corresponding previous backend files at the same time. No application should write while renaming or rolling back. The original `others/classhub_db.sql` remains an old-name dump and must not be imported over the renamed database.

| Previous table | New table | Column changes |
| --- | --- | --- |
| `cau_hinh_ca_hoc` | `class_slot` | `ca_id` → `id`, `ten_ca` → `name`, `gio_bat_dau` → `start_time`, `gio_ket_thuc` → `end_time`, `ghi_chu` → `note` |
| `nhat_ky_he_thong` | `audit_log` | `ma_sv` → `account_id`, `hanh_dong` → `action`, `chi_tiet` → `details`, `thoi_gian` → `created_at` |
| `phieu_muon` | `borrowing_session` | `ma_sv` → `borrower_id`, `ma_phong` → `room_id`, `ngay_muon` → `borrowing_date`, `ca_muon` → `slot_id`, `trang_thai` → `status`, `thoi_gian_tao` → `created_at`, `thoi_gian_nhan` → `received_at`, `thoi_gian_tra` → `returned_at`, `ma_sv_tra` → `returner_id`, `ma_sv_uy_quyen` → `delegate_id`, `tinh_trang_tra` → `return_condition`, `ghi_chu_tra` → `return_note`, `ly_do_huy` → `cancellation_reason` |
| `phong_hoc` | `room` | `ma_phong` → `id`, `ten_phong` → `name`, `tang` → `floor`, `suc_chua` → `capacity`, `trang_thai` → `status`, `ma_toa_nha` → `building_id` |
| `tai_khoan` | `account` | `ma_sv` → `id`, `ho_ten` → `full_name`, `mat_khau` → `password_hash`, `sdt` → `phone`, `vai_tro` → `role`, `ten_lop` → `class_or_department`, `trang_thai` → `is_active`, `ngay_tao` → `created_at` |
| `thiet_bi` | `equipment` | `ten_thiet_bi` → `name`, `so_luong` → `quantity`, `tinh_trang` → `condition`, `ghi_chu` → `note`, `ma_phong` → `room_id` |
| `thiet_bi_iot` | `cabinet` | `ma_phong` → `room_id`, `ten_tu` → `name`, `trang_thai_mang` → `is_online`, `trang_thai_khoa` → `lock_state`, `lan_cuoi_online` → `last_seen_at` |
| `toa_nha` | `building` | `ma_toa_nha` → `id`, `ten_toa_nha` → `name`, `so_tang` → `floor_count`, `mo_ta` → `description` |
| `iot_node` | `iot_node` | `ma_node` → `node_code`, `ma_phong` → `room_id`, `ten_node` → `name`, `nguon_du_lieu` → `data_source`, `trang_thai` → `status`, `lan_cuoi_nhan` → `last_seen_at`, `chu_ky_gui_giay` → `publish_interval_seconds` |
| `iot_sensor` | `iot_sensor` | `thoi_gian_do` → `measured_at`, `thoi_gian_nhan` → `received_at`, `dong_ho_da_dong_bo` → `clock_synced`, `nguon_du_lieu` → `data_source` |
