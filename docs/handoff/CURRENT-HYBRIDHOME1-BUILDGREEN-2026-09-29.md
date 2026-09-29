# CURRENT — HYBRIDHOME1 BUILD GREEN — 2026-09-29

## Scope

OldOS-style hybrid S60 shell experiment for Nokia 5800 RM-356 in EKA2L1.

This is an emulator compatibility / preservation path. It is separate from the
real-Home HOMEONLY investigation.

## Architecture

```
real Menu3 guest (UID 0x101F4CD2)
        ↓
host-rendered UIKit Hybrid Home
        ↓
EKA2L1 bridge::get_apps()
        ↓
existing launchAppUid / bridge::launch_app
        ↓
real registered Symbian application
```

The HYBRIDHOME1 path does **not** launch Nokia Home UID `0x102750F0`.

## Source

Research branch:

`phai-nguyen/Eka2l1-nhanh-menuu3@codex/hybridhome1-oldos-shell`

Source head used by the successful build:

`83e1326dd25bedec0b8d6d20435484b0ee965b2a`

Files:

- `apply_hybridhome1_oldosshell.py`
- `test_hybridhome1_oldosshell.py`
- `docs/handoff/HYBRIDHOME1-OLDOS-SHELL-2026-09-29.md`

## Build backend

Build host:

`phai-nguyen/Eka2l1_bot_menu_simbiam@codex/m3home-homeonly2-build`

The current HOMEONLY2 cache was no longer available in GitHub Actions cache, so
the successful build restores the fresh HOMEONLY9 backend cache. That cache is
still on the MENUUI36 / NOJAVA / MANIC3 lineage and retains the validated
Symbian backend compatibility fixes. HYBRIDHOME1 itself does not depend on the
real Nokia Home startup chain.

Audit:

- architecture = `OLDOS_STYLE_HOST_SHELL_PLUS_REAL_SYMBIAN_BACKEND`
- baseline = `HOMEONLY9_BACKEND_ON_MENUUI36_NOJAVA_MANIC3`
- Menu3 UID = `0x101F4CD2`
- real Home UID = `NOT_REQUIRED`
- presentation = `UIKIT_HOST_OVERLAY`
- app registry = `EKA2L1_BRIDGE_GET_APPS`
- app launch = `EXISTING_EKA2L1_LAUNCHER`
- Menu3 underlay = `PRESERVED`
- Java = removed

## Successful GitHub Actions build

Run:

`36600699450`

Conclusion:

**GREEN / success**

Build-host head:

`7325f43f9ef6f9079f20636ec2991138ac84ad06`

IPA artifact:

`EKA2L1-HYBRIDHOME1-OLDOS-SHELL-IPA`

Artifact ID:

`11048733884`

IPA file:

`EKA2L1-HYBRIDHOME1-OLDOS-SHELL-unsigned.ipa`

IPA SHA-256:

`101b3bdbd1d9d56e71126e053d03d720beed11f58afcb3481ae957ba564ad23f`

Audit artifact:

`EKA2L1-HYBRIDHOME1-OLDOS-SHELL-AUDIT`

Artifact ID:

`11048613934`

## Device test

1. Start the validated Menu3 path.
2. Open the emulator game menu.
3. Choose **Hybrid Home (thử nghiệm)**.
4. Confirm the host-rendered Home appears.
5. Tap **Trở về Menu3 thật** and confirm Menu3 resumes without an emulator reboot.
6. Open Hybrid Home again.
7. Tap **Ứng dụng Symbian thật**.
8. Choose one ordinary registered Symbian app.
9. Confirm that the real guest app launches.

Primary markers:

- `[HYBRIDHOME1][TRIGGER]`
- `[HYBRIDHOME1][SHOW]`
- `[HYBRIDHOME1][RETURN_MENU3]`
- `[HYBRIDHOME1][APP_CHOOSER]`
- `[HYBRIDHOME1][LAUNCH_REAL_APP]`

Architecture PASS requires:

`Menu3 real -> Hybrid Home -> Menu3 real -> Hybrid Home -> real app list -> real Symbian app`.

## New repository status

The connected GitHub action surface available in this chat can create branches,
files and workflows in existing repositories, but does not expose the GitHub
repository-creation endpoint. Therefore HYBRIDHOME1 has been kept isolated in
the branches above so work was not blocked. Once an empty top-level repository
is created, this branch can be migrated into it without changing the prototype.
