# NEW CHAT HANDOFF — HOMEONLY7 CENREPQUOTED1

**Ngày:** 2026-09-29  
**Dự án:** Hướng 1 — Menu3 → Home Screen  
**Repo nguồn:** `phai-nguyen/Eka2l1-nhanh-menuu3`  
**Nhánh hiện tại:** `codex/menu3-homeonly7-cenrepquoted1`  
**Build host:** `phai-nguyen/Eka2l1_bot_menu_simbiam` / `codex/m3home-homeonly2-build`

> Đây là mốc tiếp theo sau `NEWCHAT-HOMEONLY5-AISCUT-2026-09-29.md`.  
> Không quay lại NativeBoot/CompatBoot/DirectHome.  
> Không sửa CenRep 52→26.  
> Không suppress USER/11.

---

# 1. BASELINE BẤT BIẾN

- HOMEONLY2 / MENUUI36 WINFOCUS1 + NOJAVA + MANIC3 là baseline đúng.
- Menu3 UID: `0x101F4CD2`.
- Home UID: `0x102750F0`.
- Firmware: Nokia 5800 RM-356 v60.0.003, không đổi.
- HOMEONLY3: giữ Menu3/emulator sống sau khi Home exit.
- HOMEONLY4: event/request-semaphore diagnostics.
- HOMEONLY5: USER/11 register/stack/module diagnostics.
- NativeBoot/CompatBoot/J2ME phải vắng mặt.

# 2. ROOT CAUSE ĐÃ XÁC ĐỊNH

HOMEONLY5 panic:

- category `USER`
- reason `11` = `ETDes16Overflow`
- ngay trước panic:
  - repo `0x10275104`
  - key `0xA0001000`
  - `entry_len=52` bytes
  - GetString status 0

Exact RM-356 `aiscutplugin.dll`:

- size: 25,468
- SHA-256: `82bc75a917de8fda87a41fc49894c1928a075af99a6a89f1fa7ec61352be0221`

Reverse engineering:

- `+0x6F60/+0x6F64` là static descriptor/literal `"iconid"`, không phải code frame.
- `+0x475A` là return address ngay sau `TDes16::Copy(const TDesC16&)`.
- euser ordinal: 953.
- `+0x4A20` là return address sau helper parse field `iconid`.
- `+0x4E68` nằm trong đường parse URI/query metadata.
- `+0x0D76` là outer AISCUT caller.

Stack cho lần parse `iconid` cho thấy query descriptor có Length=6, chính xác `"iconid"`, còn destination MaxLength=8.

Exact RM-356 CenRep source có shortcut:

```
localapp:0x101F4CD2?iconid=270501603;7110&toolbar=1
```

- 51 UTF-16 code units
- 102 bytes UTF-16LE
- 26 ký tự đầu chính xác là:
  `localapp:0x101F4CD2?iconid`
- prefix này dài đúng 52 bytes.

Do đó runtime 52-byte value là chuỗi bị cắt tại dấu `=` đầu tiên bên trong quoted CenRep string.

# 3. BUG THẬT TRONG EKA2L1

Tokenizer INI cũ trong `src/emu/common/src/ini.cpp`:

- đọc quoted token;
- sau đó vẫn chạy `trim1.find('=')`;
- split quoted token tại dấu `=`.

Kết quả:

```
"localapp:0x101F4CD2?iconid=270501603;7110&toolbar=1"
```

bị biến thành:

```
localapp:0x101F4CD2?iconid
```

AISCUT sau đó lấy query `iconid` không có `=`/value, tính độ dài value âm và cuối cùng đi vào `TDes16::Copy`, gây USER/11 overflow.

Đây là bug parser generic của emulator, không phải lỗi ABI TDes16 của CenRep.

# 4. HOMEONLY7 FIX

Source commits:

- runtime fix: `2f54cf599b5fd7f138768b77cc33edbac76eeae3`
- regression gates: `fb2f19156273efe971e324b09a3d6817f0ed61f9`
- branch latest có docs/safety-only sau build: `5be056374cffe2fc32df30e12855cfc0f94b5285`

Files:

- `apply_homeonly7_cenrepquoted1.py`
- `test_homeonly7_cenrepquoted1.py`

Fix chỉ backport tokenizer quoted-token behavior hiện có trên upstream EKA2L1:

- token nhớ trạng thái `quoted`;
- `=`, comma và tab bên trong quote là literal data;
- không key=value split quoted token;
- consume closing quote đúng;
- giữ empty quoted values.

Không thay đổi:

- CenRep Get/Set byte-length ABI;
- firmware;
- AISCUT binary;
- Home code;
- input/focus/scheduler;
- panic handling;
- repository key cụ thể.

# 5. UPSTREAM CROSS-CHECK

Current `EKA2L1/EKA2L1` master đã có cùng semantic fix trong `src/emu/common/src/ini.cpp`:

- `struct ini_token { text, quoted }`
- `std::deque<ini_token>`
- quoted token không split `=`
- empty quoted token được giữ.

Vì vậy HOMEONLY7 là backport một generic upstream behavior, không phải workaround riêng RM-356.

# 6. BUILD HOMEONLY7

Build host commit:

`ac189d90ace6874823a6601df216fc421b1cb2c6`

Actions run:

`36564131999`

Result:

**GREEN**

Tất cả bước đều PASS:

- restore HOMEONLY5 cache
- baseline/old-tokenizer authority gates
- fetch HOMEONLY7 source
- apply fix + contract test
- incremental compile
- binary invariants
- package IPA
- upload IPA
- upload audit

Build-time source HEAD:

`fb2f19156273efe971e324b09a3d6817f0ed61f9`

Contract output:

- `HOMEONLY7 CENREPQUOTED1 contract: PASS`
- `rm356_1038_expected_bytes=102`

IPA:

`EKA2L1-HOMEONLY7-CENREPQUOTED1-unsigned.ipa`

IPA SHA-256:

`7a73c76a1446c4c0e541ab8d837f7c87bbdc1f672b01e014c80f886b68a6ebf4`

Artifacts:

- IPA artifact ID: `11031671131`
- AUDIT artifact ID: `11031141639`
- expires: 2026-10-13

Run URL:

https://github.com/phai-nguyen/Eka2l1_bot_menu_simbiam/actions/runs/36564131999

Cache:

`eka2l1-homeonly7-cenrepquoted1-macos15-v1`

# 7. PERSISTENCE CAVEAT — QUAN TRỌNG CHO DEVICE TEST

Central Repository loader ưu tiên:

1. device-specific persisted `.CRE`
2. global persisted `.CRE`
3. ROM/default `.TXT`

trước khi fallback sang ROM TXT.

HOMEONLY5 đã có malformed 52-byte value trong runtime/persist state. Vì vậy:

- cài đè HOMEONLY7 lên app data cũ có thể vẫn load stale malformed `.CRE`;
- nếu cài đè vẫn USER/11 thì chưa thể kết luận HOMEONLY7 fix sai;
- lượt xác nhận root fix phải dùng state CenRep sạch để buộc parser mới đọc RM-356 TXT đầy đủ.

# 8. DEVICE TEST ƯU TIÊN

## Test A — authoritative clean-state validation

1. Xóa app EKA2L1 test hiện tại.
2. Cài HOMEONLY7.
3. Cài/import lại đúng firmware Nokia 5800 RM-356 v60.0.003.
4. Mở Menu3.
5. Chọn **Vào màn hình chính**.
6. Không chạm Home trong 15–20 giây đầu.
7. Nếu Home còn sống, thử lần lượt:
   - **Telephone**
   - quay lại Home
   - **Contacts**
   - quay lại Home
   - **Set up e-mail**
8. Xuất 4 log EKA2L1.
9. Video hữu ích nhưng log là bắt buộc.

PASS chính:

- không còn Home USER/11 tại AISCUT `TDes16::Copy`;
- Home giữ focus và sống;
- touch thật được Home nhận, không phải Menu3 dưới stale framebuffer.

## Test B — optional overlay/stale-state behavior

Sau khi Test A PASS mới cần đánh giá migration/cài đè. Không dùng kết quả cài đè trên malformed state cũ để phủ nhận parser fix.

# 9. HOMEONLY6

HOMEONLY6 diagnostic vẫn có giá trị tham chiếu:

- run `36560417642`: GREEN
- IPA SHA-256:
  `ab49e0b96108b3c8280b558f5265dd8871a34cc2229b11595936985a4488995f`
- markers:
  - `[HOMEONLY6][CEN_SHORTCUT_VALUE]`
  - `[HOMEONLY6][DESC_SCAN]`

Nhưng HOMEONLY7 root cause đã được chốt bằng exact firmware + exact AISCUT disassembly + runtime HOMEONLY5 + upstream tokenizer parity; không bắt buộc phải device-test HOMEONLY6 trước HOMEONLY7.

# 10. KHÔNG LÀM

- Không đổi CenRep 52→26.
- Không hardcode key `0xA0001000`.
- Không truncate URI thủ công.
- Không sửa `aiscutplugin.dll`.
- Không suppress USER/11.
- Không quay lại NativeBoot/CompatBoot/DirectHome.
- Không đổi firmware.
