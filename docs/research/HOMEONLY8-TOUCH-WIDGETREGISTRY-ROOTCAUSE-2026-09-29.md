# HOMEONLY8 — Touch stall / WidgetRegistry startup root cause — 2026-09-29

## Scope

Emulator compatibility and preservation research for Nokia 5800 RM-356 / Symbian S60v5 in EKA2L1 only.

Baseline remains:

- HOMEONLY2 / MENUUI36 NOJAVA
- HOMEONLY7 quoted CenRep tokenizer fix retained
- no NativeBoot / CompatBoot
- no CenRep 52 -> 26 change
- no AISCUT panic suppression

## HOMEONLY7 device result

Device log set:

- EKA2L1_TakeThis(10).log
- EKA2L1_Persistent(10).log
- EKA2L1_Persistent-prev(8).log
- EKA2L1(10).log
- ScreenRecording_09-29-2026 22-23-21_1

### AISCUT USER/11 is fixed

The runtime shortcut previously truncated to 52 bytes now arrives intact:

```
22:24:01.893 [HOMEONLY1][CEN_GET_STRING]
repo=0x10275104 key=0xA0001000 entry_len=102 dst_max=2048 write_len=102
```

No USER/11 occurs in this HOMEONLY7 session.

This is the expected result of preserving '=' inside the quoted CenRep shortcut URI.

## Why Home looks alive but does not react to touch

The host/iOS input path and Window Server delivery are working.

At the first Home tap, the log records:

```
INPUT_HIT ... target_handle=9292808 client_thread=612
INPUT_FIFO_ENQUEUE ... event_type=5 evtype=0 pointer=0
INPUT_FIFO ... qsize=1 listener_pending=1
[HOMEONLY4][EVENT_WAKE] ... pending=1
[HOMEONLY4][EVENT_WAKE] stage=after_complete ... status=0 ... request_count_after=0
```

The Home thread is therefore actually woken by EventReady.

However, after that wake it immediately blocks again, and no later `INPUT_GET`
is issued by Home. Pointer events accumulate in the Window Server FIFO
(qsize 1 -> 2 -> ... -> 5).

Therefore the current failure is not hit-testing, coordinate transform, FIFO
insertion, or EventReady notification. Home is blocked on a different
synchronous dependency and does not drain its event queue.

## Blocking dependency: WidgetRegistry -> AppArc opcode 0x42

Immediately before the Home thread enters the long wait:

```
Create session to unexist server: !WidgetRegistry
Trying to summon server from executable WidgetRegistry
Spawned process: WidgetRegistry
widgetregistry.exe UID3=0x10282F06
...
Unimplemented applist opcode 0x42
```

There is no later `!WidgetRegistry` server start/rendezvous marker in the
session.

### Symbian source confirmation

Symbian Foundation WidgetRegistry source:

`webengine/widgetregistry/Server/src/WidgetRegistryServer.cpp`

`CWidgetRegistryServer::RunServerL()` connects to AppArc and synchronously
calls:

```cpp
apparcSession.RegisterNonNativeApplicationTypeL(
    KUidWidgetLauncher, KLauncherApp());
```

Only after that call returns does WidgetRegistry:

1. install its active scheduler;
2. construct/start `!WidgetRegistry`;
3. rename the server thread;
4. call `RProcess::Rendezvous(KErrNone)`;
5. enter the active scheduler.

Symbian AppArc `APSCLSV.H` maps opcode decimal 66 / hex 0x42 to:

`EAppListServRegisterNonNativeApplicationType`.

`RApaLsSession::RegisterNonNativeApplicationTypeL()` uses synchronous
`SendReceiveWithReconnect()`.

Baseline EKA2L1 already declares
`applist_request_register_non_native_app_type` in `services/applist/op.h`,
but the modern AppList dispatch switch has no handler for it. The default
branch only logs the unimplemented opcode and does not complete the IPC.

That leaves WidgetRegistry blocked before Rendezvous, which in turn leaves the
Home startup chain waiting. Touch can wake the Home thread's EventReady
request, but Home immediately returns to its other pending startup wait.

## HOMEONLY8 fix

Implement generic AppArc non-native application type registration in EKA2L1:

- handle `applist_request_register_non_native_app_type` (0x42);
- read application-type UID from IPC arg0;
- read native executable descriptor from arg1;
- store UID -> launcher mapping in memory;
- duplicate registration -> `KErrAlreadyExists`;
- complete successful registration with `KErrNone`;
- handle deregistration opcode 0x43 and complete it;
- no WidgetRegistry/Home UID or executable hard-code.

Patch:

- `apply_homeonly8_applistnonnative1.py`
- `test_homeonly8_applistnonnative1.py`

## Device PASS criteria

HOMEONLY8 should show all of:

1. `[HOMEONLY8][APPLIST_NONNATIVE] op=register ... inserted=1`;
2. WidgetRegistry proceeds past startup and reaches its server/rendezvous path;
3. Home resumes calling Window Server `GetEvent`;
4. touch FIFO does not monotonically accumulate;
5. Telephone / Contacts / Home controls react to touch;
6. no regression of the HOMEONLY7 102-byte CenRep shortcut;
7. no AISCUT USER/11.
