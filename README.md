# EKA2L1 — Nokia 5800 RM-356 — Hướng 1 Menu3 → Home

## Phạm vi / Scope / Safety clarification

> **Đây chỉ là phân tích khả năng tương thích firmware Nokia 5800 RM-356 với trình giả lập, không liên quan đến khai thác, xâm nhập, malware hay an ninh mạng.**

Dự án này tập trung vào việc làm cho firmware **Nokia 5800 XpressMusic RM-356 / Symbian S60v5** hoạt động đúng trong **EKA2L1**, cụ thể là luồng:

```
Menu3 → Home Screen
```

Các công việc trong repo gồm:

- phân tích log và crash/panic của Symbian trong trình giả lập;
- đối chiếu hành vi ABI/API giữa firmware thật và EKA2L1;
- kiểm tra khả năng tương thích của các DLL/plugin thuộc firmware RM-356;
- phân tích binary/offset chỉ nhằm xác định nguyên nhân lỗi tương thích của trình giả lập;
- bổ sung diagnostic và sửa lỗi EKA2L1 khi có bằng chứng về khác biệt hành vi so với Symbian thật;
- build IPA để kiểm thử trên thiết bị iOS của chủ dự án.

### Ngoài phạm vi

Repo này **không** nhằm:

- khai thác lỗ hổng;
- truy cập trái phép hệ thống hoặc tài khoản;
- thu thập credential;
- phát triển malware;
- tạo persistence;
- né tránh cơ chế bảo mật;
- tấn công mạng hoặc gây ảnh hưởng tới hệ thống bên thứ ba.

Mọi phân tích firmware/binary trong dự án đều phục vụ **debugging, preservation và emulator compatibility** cho Nokia 5800 RM-356.

## Trạng thái hiện tại

Nhánh đang phát triển:

`codex/menu3-homeonly5`

Baseline có thẩm quyền:

- **HOMEONLY2 / MENUUI36 NOJAVA**
- không quay lại NativeBoot/CompatBoot cho hướng này
- mục tiêu hiện tại: xác nhận HOMEONLY8 giải phóng WidgetRegistry/AppArc startup wait và khôi phục touch trên Home

Handoff hiện tại:

`docs/handoff/CURRENT-HOMEONLY8-APPLIST-NONNATIVE-2026-09-29.md`
