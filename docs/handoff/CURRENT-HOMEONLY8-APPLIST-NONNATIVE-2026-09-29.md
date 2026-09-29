# CURRENT HANDOFF — HOMEONLY8 APPLISTNONNATIVE1 — 2026-09-29

## Scope

EKA2L1 emulator compatibility / preservation for Nokia 5800 RM-356 / Symbian S60v5.

Baseline semantic:

- HOMEONLY2 / MENUUI36 NOJAVA / MANIC3
- HOMEONLY7 quoted CenRep tokenizer root fix retained
- no NativeBoot / CompatBoot
- no CenRep 52 -> 26 conversion
- no firmware patch
- no AISCUT panic suppression

Research branch:

`codex/menu3-homeonly8-applist-nonnative1`

## HOMEONLY7 device result

HOMEONLY7 successfully fixed the previous AISCUT USER/11 path.

In `EKA2L1_TakeThis(10).log`:

```
repo=0x10275104 key=0xA0001000 entry_len=102 dst_max=2048 write_len=102
```

The old broken value was 52 bytes. No USER/11 occurs in this run.

Video shows Home Screen renders, but taps on the Home UI do not produce visible UI action.

## Touch pipeline diagnosis

The host input path reaches the real Home window:

```
INPUT_HIT ... target_handle=9292808 client_thread=612
INPUT_FIFO_ENQUEUE ... event_type=5 evtype=0
INPUT_FIFO ... qsize=1 listener_pending=1
[HOMEONLY4][EVENT_WAKE] ... pending=1
[HOMEONLY4][EVENT_WAKE] stage=after_complete ... status=0 ... request_count_after=0
```

Therefore:

- coordinate conversion is working;
- hit testing selects Home;
- Window Server queues the touch event;
- EventReady completes;
- the Home thread is signalled.

But Home does not issue another Window Server GetEvent after startup. Subsequent
pointer events accumulate in the FIFO.

## New blocker

Immediately before the long Home wait:

```
Create session to unexist server: !WidgetRegistry
Trying to summon server from executable WidgetRegistry
Spawned process: WidgetRegistry
...
Unimplemented applist opcode 0x42
```

Exact Symbian sources identify AppList opcode 0x42 as:

`EAppListServRegisterNonNativeApplicationType`.

WidgetRegistry startup synchronously calls:

```
RApaLsSession::RegisterNonNativeApplicationTypeL(
    KUidWidgetLauncher, KLauncherApp());
```

before it constructs `!WidgetRegistry` and calls `RProcess::Rendezvous`.

Baseline EKA2L1 defines the opcode enum but has no dispatch handler. Its
default AppList case only logs the unimplemented opcode without completing
the synchronous IPC. WidgetRegistry therefore never reaches Rendezvous and
the Home startup chain stays blocked.

Detailed research:

`docs/research/HOMEONLY8-TOUCH-WIDGETREGISTRY-ROOTCAUSE-2026-09-29.md`

## HOMEONLY8 fix

Patch:

- `apply_homeonly8_applistnonnative1.py`
- `test_homeonly8_applistnonnative1.py`

Generic implementation:

- handle AppList register non-native type opcode 0x42;
- read type UID from arg0;
- read native launcher descriptor from arg1;
- store UID -> executable mapping;
- duplicate -> KErrAlreadyExists;
- complete success -> KErrNone;
- handle deregistration opcode 0x43;
- no Home/WidgetRegistry UID or executable hardcode.

HOMEONLY7 tokenizer and all diagnostic markers remain.

## Build

Build repo:

`phai-nguyen/Eka2l1_bot_menu_simbiam`

Branch:

`codex/m3home-homeonly2-build`

Workflow:

`.github/workflows/build-homeonly8-applist-nonnative1.yml`

Run:

`36592695512`

Result:

**GREEN / success**

Build host commit:

`cc39f2307868b8e543bc944924884382162ac1ad`

IPA artifact:

`EKA2L1-HOMEONLY8-APPLIST-NONNATIVE1-IPA`

Artifact ID:

`11044861852`

IPA filename:

`EKA2L1-HOMEONLY8-APPLIST-NONNATIVE1-unsigned.ipa`

IPA SHA-256:

`5b4915f5097b675a2c2e59a0393a5fb3c652dcdddd3398a43894301cf9dcf466`

## Device test criteria

Prefer clean install.

Primary PASS markers:

1. `[HOMEONLY8][APPLIST_NONNATIVE] op=register ... inserted=1`
2. no endless `Unimplemented applist opcode 0x42`
3. `!WidgetRegistry` proceeds through startup / Rendezvous
4. Home resumes Window Server GetEvent after pointer wake
5. FIFO qsize drains instead of monotonically growing
6. Telephone / Contacts / Home controls react
7. runtime shortcut remains 102 bytes
8. no AISCUT USER/11

If touch still does not react, keep this build and inspect the next synchronous
startup dependency after WidgetRegistry; do not return to the old AISCUT or
CenRep hypotheses unless the corresponding diagnostics actually regress.
