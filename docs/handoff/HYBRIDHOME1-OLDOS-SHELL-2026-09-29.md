# HYBRIDHOME1 — OldOS-style S60 Hybrid Home

**Ngày:** 2026-09-29  
**Nhánh nghiên cứu:** `codex/hybridhome1-oldos-shell`

## Mục tiêu

Chứng minh kiến trúc mới:

```
MENUUI36 / Menu3 thật
        ↓
Hybrid Home do host iOS dựng
        ↓
EKA2L1 app registry thật
        ↓
launch_app(uid) thật
        ↓
ứng dụng Symbian thật
```

HYBRIDHOME1 **không khởi chạy** Nokia Home UID `0x102750F0`. Vì vậy prototype không phụ thuộc vào AISCUT, WidgetRegistry, MMF startup chain hay các plugin của Home thật.

## Baseline bắt buộc

- HOMEONLY2 / MENUUI36 WINFOCUS1
- MENUUI35 async input
- MENUUI33 key sound
- MENUUI31 raw pen input
- MENUUI30 stock FEP
- MANIC3
- NOJAVA
- không NativeBoot / CompatBoot

Menu3 UID: `0x101F4CD2`.

## HYBRIDHOME1

Khi Menu3 đang chạy, menu EKA2L1 có thêm:

**Hybrid Home (thử nghiệm)**

Chọn mục này:

1. Menu3 vẫn chạy bên dưới.
2. iOS frontend dựng một Home tối giản bằng UIKit.
3. Input guest bị chặn trong lúc Hybrid Home đang hiển thị.
4. Nút **Trở về Menu3 thật** chỉ gỡ overlay; không reboot emulator.
5. Nút **Ứng dụng Symbian thật** đọc `bridge::get_apps()`.
6. Danh sách loại Menu3 và Home thật để tránh quay lại startup chain đang nghiên cứu.
7. Chọn ứng dụng gọi `launchAppUid(uid)` → `bridge::launch_app(uid)` → launcher EKA2L1 thật.

## Marker cần thấy

- `[HYBRIDHOME1][TRIGGER]`
- `[HYBRIDHOME1][SHOW]`
- `[HYBRIDHOME1][RETURN_MENU3]`
- `[HYBRIDHOME1][APP_CHOOSER]`
- `[HYBRIDHOME1][LAUNCH_REAL_APP]`

## PASS đầu tiên

PASS kiến trúc khi thiết bị chứng minh được:

```
Menu3 thật
 → Hybrid Home hiện
 → trở về Menu3 được
 → Hybrid Home hiện lại
 → danh sách app thật mở
 → chọn 1 app
 → app Symbian thật chạy
```

Không yêu cầu giao diện đẹp ở HYBRIDHOME1. Theme/icon/resource RM-356 sẽ làm ở HYBRIDHOME2/3 sau khi đường launch được chứng minh.

## Tách biệt với HOMEONLY

Nhánh này không thay thế HOMEONLY7/8/9. HOMEONLY tiếp tục nghiên cứu Home thật. HYBRIDHOME là đường kiến trúc song song để đạt một S60 usable shell nhanh hơn.
