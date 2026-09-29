# CURRENT HANDOFF — HOMEONLY7 CENREPQUOTED1 — 2026-09-29

## Scope / Safety clarification

> **Đây chỉ là phân tích khả năng tương thích firmware Nokia 5800 RM-356 với trình giả lập, không liên quan đến khai thác, xâm nhập, malware hay an ninh mạng.**

Dự án: Hướng 1 — Menu3 → Home Screen  
Repo nghiên cứu: `phai-nguyen/Eka2l1-nhanh-menuu3`  
Baseline semantic: **HOMEONLY2 / MENUUI36 NOJAVA / MANIC3**  
Không quay lại NativeBoot/CompatBoot.  
Không đổi CenRep `52 → 26`.

---

## 1. Trạng thái được khôi phục sau HANDOFF HOMEONLY5

HANDOFF cũ `NEWCHAT-HOMEONLY5-AISCUT-2026-09-29.md` bị dừng trước một số run đã thực hiện cùng ngày.

Các run tiếp theo đã tồn tại:

1. HOMEONLY6 Shortcut Value Probe
   - run `36557523872`
   - GREEN

2. HOMEONLY6 Shortcut Descriptor Probe
   - run `36560417642`
   - GREEN

3. HOMEONLY7 CenRep Quoted Token Fix
   - run `36564131999`
   - GREEN
   - build host HEAD `ac189d90ace6874823a6601df216fc421b1cb2c6`

HOMEONLY7 là bản production-test candidate hiện tại.

---

## 2. Root cause đã xác định

HOMEONLY5 USER/11 = **TDes16 overflow**.

Exact RM-356 `aiscutplugin.dll` cho return chain:

```
0x0D76 ← 0x4E68 ← 0x4A20 ← 0x475A
```

- `0x6F60` = descriptor length 6
- `0x6F64` = UTF-16 `"iconid"`
- `0x475A` = return sau `TDes16::Copy(TDesC16 const&)`
- import: `euser{000a0000}[100039e5].dll`, EABI ordinal 953

HOMEONLY5 stack cho thấy source descriptor đi vào Copy có header `0xFFFFFFFF`, tức length `-1`.

AISCUT nhận bare token `iconid` (6 chars), tính value start sau `iconid=` (7 chars), sinh sub-length `6 - 7 = -1`, rồi cuối cùng `TDes16::Copy` phát USER 11.

---

## 3. Tại sao AISCUT nhận bare iconid

Exact RM-356 `SYM.RPKG` chứa:

`Z:\\private\\10202BE9\\10275102.txt`

với entry:

```
0x1038 string "localapp:0x101F4CD2?iconid=270501603;7110&toolbar=1" 0 ...
```

Chuỗi đầy đủ dài 51 UTF-16 code units = 102 bytes.

Prefix trước dấu `=` đầu tiên:

```
localapp:0x101F4CD2?iconid
```

dài đúng 26 UTF-16 code units = **52 bytes**.

HOMEONLY5 ngay trước panic đọc runtime CenRep:

- repo `0x10275104`
- key `0xA0001000`
- `entry_len=52`
- đầu chuỗi UTF-16 là `loca...`

Đây khớp chính xác với prefix bị cắt tại dấu `=`.

Không suy diễn rằng ROM `10275104.txt` chứa sẵn key `0xA0001000`; runtime repo/key có thể được guest tạo/copy động.

---

## 4. Lỗi tương thích EKA2L1 baseline

HOMEONLY2 audit xác nhận immutable EKA2L1 upstream HEAD:

`661031f9d8ccd37612797e32a52b2d4c6aadfcdc`

Ở baseline này:

- `parse_new_centrep_ini()` dùng `common::ini_file`;
- `ini_linestream` không giữ trạng thái quoted khi split `=`;
- `trim1.find('=')` chạy cả với quoted string;
- closing quote không được consume đúng.

Do đó `=` nằm trong shortcut URI quoted bị hiểu sai thành separator INI.

EKA2L1 mới hơn đã sửa generic tokenizer để quoted token là literal.

---

## 5. HOMEONLY7 fix

Workflow:

`.github/workflows/build-homeonly7-cenrepquoted1.yml`

Build host:

`phai-nguyen/Eka2l1_bot_menu_simbiam`

Run:

`36564131999`

Fix:

- backport quote-aware generic INI tokenizer;
- `=`, comma, tab trong quoted token là literal;
- consume closing quote;
- không hardcode Home UID/repo/key/URI;
- không sửa CenRep byte/UTF-16 ABI;
- không suppress panic;
- không sửa `aiscutplugin.dll`;
- giữ HOMEONLY5 diagnostics;
- NOJAVA;
- NativeBoot/CompatBoot absent.

Artifact:

`EKA2L1-HOMEONLY7-CENREPQUOTED1-unsigned.ipa`

SHA-256:

`7a73c76a1446c4c0e541ab8d837f7c87bbdc1f672b01e014c80f886b68a6ebf4`

Artifact ID:

`11031671131`

---

## 6. Device test tiếp theo

Ưu tiên **clean install** để tránh persisted CenRep value 52-byte đã được tạo từ tokenizer lỗi trước đó.

Test:

1. gỡ app/build test cũ nếu cần giữ test clean;
2. cài HOMEONLY7;
3. cài firmware RM-356 chuẩn như baseline;
4. mở Menu3;
5. chọn **Vào màn hình chính**;
6. chờ Home khoảng 1–2 phút;
7. thử chạm Telephone/Contacts và vùng Home;
8. gửi `EKA2L1_TakeThis.log`, `EKA2L1.log`, Persistent/Persistent-prev và video nếu hành vi khác.

PASS quan trọng nhất:

- không còn `USER 11` tại AISCUT iconid path;
- Home thread còn sống;
- touch thực sự được Home nhận, không phải stale framebuffer/Menu3.

Nếu USER 11 còn tái hiện, HOMEONLY5 stack markers vẫn còn trong binary để bắt call path mới.

---

## 7. Không lặp lại các hướng đã loại

- không sửa CenRep server 52→26;
- không suppress USER 11;
- không hardcode `0x10275104 / 0xA0001000` làm fix;
- không quay lại NativeBoot/CompatBoot;
- không fake TfxServer/Home;
- không đổi firmware.

Research chi tiết:

`docs/research/HOMEONLY6-AISCUT-ROOTCAUSE-2026-09-29.md`
