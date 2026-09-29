# ⚠️ SUPERSEDED / ĐÃ CÓ HANDOFF MỚI

Trạng thái hiện tại đã tiến tới HOMEONLY7. Tiếp tục từ:

`docs/handoff/CURRENT-HOMEONLY7-CENREPQUOTED-2026-09-29.md`

HANDOFF bên dưới được giữ làm lịch sử HOMEONLY5/AISCUT và không còn là điểm bắt đầu mới nhất.

---

# NEW CHAT HANDOFF — HOMEONLY5 → AISCUT USER/11

**Ngày:** 2026-09-29  
**Dự án:** Hướng 1 — Menu3 → Home Screen  
**Repo nguồn:** `phai-nguyen/Eka2l1-nhanh-menuu3`  
**Nhánh hiện tại:** `codex/menu3-homeonly5`  
**Build host:** `phai-nguyen/Eka2l1_bot_menu_simbiam` / `codex/m3home-homeonly2-build`

> Đây là HANDOFF có thẩm quyền cho chat tiếp theo.  
> Không quay lại NativeBoot/CompatBoot/DirectHome trừ khi người dùng yêu cầu rõ ràng.

---

# 0. PHẠM VI / SCOPE / SAFETY CLARIFICATION

> **Đây chỉ là phân tích khả năng tương thích firmware Nokia 5800 RM-356 với trình giả lập, không liên quan đến khai thác, xâm nhập, malware hay an ninh mạng.**

Toàn bộ công việc trong HANDOFF này thuộc phạm vi **emulator compatibility / debugging / preservation** cho Nokia 5800 RM-356 và EKA2L1.

Các thuật ngữ như `binary analysis`, `reverse-engineering`, `disassembly`, `offset`, `stack trace`, `ABI`, `panic` hoặc `DLL/plugin analysis` trong tài liệu này chỉ được dùng để:

- xác định nguyên nhân firmware Symbian hoạt động khác trên EKA2L1 so với thiết bị thật;
- đối chiếu ABI/API và hành vi runtime;
- sửa lỗi hoặc bổ sung diagnostic cho trình giả lập;
- kiểm thử luồng Menu3 → Home Screen trên firmware RM-356 do chủ dự án cung cấp.

**Ngoài phạm vi:** khai thác lỗ hổng, truy cập trái phép, credential theft, malware, persistence, bypass bảo mật, tấn công mạng hoặc gây ảnh hưởng tới hệ thống bên thứ ba.

---

# 1. MỤC TIÊU HIỆN TẠI

Mục tiêu là chạy **Home Screen thật của Nokia 5800 RM-356 / S60v5** bên trong EKA2L1 bằng đường HLE/normal mode đã ổn định:

```
normal EKA2L1
   ↓
Menu3 UID 0x101F4CD2
   ↓
iOS launcher hiện có
   ↓
Home Screen thật UID 0x102750F0
```

Ưu tiên hiện tại:

1. Giữ baseline Menu3 đã test ổn định.
2. Giữ Java/J2ME bị gỡ.
3. Không dùng NativeBoot/CompatBoot.
4. Không fake TfxServer/IPC.
5. Không đổi firmware.
6. Không suppress panic chỉ để làm Home “có vẻ chạy”.
7. Sửa lỗi tổng quát/ABI thật nếu tìm được nguyên nhân.
8. Giữ Menu3 sống bên dưới Home để chẩn đoán/khôi phục.

---

# 2. MÔI TRƯỜNG TEST CỦA NGƯỜI DÙNG

- iPhone 12 Pro Max
- iOS 18.7
- Windows 7 64-bit, RAM 2 GB
- không có Mac
- firmware Nokia 5800 XpressMusic RM-356 v60.0.003
- UI firmware có tiếng Việt
- người dùng không dùng tiếng Anh: hướng dẫn test phải viết bằng tiếng Việt

Firmware chuẩn đang dùng:

- `SYM.ROM`
  - size: 41,283,584
  - SHA256: `b4328dfa555d73e14a4bab2de46bbec702970e4b63c8ce878da589fa6b64c444`
- `SYM.RPKG`
  - size: 134,540,934
  - SHA256: `bc41496abc8d4c87de976b65cadfb922b4dfd9583a0dbcf35b7e4bff23eb008f`

Library/firmware package historically: `5800 (S60v5).zip`.

---

# 3. GOLDEN BASELINE — HOMEONLY2

## HOMEONLY1 là baseline sai và đã bỏ

HOMEONLY1 từng được dựng từ MENUUI14. Device test cho thấy Menu3 quay lại lỗi cảm ứng và user nhắc rằng Java đã được gỡ ở các bản mới hơn.

**Không dùng HOMEONLY1 nữa.**

## Baseline chính xác là MENUUI36

HOMEONLY2 được dựng lại từ **MENUUI36 WINFOCUS1 + NOJAVA + MANIC3**, tức mốc MenuUI cuối cùng trước NativeBoot.

Các thành phần bắt buộc phải giữ:

- MENUUI36 WINFOCUS1
- MENUUI35 async simulate input
- MENUUI33 key sound
- MENUUI31 raw pen input
- MENUUI30 Stock FEP
- MANIC3
- `src/emu/j2me` không tồn tại
- Java/J2ME binary marker không tồn tại

NativeBoot/CompatBoot cũng phải hoàn toàn vắng mặt.

HOMEONLY2 build:

- run: `36544190013`
- IPA SHA256:
  `f9da544ad1b105789909a89bcf02580e4b140217d676b1e218b68c05f283e360`
- clean cache:
  `eka2l1-homeonly2-clean-menuui36-nojava-manic3-macos15-v1`

**Đây vẫn là semantic baseline có thẩm quyền.**

---

# 4. MENU3 → HOME BRIDGE

M3HOME1:

- Menu3 UID: `0x101F4CD2`
- Home UID: `0x102750F0`
- menu option: **Vào màn hình chính**
- marker:
  - `[M3HOME1][TRIGGER]`
  - `[M3HOME1][APPARC_REQUEST]`
  - `[M3HOME1][APPARC_DISPATCHED]`

Tên marker APPARC là legacy; đường thật là launcher HLE/iOS đang có, không phải native AppArc.

Home thật đã render được:

- wallpaper Nokia
- status bar
- “Set up e-mail”
- softkey Telephone / Contacts
- WindowServer group/focus thật của Home

TfxServer không cần thiết để Home render trên đường này.

---

# 5. CENREP FIXES ĐÃ GIỮ

M3HOME2/HOMEONLY baseline đã thêm:

## transaction support

- CenRep transaction-local changes
- commit persist một lần

## DeleteRange opcode 0x21 / decimal 33

Generic matching:

```
(key & mask) == (partialKey & mask)
```

Không hardcode Home key.

## GetString diagnostic

Marker:

- `[HOMEONLY1][CEN_GET_STRING] phase=pre_write`
- `[HOMEONLY1][CEN_GET_STRING] phase=complete`

Marker vẫn mang tên HOMEONLY1 do tái sử dụng patch; không có nghĩa baseline là HOMEONLY1.

---

# 6. HOMEONLY3 — POST-EXIT CONTAINMENT

HOMEONLY3 thay đổi host lifecycle sau khi Home chết:

Nếu `currentGameUid == 0x102750F0`:

- không gọi `exitGame()`
- không reboot toàn emulator
- giữ Menu3/emulator session sống
- restore host bookkeeping về Menu3 UID `0x101F4CD2`

Marker:

`[HOMEONLY3][HOME_EXIT_KEEP_MENU3]`

Quan trọng:

- HOMEONLY3 **không bypass panic Home**
- không sửa CenRep
- không sửa guest/kernel semantics trước panic

Build:

- run `36546587496`
- SHA256:
  `721647d2963f30e3d6ba0c0f8f98dd6329041a08f3c31949c81d6c6842db582b`
- cache:
  `eka2l1-homeonly3-keepmenu3-macos15-v1`

## Đính chính video HOMEONLY2/HOMEONLY3

User đã xác nhận:

```
Menu3 → Home hiện → EKA2L1 về danh sách app → user tự vuốt về iOS Home
```

Đoạn iOS Home **không phải app crash**.

Không được ghi lại kết luận sai rằng EKA2L1 tự crash ra iOS Home trong test này.

---

# 7. HOMEONLY4 — EVENT WAKE PROBE

HOMEONLY4 thêm diagnostics, không đổi semantics:

- `[HOMEONLY4][EVENT_WAKE]`
- `[HOMEONLY4][SEMA_WAKE]`
- `[HOMEONLY4][REQ_WAIT]`

Mục đích ban đầu: trace EventReady → RequestStatus → request semaphore → Home thread wake.

Build:

- run `36549741084`
- SHA256:
  `202825a53cc35ce4526d05efb194765ac34ad1565488999b7ef96e9efbe95ef6`
- cache:
  `eka2l1-homeonly4-eventwakeprobe-macos15-v1`

## Đính chính quan trọng từ device log

Ảnh/video từng trông như cảm ứng Home đã nhận:

- user bấm vùng Telephone
- hiện menu “Show open apps / Change Menu view / Organise…”

Log chứng minh đó **không phải Home xử lý touch**.

Chuỗi thật:

1. Home UID `0x102750F0` render.
2. Home panic `USER / 11`.
3. HOMEONLY3 giữ framebuffer cuối của Home trên màn hình.
4. focus WindowServer quay về group 2 của Menu3.
5. user chạm vào framebuffer Home đang stale.
6. touch được giao cho Menu3 thread/group.
7. Menu3 mở menu Options phủ lên hình Home stale.

Vì vậy:

**Touch Home chưa được chứng minh hoạt động.**

Không tiếp tục sửa coordinate/hit-test dựa trên ảnh menu đó.

---

# 8. HOMEONLY5 — USER/11 STACK TRACE

HOMEONLY5 thêm diagnostic tại `thread_kill` cho đúng:

- process UID3 `0x102750F0`
- category `USER`
- reason `11`
- exit type panic

Marker:

- `[HOMEONLY5][USER11_CONTEXT]`
- `[HOMEONLY5][USER11_FRAME]`
- `[HOMEONLY5][USER11_STACK]`
- `[HOMEONLY5][USER11_STACK_END]`

Capture:

- PC / LR / SP / CPSR
- r0-r12
- request_count
- 64 stack words / 256 bytes
- map addresses to loaded module + offset

Không suppress panic.

Build:

- workflow run: `36553079575`
- rerun sau khi sửa source gate: GREEN
- IPA artifact ID: `11024594554`
- AUDIT artifact ID: `11025606850`
- IPA:
  `EKA2L1-HOMEONLY5-USER11STACK-unsigned.ipa`
- SHA256:
  `0b7737d9f3e38403dc52698c15f506e142674b6e8066f347a41a6e32ab25391b`
- cache:
  `eka2l1-homeonly5-user11stack-macos15-v1`

Source branch hiện tại:

`codex/menu3-homeonly5`

Source HEAD trước HANDOFF này:

`6c0b1f552512876fa402fd5423a76e6133086fa0`

---

# 9. HOMEONLY5 DEVICE RUN #1 — HOME SỐNG > 1 PHÚT

Lần test HOMEONLY5 đầu tiên:

- Home launch khoảng `17:18:08.705`
- Home focus group 30
- Home thread UID 611
- không USER 11
- không HOMEONLY5 stack marker vì không có panic
- đến khoảng `17:19:27.607`, Home thread vẫn còn sống/wake

THREADKILL duy nhất là AknIconPrecache2 exit bình thường:

- exit_type=0
- reason=0

Kết luận:

- Home có thể sống ổn định >1 phút
- USER 11 có tính state/timing dependent
- khả năng liên quan persistent CenRep state, nhưng chưa chứng minh

User được yêu cầu giữ dữ liệu app, không clean install.

---

# 10. HOMEONLY5 DEVICE RUN #2 — USER/11 TÁI HIỆN VÀ STACK ĐÃ BẮT ĐƯỢC

Log chính:

`EKA2L1_TakeThis(8).log`

HOME process/thread:

- process `Màn hình chủ[102750f0]0003`
- thread UID trong run này: 629

Panic:

- timestamp khoảng `17:25:14.279`
- exit_type = 2
- reason = 11
- category = `USER`
- PC = `0x80298584`
- LR = `0x802A3A39`

Ngay trước panic:

```
repo = 0x10275104
key = 0xA0001000
entry_len = 52
dst_max = 2048
write_len = 52
len_desc_present = 1
len_desc_max = 4
len_before = 2048
hex8 = 6C006F0063006100
status = 0
```

8 byte đầu là UTF-16LE bắt đầu bằng `l o c a ...`.

Key trước đó:

- `0x90001002`
- entry_len = 38
- status = 0

CenRep GetString hoàn tất thành công rồi Home panic USER 11 gần như ngay sau đó.

---

# 11. HOMEONLY5 STACK — MODULE QUAN TRỌNG LÀ AISCUTPLUGIN.DLL

PC/LR ở euser:

- PC:
  - `euser.dll + 0x0000313C`
- LR:
  - `euser.dll + 0x0000E5F0`

Các stack address map vào `aiscutplugin.dll`:

- stack[0]  → `aiscutplugin.dll + 0x00006F64`
- stack[17] → `aiscutplugin.dll + 0x0000475A`
- stack[24] → `aiscutplugin.dll + 0x00006F60`
- stack[31] → `aiscutplugin.dll + 0x00004A20`
- stack[51] → `aiscutplugin.dll + 0x00004E68`
- stack[63] → `aiscutplugin.dll + 0x00000D76`

Các frame euser khác:

- `euser.dll + 0x0001B080`
- `euser.dll + 0x00016804`
- `euser.dll + 0x000167C8`
- `euser.dll + 0x0001A562`
- `euser.dll + 0x00011E06`

**Đây là điểm điều tra hiện tại.**

AISCUT là shortcut/plugin của Active Idle/Home.

Không có source Nokia trực tiếp của `aiscutplugin.dll` trong SymbianSource search.

---

# 12. GIẢ THUYẾT CENREP “52 BYTE PHẢI LÀ 26 CHAR” ĐÃ BỊ LOẠI

Đã kiểm tra source Central Repository gốc của Symbian:

Repo:

`SymbianSource/oss.FCL.sf.os.persistentdata`

File:

`persistentstorage/centralrepository/pccenrep/src/pccenrep.cpp`

Implementation authoritative:

```cpp
EXPORT_C TInt CRepository::Get(TUint32 aKey, TDes16& aValue)
{
    TPtr8 ptr8((TUint8*)aValue.Ptr(), 0, aValue.MaxSize());
    TInt ret=Get(aKey,ptr8);
    if (ret==KErrNone)
        aValue.SetLength(ptr8.Length()/2);
    return ret;
}
```

Overload có actual length:

```cpp
EXPORT_C TInt CRepository::Get(
    TUint32 aKey,
    TDes16& aValue,
    TInt& aActualLength)
{
    TInt actualLength8;
    TPtr8 ptr8((TUint8*)aValue.Ptr(), 0, aValue.MaxSize());
    TInt ret=Get(aKey,ptr8,actualLength8);
    aValue.SetLength(ptr8.Length()/2);
    aActualLength=actualLength8/2;
    return ret;
}
```

Kết luận:

- CenRep server trả độ dài raw **theo byte**
- client TDes16 tự chia `/2`
- `entry_len=52` ở EKA2L1 server là hợp logic cho 26 UCS-2 chars

**KHÔNG sửa server 52 → 26.**

Hướng đó là sai ABI và đã bị loại.

---

# 13. FIRMWARE BINARY ĐÃ EXTRACT ĐỂ REVERSE ENGINEER

Trong runtime của chat này, exact RM-356 payload đã được extract và target files đã chuẩn bị:

```
/mnt/data/firmware-homeonly6/targets/aiscutplugin.dll
/mnt/data/firmware-homeonly6/targets/aiscutplugin.uncompressed.e32
/mnt/data/firmware-homeonly6/targets/aiscutplugin.code.bin
/mnt/data/firmware-homeonly6/targets/aiscutplugin.code.elf
/mnt/data/firmware-homeonly6/targets/aiscutsettings.dll
/mnt/data/firmware-homeonly6/targets/10275104.txt
```

Hashes:

## aiscutplugin.dll

- size: 25,468
- SHA256:
  `82bc75a917de8fda87a41fc49894c1928a075af99a6a89f1fa7ec61352be0221`

## aiscutplugin.uncompressed.e32

- size: 37,480
- SHA256:
  `b9f1f45cd5951817f6b17853528dc985c43fce748bfa46d551efb2cd5612221b`

## aiscutplugin.code.bin

- size: 33,856
- SHA256:
  `9ee630ae2368f6b390c555cf6625e131f3f3060a62688e291e5bb5033f0b1ca0`

## aiscutplugin.code.elf

- size: 34,260
- SHA256:
  `1738ae09da03122efd533cee8a2d515e90da9f0c40cb2cd7aedea66bd8231883`

## aiscutsettings.dll

- size: 17,553
- SHA256:
  `27a1692ee49f84c1faf63e89e11aa36e0259cd8916ba603610b67eaebd7997d9`

## 10275104.txt

- size: 1,410
- SHA256:
  `74f7b0431a83145e25f9743966e05ffdce8e90b5821ac0daee2b5aa84f9da289`

Decoded ROM-side `10275104.txt`:

- cenrep version 1
- owner `0x102750F9`
- default/meta/security policy entries
- `[Main]` is empty in this ROM text baseline

Do **not** infer that runtime key `0xA0001000` is absent from all sources; it may be created/persisted dynamically or supplied by another repository layer.

Important: `/mnt/data` is session-local. New chat may need to re-materialize/re-extract firmware from Library.

---

# 14. ĐIỂM ĐIỀU TRA ĐANG DỪNG CHÍNH XÁC

Đang ở bước:

**Disassemble exact `aiscutplugin.dll` RM-356 và map các HOMEONLY5 stack offsets về function/instruction/import calls.**

Offsets ưu tiên:

```
0x6F64
0x475A
0x6F60
0x4A20
0x4E68
0x0D76
```

Cần phân biệt ARM/Thumb đúng theo instruction/callsite.

Mục tiêu là tìm:

- descriptor Copy/Append/SetLength call nào dẫn tới USER 11
- fixed-size target descriptor là bao nhiêu
- dữ liệu nguồn là chuỗi CenRep nào
- code path trong AISCUT shortcut plugin
- import nào từ euser/centralrepository/Avkon liên quan

Sau khi tìm được callsite:

1. xác định lỗi thuộc guest/plugin do input/state bất thường hay emulator ABI;
2. chỉ sửa EKA2L1 nếu chứng minh ABI/behavior của emulator khác Symbian thật;
3. nếu cần thêm diagnostic, tạo HOMEONLY6 nhỏ, generic;
4. không hardcode `repo=0x10275104,key=0xA0001000` làm “fix” cuối;
5. không suppress USER 11.

---

# 15. E32/BINARY NOTES ĐÃ TRA

EKA2L1 E32 loader source:

- `src/emu/loader/include/loader/e32img.h`
- `src/emu/loader/src/e32img.cpp`

Relevant structures:

- E32 header has:
  - code_size
  - text_size
  - code_offset
  - import_offset
  - dll_ref_table_count
- IAT is parsed from:
  `code_offset + text_size`
- import section contains DLL name + ordinal lists

Prepared `aiscutplugin.code.bin` is 33,856 bytes and all observed AISCUT stack offsets fall inside its code range.

Next chat should use the prepared ELF/bin if still mounted, otherwise reproduce extraction/decompression and then use ARM/Thumb disassembly plus imports.

---

# 16. BUILD STRATEGY TỪ ĐÂY

Do not rebuild from MENUUI/B19 again.

Cache chain:

```
HOMEONLY2:
eka2l1-homeonly2-clean-menuui36-nojava-manic3-macos15-v1

HOMEONLY3:
eka2l1-homeonly3-keepmenu3-macos15-v1

HOMEONLY4:
eka2l1-homeonly4-eventwakeprobe-macos15-v1

HOMEONLY5:
eka2l1-homeonly5-user11stack-macos15-v1
```

Nếu làm HOMEONLY6:

- restore HOMEONLY5 cache
- apply only HOMEONLY6 delta
- incremental compile
- preserve binary gates:
  - MENUUI36 marker
  - M3HOME1
  - HOMEONLY3
  - HOMEONLY4 diagnostics nếu vẫn cần
  - HOMEONLY5 diagnostics nếu vẫn cần
  - no `[NBOOT2]`
  - no `[COMPATBOOT]`
  - no `src/emu/j2me`

Không replay NativeBoot/B29-B98.

---

# 17. PERMANENT INVARIANTS

- target Nokia 5800 RM-356 v60.0.003
- firmware không đổi
- UI hướng dẫn bằng tiếng Việt
- NOJAVA
- MANIC3 giữ nguyên
- Menu3 UID `0x101F4CD2`
- Home UID `0x102750F0`
- EPOC94 mapping lịch sử:
  - `0xAA` unmapped
  - `0xAB` message_construct
  - `0xAC` message_kill
- không fake TfxServer
- không fake Home
- không hardcode Home CenRep key làm production fix
- không suppress guest panic để che lỗi
- không merge Hướng 1 sang repo chính nếu user chưa yêu cầu
- repo `Eka2l1_bot_menu_simbiam` chỉ là build/cache host cho hướng này

---

# 18. NHỮNG KẾT LUẬN SAI ĐÃ LOẠI — KHÔNG LẶP LẠI

1. **“HOMEONLY2/HOMEONLY3 tự crash ra iOS Home”**  
   Sai. User tự vuốt về iOS Home.

2. **“Menu Options hiện ra chứng minh touch Home hoạt động”**  
   Sai. Home đã panic, framebuffer stale; Menu3 nhận touch.

3. **“TfxServer là hard barrier của Home route này”**  
   Sai. Home thật đã render/focus không cần TfxServer.

4. **“CenRep 52 bytes phải đổi thành 26 ở server”**  
   Sai. Symbian CRepository TDes16 wrapper tự chia /2 ở client.

5. **“CenRep GetString write trực tiếp overflow dst buffer”**  
   Không có bằng chứng. Lần panic mới nhất:
   - entry_len 52
   - dst_max 2048
   - write_len 52
   - status 0

6. **“HOMEONLY1 MENUUI14 là clean baseline tốt”**  
   Sai. Nó làm mất các input/focus fixes. HOMEONLY2/MENUUI36 mới là baseline.

---

# 19. FILE DEVICE EVIDENCE QUAN TRỌNG

HOMEONLY4 corrected evidence:

- `EKA2L1_TakeThis(6).log`
- video/screenshots 16:49
- USER 11 trước touch
- focus trả Menu3 group 2
- Menu3 nhận touch

HOMEONLY5 stable run:

- `EKA2L1_TakeThis(7).log`
- Home sống >1 phút, không USER 11

HOMEONLY5 reproduced panic + stack:

- `EKA2L1_TakeThis(8).log`
- `EKA2L1_Persistent-prev(7).log`
- 4 log + video user gửi trong lần test cuối

Nếu chat mới có file access, ưu tiên đọc `EKA2L1_TakeThis(8).log` quanh `17:25:14.278–17:25:14.280`.

---

# 20. VIỆC TIẾP THEO — KHÔNG HỎI LẠI USER

Bắt đầu chat mới bằng việc:

1. đọc HANDOFF này;
2. kiểm tra `codex/menu3-homeonly5`;
3. nếu `/mnt/data/firmware-homeonly6/targets` còn tồn tại thì dùng:
   - `aiscutplugin.code.elf`
   - `aiscutplugin.code.bin`
4. disassemble vùng quanh các stack offsets;
5. parse imports/IAT để đặt tên các call;
6. xác định descriptor operation gây USER 11;
7. mới quyết định HOMEONLY6 diagnostic/fix;
8. nếu có đủ bằng chứng thì tự triển khai/build, không cần xin phép lại.

User đã nhiều lần cho phép chủ động sửa/build.

---

# 21. CÂU LỆNH MỞ CHAT MỚI

Dùng nguyên văn:

> Tiếp tục dự án Hướng 1 Menu3 → Home từ `docs/handoff/NEWCHAT-HOMEONLY5-AISCUT-2026-09-29.md` trong repo `phai-nguyen/Eka2l1-nhanh-menuu3`, nhánh `codex/menu3-homeonly5`. HOMEONLY2/MENUUI36 NOJAVA là baseline đúng. HOMEONLY5 đã bắt được Home USER 11 với stack trỏ vào `aiscutplugin.dll`. Tiếp tục reverse-engineer exact RM-356 `aiscutplugin.dll` tại các offset `0x6F64, 0x475A, 0x6F60, 0x4A20, 0x4E68, 0x0D76`; không quay lại NativeBoot/CompatBoot và không sửa CenRep 52→26 vì Symbian TDes16 client tự chia /2.
