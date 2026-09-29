# EKA2L1 — Hướng 1 Menu3 / Nokia 5800 Symbian

Dedicated repository for the **Hướng 1 Menu3** compatibility line:

`phai-nguyen/Eka2l1-nhanh-menuu3`

## Scope / Safety clarification

This repository is for **Symbian/S60v5 emulation and application/firmware compatibility research**.

The primary target is Nokia 5800 XpressMusic RM-356 v60.0.003. The project aims to boot and run the real Symbian **Menu3** environment inside EKA2L1 and reproduce the guest OS behavior required for legitimate software compatibility. Current experiments may launch the real Symbian Home Screen from the stable Menu3 baseline.

This project is **not an exploitation, intrusion or malware project**. It is not intended for unauthorized access, credential theft, password/token/session harvesting, malicious persistence, spyware, ransomware, command-and-control, lateral movement, privilege escalation against real targets, phishing, scanning, denial of service, data exfiltration or network attacks.

References to processes, servers, launchers, IPC, startup, hooks, firmware internals or persistent state describe **guest Symbian behavior inside the emulator**.

## Current status

Correct baseline:

`MENUUI36 WINFOCUS1 + NOJAVA + MANIC3`

Key UIDs:

- Menu3: `0x101F4CD2`
- Home Screen: `0x102750F0`

The real Home Screen has rendered from Menu3. The current promoted diagnostic state is **HOMEONLY5**, which captured a real Home `USER/11` panic with multiple stack frames in RM-356 `aiscutplugin.dll`. The next task is to map those exact firmware offsets and determine whether the failure is guest-state related or an EKA2L1 ABI/behavior mismatch.

Full current checkpoint:

[docs/handoff/PROJECT-STATE-2026-09-29.md](docs/handoff/PROJECT-STATE-2026-09-29.md)

Short current pointer:

[docs/handoff/CURRENT.md](docs/handoff/CURRENT.md)
