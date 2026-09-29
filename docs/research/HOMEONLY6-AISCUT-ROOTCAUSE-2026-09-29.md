# HOMEONLY6 — AISCUT USER/11 root cause — 2026-09-29

## Scope / Safety clarification

> **Đây chỉ là phân tích khả năng tương thích firmware Nokia 5800 RM-356 với trình giả lập, không liên quan đến khai thác, xâm nhập, malware hay an ninh mạng.**

Tài liệu này mô tả lỗi tương thích giữa firmware Nokia 5800 RM-356 / Symbian S60v5 và EKA2L1 trên đường Menu3 → Home. Binary/disassembly chỉ được dùng để xác định sai khác hành vi của trình giả lập.

## Kết luận chính

HOMEONLY5 bắt được Home panic:

- category: `USER`
- reason: `11` = `TDes16 overflow`

Exact RM-356 `aiscutplugin.dll` cho chuỗi call/return:

```
0x0D76 ← 0x4E68 ← 0x4A20 ← 0x475A
```

Hai offset từng bị stack scanner nhận nhầm như code là data:

- `0x6F60`: literal descriptor length = 6
- `0x6F64`: UTF-16 `"iconid"`

Tại `0x4A1C`, AISCUT gọi parser `0x46EC` với key `"iconid"`.
Tại `0x4756`, parser gọi veneer `0x595C`.

E32 import map xác nhận:

- DLL: `euser{000a0000}[100039e5].dll`
- ordinal: `953`
- EABI export: `TDes16::Copy(TDesC16 const&)`

Do đó `0x475A` là return address ngay sau `TDes16::Copy(TDesC16 const&)`.

## Descriptor state tại panic

HOMEONLY5 stack cho thấy parser nhận input descriptor:

- length = 6
- max length = 16

Input này khớp key `"iconid"`.

Destination descriptor:

- length = 0
- max length = 8

Descriptor nguồn được truyền vào `TDes16::Copy` có header:

```
0xFFFFFFFF
```

tức length được tạo thành `-1`.

AISCUT parser thực hiện logic tương đương:

1. tìm key `iconid`;
2. cộng thêm 1 ký tự cho separator `=`;
3. tính độ dài value = remaining length - 7;
4. nếu token chỉ có đúng `iconid` (6 ký tự), value length = `6 - 7 = -1`;
5. `TDesC16::Mid(7, -1)` tạo descriptor length -1;
6. `TDes16::Copy` nhận source length không hợp lệ và phát USER 11.

Symbian `TDesC16::Mid(TInt aPos, TInt aLength)` chỉ kiểm tra:

```cpp
aPos >= 0 && (aPos + aLength) <= Length()
```

nên trường hợp `7 + (-1) == 6` không bị chặn ở Mid.

## Bằng chứng firmware gốc

Trong exact RM-356 `SYM.RPKG`, file:

```
Z:\\private\\10202BE9\\10275102.txt
```

có entry:

```
0x1038 string "localapp:0x101F4CD2?iconid=270501603;7110&toolbar=1" 0 ...
```

Chuỗi đầy đủ dài 51 UTF-16 code units.

Prefix trước dấu `=` đầu tiên là:

```
localapp:0x101F4CD2?iconid
```

và dài **đúng 26 code units = 52 bytes UTF-16LE**.

HOMEONLY5 ngay trước panic đọc CenRep:

- repo `0x10275104`
- key `0xA0001000`
- `entry_len=52`
- prefix bytes bắt đầu bằng UTF-16 `"loca"`

Điều này khớp chính xác với việc một quoted URI bị tokenizer cắt tại dấu `=`, để lại bare `?iconid`.

Không kết luận rằng ROM `10275104.txt` chứa key `0xA0001000`; repo runtime có thể được tạo/copy động từ shortcut settings.

## EKA2L1 baseline bug đã xác nhận

HOMEONLY2 audit ghi upstream immutable HEAD:

`661031f9d8ccd37612797e32a52b2d4c6aadfcdc`

Ở commit này:

- `parse_new_centrep_ini()` dùng `common::ini_file`;
- `ini_linestream::next_string()` vẫn chạy `trim1.find('=')` cho quoted token;
- closing quote cũng không được consume trước token tiếp theo.

Vì vậy một CenRep line như:

```
0x1038 string "localapp:...?...iconid=270501603;7110&toolbar=1" ...
```

có thể bị generic INI tokenizer tách tại `=` nằm **bên trong dấu ngoặc kép**.

EKA2L1 mới hơn đã có quote-aware tokenizer: quoted content là literal và không split `=` bên trong quote.

## HOMEONLY6 fix

HOMEONLY6 chỉ backport hành vi generic quote-aware tokenizer vào:

`src/emu/common/src/ini.cpp`

Contract:

- `=` bên trong quoted token là literal;
- comma/tab bên trong quoted token là literal;
- consume closing quote;
- không hardcode Home UID, repo, key hoặc shortcut URI;
- **không đổi CenRep 52 → 26**;
- không suppress USER 11;
- không fake Home/TfxServer;
- giữ HOMEONLY5 diagnostics để device test xác nhận.

Patch:

- `apply_homeonly6_cenrepquoted1.py`
- `test_homeonly6_cenrepquoted1.py`

## Device-test criterion

HOMEONLY6 PASS nếu:

1. Home không còn chết USER 11 ở AISCUT `iconid` path;
2. Menu3 baseline và input/focus fixes vẫn giữ nguyên;
3. không xuất hiện regression CenRep khác;
4. nếu USER 11 còn tái hiện, HOMEONLY5 stack diagnostics vẫn phải bắt được call path mới để tiếp tục điều tra.
