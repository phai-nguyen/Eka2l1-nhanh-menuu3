# PROJECT STATE — Hướng 1 Menu3 / Symbian emulation

**Updated:** 2026-09-29  
**Repository:** `phai-nguyen/Eka2l1-nhanh-menuu3`  
**Primary project:** EKA2L1 + Nokia 5800 XpressMusic RM-356 / S60v5  
**Primary goal:** boot and run the real Symbian Menu3 environment inside EKA2L1, then use that stable Menu3 baseline for compatibility experiments such as launching the real Home Screen.

---

## 0. Scope / Safety clarification

This repository is an **emulation and compatibility research project for Symbian/S60v5**.

The intended scope is:

- emulate Nokia 5800 RM-356 / Symbian behavior in EKA2L1;
- boot the real firmware-side Menu3 / application shell components;
- reproduce guest OS services and ABI behavior needed by legitimate applications;
- diagnose crashes, panics, IPC, descriptors, CenRep, WindowServer, input/focus, startup, and application-launch behavior;
- preserve device-test evidence so compatibility regressions can be reproduced.

The project is **not** intended for, and is not related to:

- exploitation of third-party systems;
- unauthorized access or intrusion;
- malware, trojans, ransomware, spyware, or credential theft;
- credential harvesting, password/token/session theft, or account takeover;
- malicious persistence on devices, servers, or networks;
- command-and-control, lateral movement, privilege escalation against real targets, or evasion;
- network attacks, scanning, phishing, denial of service, or data exfiltration.

Any references in the code or logs to processes, servers, launchers, IPC, hooks, startup state, persistence files, or firmware internals refer to **guest Symbian emulation/compatibility behavior inside the emulator**, not to mechanisms for compromising external systems.

Reverse engineering performed in this project is limited to understanding **firmware/application compatibility and ABI behavior** required to make the emulated Symbian environment behave like the original device.

---

## 1. Project identity and repository split

This repository is the dedicated **Hướng 1 / Menu3** project:

`phai-nguyen/Eka2l1-nhanh-menuu3`

It was split from the earlier mixed NATIVEBOOT2 work so Menu3 experiments can proceed without changing the B99 / DirectHome comparison line.

Important separation:

- **Hướng 1 / this repo:** preserve the proven MenuUI/Menu3 baseline and move from Menu3 toward real Home when useful.
- **NATIVEBOOT2 / CompatBoot / DirectHome:** separate historical/parallel work. Do not merge it back into Hướng 1 unless explicitly requested.
- `phai-nguyen/Eka2l1_bot_menu_simbiam` may still be used as a build/cache host for some Hướng 1 workflows, but it is not the authoritative Hướng 1 source repository.

---

## 2. Target device and firmware

Target:

- Nokia 5800 XpressMusic
- RM-356
- S60 5th Edition / Symbian
- firmware v60.0.003
- firmware UI used for device testing is Vietnamese

Device-test environment:

- iPhone 12 Pro Max
- iOS 18.7
- Windows 7 64-bit PC, 2 GB RAM
- no Mac available to the tester

Known firmware files:

### SYM.ROM

- size: 41,283,584 bytes
- SHA256: `b4328dfa555d73e14a4bab2de46bbec702970e4b63c8ce878da589fa6b64c444`

### SYM.RPKG

- size: 134,540,934 bytes
- SHA256: `bc41496abc8d4c87de976b65cadfb922b4dfd9583a0dbcf35b7e4bff23eb008f`

Do not silently replace or mix the firmware set while diagnosing runtime behavior.

---

## 3. Historical Menu3 baseline

The earlier MenuUI line established the usable Menu3 input/focus baseline.

Relevant milestones:

- MENUUI30 — Stock FEP work
- MENUUI31 — raw pen input
- MENUUI33 — key sound
- MENUUI35 — async simulated input
- MENUUI36 — WINFOCUS1
- NOJAVA — J2ME removed
- MANIC3 — retained

**MENUUI36 WINFOCUS1 + NOJAVA + MANIC3 is the semantic baseline that must be preserved.**

Do not rebuild current Hướng 1 work from the older MENUUI14/HOMEONLY1 baseline.

Historical EPOC94 mapping to preserve unless deliberately changed:

- `0xAA` — unmapped
- `0xAB` — `message_construct`
- `0xAC` — `message_kill`

---

## 4. Current Menu3 → Home route

Current compatibility route:

```text
normal EKA2L1
    ↓
Menu3 UID 0x101F4CD2
    ↓
existing EKA2L1/iOS launcher path
    ↓
real Home Screen UID 0x102750F0
```

Menu command:

**Vào màn hình chính**

Markers include:

- `[M3HOME1][TRIGGER]`
- `[M3HOME1][APPARC_REQUEST]`
- `[M3HOME1][APPARC_DISPATCHED]`

The `APPARC` wording is a legacy marker name; the route uses the existing launcher/HLE path rather than requiring native AppArc startup.

The real Home Screen has rendered on device with:

- Nokia wallpaper;
- status bar;
- “Set up e-mail”;
- Telephone / Contacts softkeys;
- a real WindowServer Home window group/focus.

This proves that **TfxServer is not a hard prerequisite for rendering Home on this route**.

---

## 5. HOMEONLY baselines and device results

### HOMEONLY1 — rejected baseline

HOMEONLY1 was derived from MENUUI14 and regressed the later Menu3 input/focus work.

**Do not use HOMEONLY1 as the current baseline.**

### HOMEONLY2 — correct clean baseline

HOMEONLY2 was rebuilt from:

- MENUUI36 WINFOCUS1
- NOJAVA
- MANIC3

Build authority:

- Actions run: `36544190013`
- IPA SHA256: `f9da544ad1b105789909a89bcf02580e4b140217d676b1e218b68c05f283e360`
- cache: `eka2l1-homeonly2-clean-menuui36-nojava-manic3-macos15-v1`

This remains the semantic baseline.

### HOMEONLY3 — preserve Menu3 after Home exits

HOMEONLY3 changes host lifecycle only:

- if Home UID `0x102750F0` exits, do not reboot the emulator;
- keep Menu3/session alive;
- restore host bookkeeping to Menu3 UID `0x101F4CD2`.

Marker:

`[HOMEONLY3][HOME_EXIT_KEEP_MENU3]`

Build:

- Actions run: `36546587496`
- IPA SHA256: `721647d2963f30e3d6ba0c0f8f98dd6329041a08f3c31949c81d6c6842db582b`
- cache: `eka2l1-homeonly3-keepmenu3-macos15-v1`

Important correction: the earlier video did **not** prove EKA2L1 crashed to iOS Home; the user manually swiped to iOS Home.

### HOMEONLY4 — EventReady/request-semaphore diagnostics

Diagnostics:

- `[HOMEONLY4][EVENT_WAKE]`
- `[HOMEONLY4][SEMA_WAKE]`
- `[HOMEONLY4][REQ_WAIT]`

Build:

- Actions run: `36549741084`
- IPA SHA256: `202825a53cc35ce4526d05efb194765ac34ad1565488999b7ef96e9efbe95ef6`
- cache: `eka2l1-homeonly4-eventwakeprobe-macos15-v1`

Corrected device interpretation:

1. Home renders.
2. Home can panic with `USER / 11`.
3. HOMEONLY3 keeps the last Home framebuffer visible.
4. WindowServer focus can return to Menu3.
5. A later tap can be delivered to Menu3.
6. Menu3 can therefore draw an Options menu over the stale Home framebuffer.

Therefore **Home touch has not yet been proven to work**. Do not treat the visible Menu3 Options overlay as evidence of Home hit-testing.

### HOMEONLY5 — USER/11 stack capture

HOMEONLY5 adds targeted diagnostic capture for:

- process UID3 `0x102750F0`;
- panic category `USER`;
- reason `11`.

Markers:

- `[HOMEONLY5][USER11_CONTEXT]`
- `[HOMEONLY5][USER11_FRAME]`
- `[HOMEONLY5][USER11_STACK]`
- `[HOMEONLY5][USER11_STACK_END]`

Captured state includes PC/LR/SP/CPSR, r0-r12, request_count and a bounded stack dump mapped to guest modules.

Build authority:

- workflow run: `36553079575`
- IPA artifact ID: `11024594554`
- AUDIT artifact ID: `11025606850`
- IPA SHA256: `0b7737d9f3e38403dc52698c15f506e142674b6e8066f347a41a6e32ab25391b`
- cache: `eka2l1-homeonly5-user11stack-macos15-v1`

Authoritative source branch for this state:

`codex/menu3-homeonly5`

Later experiment branches such as `codex/menu3-homeonly6` and `codex/menu3-homeonly7-cenrepquoted1` exist in the repository, but HOMEONLY5 remains the last promoted device-evidence baseline unless a newer result is explicitly promoted.

---

## 6. HOMEONLY5 device evidence

### Run 1 — Home stayed alive for more than one minute

Observed:

- Home launch around `17:18:08.705`
- Home WindowServer focus group 30
- Home thread UID 611
- no `USER/11`
- no HOMEONLY5 panic stack because no panic occurred
- Home thread still alive/waking around `17:19:27.607`

Conclusion:

- Home can stay alive for >1 minute.
- `USER/11` is state/timing dependent.
- persistent guest state, including CenRep state, remains a possibility but is not proven as the cause.

### Run 2 — USER/11 reproduced and stack captured

Panic:

- time: ~`17:25:14.279`
- exit type: panic
- category: `USER`
- reason: `11`
- PC: `0x80298584`
- LR: `0x802A3A39`

Immediately before panic, CenRep GetString completed with:

- repo: `0x10275104`
- key: `0xA0001000`
- entry_len: 52
- dst_max: 2048
- write_len: 52
- status: 0
- first bytes: `6C006F0063006100` (UTF-16LE beginning with “loca…”)

The previous key `0x90001002` also completed successfully.

This is a temporal correlation, not proof that CenRep itself is the panic source.

---

## 7. Current strongest lead: aiscutplugin.dll

HOMEONLY5 stack frames map repeatedly into the exact RM-356 firmware module:

`Z:\\sys\\bin\\aiscutplugin.dll`

Important offsets:

- `0x6F64`
- `0x475A`
- `0x6F60`
- `0x4A20`
- `0x4E68`
- `0x0D76`

PC/LR are in `euser.dll`, while these AISCUT frames are the strongest guest-side path leading to the panic.

Prepared exact firmware artifacts from the analysis session included:

- `aiscutplugin.dll`
- `aiscutplugin.uncompressed.e32`
- `aiscutplugin.code.bin`
- `aiscutplugin.code.elf`
- `aiscutsettings.dll`
- `10275104.txt`

Key hashes:

### aiscutplugin.dll

- size: 25,468
- SHA256: `82bc75a917de8fda87a41fc49894c1928a075af99a6a89f1fa7ec61352be0221`

### aiscutplugin.uncompressed.e32

- size: 37,480
- SHA256: `b9f1f45cd5951817f6b17853528dc985c43fce748bfa46d551efb2cd5612221b`

### aiscutplugin.code.bin

- size: 33,856
- SHA256: `9ee630ae2368f6b390c555cf6625e131f3f3060a62688e291e5bb5033f0b1ca0`

### aiscutsettings.dll

- size: 17,553
- SHA256: `27a1692ee49f84c1faf63e89e11aa36e0259cd8916ba603610b67eaebd7997d9`

### 10275104.txt

- size: 1,410
- SHA256: `74f7b0431a83145e25f9743966e05ffdce8e90b5821ac0daee2b5aa84f9da289`

The next technical task is to disassemble the exact AISCUT code around the captured offsets and map calls/imports to the descriptor operation that triggers `USER/11`.

---

## 8. CenRep ABI conclusion — do not regress this

A prior hypothesis proposed changing a CenRep 16-bit string length from 52 bytes to 26 characters at the server boundary.

That hypothesis was rejected.

Symbian `CRepository::Get(TDes16&)` wraps the destination in a `TPtr8`, receives raw bytes from the server and then divides the resulting descriptor length by two on the client side.

Therefore:

- `entry_len=52` bytes is ABI-consistent for a 26-character UCS-2 string;
- do **not** change the server result from 52 to 26 as a fix;
- do not hardcode `repo=0x10275104,key=0xA0001000` as a production fix.

---

## 9. Current invariants

Keep these unless a new experiment explicitly changes them:

- Nokia 5800 RM-356 v60.0.003 target
- firmware set unchanged
- Vietnamese test instructions
- MENUUI36 semantic baseline
- NOJAVA
- MANIC3
- Menu3 UID `0x101F4CD2`
- Home UID `0x102750F0`
- do not fake TfxServer
- do not fake Home
- do not suppress guest panic merely to hide a compatibility failure
- do not hardcode a specific Home CenRep key as the final fix
- do not silently reintroduce NativeBoot/CompatBoot into Hướng 1
- do not merge Hướng 1 into the other repo/branch family unless explicitly requested

---

## 10. Current branch map

Known relevant branches in this repository:

- `main` — project/checkpoint branch; was stale at B98 before this state refresh
- `codex/compatboot1-menuprobe1` — imported historical Menu3/CompatBoot line
- `codex/menu3-homebridge1`
- `codex/menu3-homebridge2`
- `codex/menu3-homebridge3`
- `codex/menu3-homeonly1`
- `codex/menu3-homeonly3`
- `codex/menu3-homeonly4`
- `codex/menu3-homeonly5` — authoritative promoted HOMEONLY5 source state
- `codex/menu3-homeonly6` — later experiment branch
- `codex/menu3-homeonly7-cenrepquoted1` — later experiment branch carrying the HOMEONLY5 authoritative handoff

The presence of a later-numbered branch does not by itself promote its runtime behavior. Promotion requires device evidence and an updated authoritative checkpoint.

---

## 11. Next work

Next work should begin from the HOMEONLY5/MENUUI36 state, not from B98 or NativeBoot.

Priority:

1. disassemble exact RM-356 `aiscutplugin.dll`;
2. map `0x6F64, 0x475A, 0x6F60, 0x4A20, 0x4E68, 0x0D76` to instructions/functions/imports;
3. identify the exact descriptor operation leading to `USER/11`;
4. determine whether the failure is caused by guest state/input or an EKA2L1 ABI/behavior mismatch;
5. if more evidence is required, make a small generic HOMEONLY6 diagnostic delta;
6. preserve HOMEONLY5 diagnostics and incremental build/cache chain;
7. only change emulator semantics when there is evidence they differ from real Symbian behavior.

Do not return to B29-B98 NativeBoot replay for this line.

---

## 12. Build/cache chain

```text
HOMEONLY2
eka2l1-homeonly2-clean-menuui36-nojava-manic3-macos15-v1

HOMEONLY3
eka2l1-homeonly3-keepmenu3-macos15-v1

HOMEONLY4
eka2l1-homeonly4-eventwakeprobe-macos15-v1

HOMEONLY5
eka2l1-homeonly5-user11stack-macos15-v1
```

Future builds should restore the latest valid cache and apply only the next delta.

---

## 13. Authoritative continuity note

For a new conversation, start from this file plus:

`codex/menu3-homeonly7-cenrepquoted1:docs/handoff/NEWCHAT-HOMEONLY5-AISCUT-2026-09-29.md`

The key continuity sentence is:

> Hướng 1 is a Symbian emulation/compatibility project. Preserve MENUUI36 + NOJAVA + MANIC3, boot Menu3 UID 0x101F4CD2, and continue the Menu3 → real Home investigation from HOMEONLY5. HOMEONLY5 captured a real Home `USER/11` panic with multiple stack frames in exact RM-356 `aiscutplugin.dll`. Do not return to NativeBoot/CompatBoot, do not change CenRep 52→26, and do not suppress the panic as a cosmetic workaround.
