# Menu3 → Home Screen Bridge Design

Date: 2026-09-29  
Repository: `phai-nguyen/Eka2l1-nhanh-menuu3`  
Base branch: `codex/compatboot1-menuprobe1`  
Base commit: `bff5fb5f7b56831f6b930b389ba6d4b6990c2288`  
Work branch: `codex/menu3-homebridge1`

## Mục tiêu

Dùng Menu3 thật của firmware RM-356 làm nền UI đã khởi động ổn định, sau đó
cho người thử nghiệm chủ động yêu cầu mở Home Screen thật. Phép thử phải cho
biết Home có được AppArc khởi chạy, nhận focus và vẽ khung hình đầu tiên hay
không.

Mục tiêu không phải biến Menu3 thành Home giả, cũng không phải quay lại luồng
DirectHome. Menu3 vẫn là điểm kiểm soát an toàn phía sau trong phép thử đầu.

## Bằng chứng chọn hướng

Log và video thiết bị ngày 2026-09-29 xác nhận:

- Menu3 thật (`UID3 0x101F4CD2`) spawn, rendezvous và hiển thị lưới ứng dụng.
- Menu3 phản hồi thao tác; lần trở về iOS Home trong video xảy ra sau thao tác
  **Thoát trò chơi**, không phải bằng chứng Menu3 tự crash.
- Trong quá trình Menu3 khởi động, các thành phần `AknIconSrv`, `ECom`,
  `CdlServer`, `alfredserver` và `xnthemeserver` đã được khởi tạo.
- AppArc nhận diện Home Screen với UID `0x102750F0`.
- `TfxServer` vẫn chưa xuất hiện; các khoảng trống EikCore SVC `0x88/0x89`
  vẫn tồn tại. Vì vậy hướng này tạo điểm xuất phát ổn định hơn nhưng không được
  coi là đã sửa TfxServer hay EikCore.

## Kiến trúc được duyệt

### Điểm kích hoạt

Bản thử đầu thêm mục **Vào Home Screen** vào menu điều khiển emulator/game của
iOS, cạnh các mục hiện có như đổi bố cục phím và thoát trò chơi. Không sửa tài
nguyên hay giao diện bên trong `menu3.exe`.

Kích hoạt thủ công được chọn cho bản đầu vì thao tác của người thử nghiệm xác
nhận Menu3 đã hiển thị trước khi yêu cầu chuyển Home. Chưa tự động chuyển theo
thời gian.

### Điều kiện cho phép

Yêu cầu chỉ được chấp nhận khi:

- profile CompatBoot Menu3 đang hoạt động;
- tiến trình Menu3 UID `0x101F4CD2` còn sống;
- chưa có một yêu cầu Home khác đang chạy;
- Home UID `0x102750F0` được AppArc nhận diện.

Nếu thiếu điều kiện, không khởi chạy và ghi rõ lý do. Mỗi phiên chỉ có tối đa
một yêu cầu đang chạy; không tạo vòng lặp retry.

### Cách mở Home

Launcher gửi yêu cầu qua AppArc bằng UID `0x102750F0`. Phép thử đầu không gọi
thẳng executable, không gọi `ailaunch.exe`, không chủ động khởi động PhoneUi
và không giả lập TfxServer/IPC.

Nếu AppArc không chấp nhận yêu cầu, dừng tại kết quả đó và giữ Menu3. Không
fallback sang direct executable trong cùng bản thử vì sẽ làm mất khả năng xác
định nguyên nhân.

### Vòng đời Menu3

Menu3 không bị kill, suspend cưỡng bức hoặc thay thế khi gửi yêu cầu Home.
Nếu Home không spawn, panic, thoát hoặc không nhận focus, người dùng vẫn có thể
quay lại Menu3 hoặc thoát emulator bình thường.

Chỉ sau khi Home vẽ được và ổn định trên thiết bị mới xem xét bản sau tự động
chuyển Home hoặc hạ Menu3 xuống nền.

## Luồng quan sát

1. CompatBoot vượt hàng rào sáu dịch vụ hiện có và mở Menu3 thật.
2. Người dùng xác nhận lưới Menu3 đã hiển thị.
3. Người dùng mở menu điều khiển và chọn **Vào Home Screen**.
4. Host kiểm tra các điều kiện và gửi yêu cầu AppArc cho UID `0x102750F0`.
5. Trace theo dõi tuần tự: kết quả yêu cầu, process spawn, rendezvous, WindowGroup,
   focus, khung hình đầu, panic/exit và first failure.
6. Nếu Home thất bại hoặc timeout, Menu3 tiếp tục là nền an toàn.

## Marker bắt buộc

- `[HOME_BRIDGE][TRIGGER]`
- `[HOME_BRIDGE][GUARD_REJECT] reason=...`
- `[HOME_BRIDGE][APPARC_REQUEST] uid=0x102750F0 result=...`
- `[HOME_BRIDGE][PROCESS_SPAWN] uid=0x102750F0 ...`
- `[HOME_BRIDGE][RENDEZVOUS] ...`
- `[HOME_BRIDGE][WINDOW_GROUP] ...`
- `[HOME_BRIDGE][FOCUS] ...`
- `[HOME_BRIDGE][FIRST_FRAME] ...`
- `[HOME_BRIDGE][TARGET_EXIT] category=... code=...`
- `[HOME_BRIDGE][TIMEOUT] stage=...`
- `[HOME_BRIDGE][FIRST_FAILURE] source=... result=...`

Các marker phải mang timestamp, process/thread và UID liên quan; không ghi dữ
liệu người dùng.

## Xử lý lỗi

- AppArc không có Home UID: từ chối với lý do cụ thể, giữ Menu3.
- AppArc trả lỗi: ghi đúng mã lỗi, không thử đường khởi chạy khác.
- Home spawn nhưng không rendezvous/focus/vẽ: timeout theo từng giai đoạn và ghi
  giai đoạn cuối đã đạt.
- Home panic/exit: ghi category/code và giữ Menu3.
- Thiếu `TfxServer` hoặc SVC chưa hỗ trợ: ghi như first failure nếu nó là lỗi
  quyết định sớm nhất; không che lỗi trong bản đầu.
- Không thay đổi hành vi thoát emulator hiện có.

## Phạm vi không làm

- Không sửa, merge hoặc reset DirectHome và B99.
- Không thay firmware, hàng rào sáu dịch vụ hoặc Native Boot mặc định.
- Không tự động mở Home ngay khi Menu3 xuất hiện trong bản đầu.
- Không kill Menu3 sau khi gửi yêu cầu.
- Không giả lập `TfxServer`, ALF IPC, EikCore SVC hay trạng thái hệ thống.
- Không tuyên bố Home thành công chỉ vì AppArc trả 0 hoặc process được spawn.
- Không thêm fallback Menu3 vào DirectHome; đây là một nhánh thử riêng bắt đầu
  từ Menu3.

## Kiểm thử

### Kiểm thử hợp đồng

- Mục **Vào Home Screen** chỉ xuất hiện/hoạt động trong profile thử này.
- Native Boot vẫn là mặc định.
- Guard từ chối khi Menu3 không sống, Home UID không tồn tại hoặc yêu cầu đang
  chạy.
- Một thao tác chỉ phát sinh một yêu cầu AppArc.
- Launcher dùng chính xác UID `0x102750F0`.
- Không có lời gọi direct executable, `ailaunch.exe`, PhoneUi hay Tfx shim.
- Menu3 không bị kill/suspend bởi cầu nối.
- Marker và workflow/manifest FASTBUILD được đăng ký; patcher idempotent.

### Kiểm thử thiết bị

- **P0:** Menu3 vẫn hiển thị và nhận thao tác như baseline.
- **P1:** AppArc trả kết quả và log nhận diện đúng Home UID.
- **P2:** Home process spawn và rendezvous.
- **P3:** Home tạo WindowGroup và nhận focus.
- **P4:** Home vẽ được khung hình đầu tiên.
- **P5:** Home phản hồi chạm và có thể quay lại Menu3.

Chỉ P4 trở lên được gọi là đã vào được Home Screen. Build chỉ được gọi GREEN
khi GitHub Actions kết luận `success`; chỉ báo có IPA khi artifact IPA được
xác nhận.

## Bảo toàn mốc đối chứng

- Nhánh gốc Menu3 `codex/compatboot1-menuprobe1` giữ nguyên.
- Nhánh DirectHome trong repo chính giữ nguyên.
- Nhánh B99 `codex/compatboot1-menuprobe2-nobypass` giữ nguyên.
- Mọi thay đổi của phép thử nằm trên `codex/menu3-homebridge1`.


## 2026-09-29 implementation correction from device evidence

The device video/log set used for M3HOME1 establishes that the successful Menu3 baseline is **normal EKA2L1/HLE frontend mode**, not CompatBoot/native PhoneUI:

- runtime marker: `[NBOOT2][MODE] native_phone_boot=0`;
- Menu is registered as UID `0x101F4CD2`;
- Home screen is registered as UID `0x102750F0`;
- the iOS frontend already launches system applications through
  `RootViewController::launchAppUid` → `bridge::launch_app(uid)` →
  `g_state->launcher_->launch_app(uid)`.

Therefore M3HOME1 does **not** construct a native AppArc client session and does not pass through PhoneUI, `ailaunch.exe`, EStart, or a TfxServer shim.

The minimal implementation is:

1. launch Menu3 normally (UID `0x101F4CD2`);
2. keep Menu3 running;
3. expose **Vào màn hình chính** only while that UID is current;
4. on selection, queue one main-thread turn and call
   `launchAppUid:0x102750F0`;
5. instrument the existing bridge route with:
   - `[M3HOME1][TRIGGER]`
   - `[M3HOME1][APPARC_REQUEST]`
   - `[M3HOME1][APPARC_DISPATCHED]`
   - `[M3HOME1][GUARD_REJECT]`.

This is intentionally a one-variable experiment: no firmware changes, no Home dependency emulation, no Menu3 shutdown before launch, and no changes to AppList/WindowServer behavior. If Home launches but does not become visible, the next investigation is foreground/window-group ownership rather than startup-chain bootstrapping.
