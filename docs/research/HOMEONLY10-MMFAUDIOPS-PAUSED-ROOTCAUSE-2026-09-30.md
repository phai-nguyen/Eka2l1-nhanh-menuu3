# HOMEONLY10 — Missing paused-client MMF P&S after HOMEONLY9 — 2026-09-30

## Scope

EKA2L1 emulator compatibility / preservation for Nokia 5800 RM-356 / Symbian S60v5.

Baseline retained:

- HOMEONLY2 / MENUUI36 NOJAVA / MANIC3
- HOMEONLY7 quote-aware CenRep tokenizer fix
- HOMEONLY8 AppList non-native registration fix
- HOMEONLY9 standard MMF playing-client P&S fix
- no NativeBoot / CompatBoot
- no CenRep 52 -> 26 conversion
- no firmware patch
- no AISCUT patch
- no panic suppression

## HOMEONLY9 device result

HOMEONLY9 fixes the HOMEONLY8 crash:

- marker appears at startup:
  `[HOMEONLY9][MMF_AUDIO_PS] category=0x101F457F key=2 size=88 ... defined_now=1`
- there is no HOMEONLY8 access violation at `0x00410000`
- there is no KERN-EXEC 3 termination of the Home thread
- WidgetRegistry still completes the HOMEONLY8 AppArc registration path

The Home process remains alive and Window Server hit-testing still targets the
real Home client.

However Home does not drain pointer events after startup.

## Input evidence

At the first tap after Home renders:

```
INPUT_HIT ... target_handle=9293680 client_thread=613
INPUT_FIFO_ENQUEUE ... event_type=5 evtype=0
INPUT_FIFO ... qsize=1 listener_pending=1
[HOMEONLY4][EVENT_WAKE] ... thread=Home screen ... pending=1
[HOMEONLY4][EVENT_WAKE] stage=after_complete ... status=0 ... request_count_after=0
```

So the iOS input path, coordinate transform, hit-test, FIFO insertion and
EventReady completion still work.

Home nevertheless does not issue another `INPUT_GET`; later pointer packets
accumulate in the FIFO.

## Newly exposed dependency

Immediately before the next MPX startup transition HOMEONLY9 records:

```
Attach to property with category: 0x101f457f, key: 0x2
Attach to property with category: 0x101f457f, key: 0x4
Property (0x101f457f, 0x4) has not been defined before, undefined behavior may rise
Create session to unexist server: MPXPlaybackServer
```

HOMEONLY9 deliberately fixed only key 2. The device log therefore proves a
second standard MMF property is required.

Symbian `AudioClientsListPSKeys.h` identifies:

- category `0x101F457F` = `KPSUidMMFAudioServer`
- key 2 = `KAudioPolicyApplicationAudioStatePlaying`
- key 4 = `KAudioPolicyApplicationAudioStatePaused`

`ProfileSettingsMonitorServerImpl::InitializeAudioClientsListPSKeysL()`
defines both playing and paused state properties as byte arrays whose
preallocation is `sizeof(TAudioPolicyProcessIdListStruct)`.

The same struct is already validated as 88 bytes on this EKA2 ABI.

## HOMEONLY10 change

HOMEONLY10 adds only the newly proven key 4 dependency:

- category `0x101F457F`
- paused key `4`
- binary P&S
- package size `88`
- empty process list

HOMEONLY9 key 2 remains unchanged.

No key 3, key 5, or key 6 is added in this step because the HOMEONLY9 device log
has not yet proven those dependencies are needed.

Files:

- `apply_homeonly10_mmfaudiops_paused1.py`
- `test_homeonly10_mmfaudiops_paused1.py`

## Device PASS criteria

1. `[HOMEONLY10][MMF_AUDIO_PS] ... key=4 size=88` appears.
2. No warning that `0x101F457F:4` is undefined.
3. HOMEONLY9 key 2 remains defined.
4. Home remains alive.
5. A Home pointer wake is followed by `INPUT_GET` from the Home thread.
6. FIFO qsize drains instead of growing.
7. Telephone / Contacts / Home controls visibly react.
8. No HOMEONLY8 `0x00410000` access violation returns.
9. No regression of HOMEONLY8 WidgetRegistry registration.
10. No regression of HOMEONLY7 CenRep / AISCUT fix.
