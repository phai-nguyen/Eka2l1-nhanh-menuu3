# CURRENT — HOMEONLY10 MMFAUDIOPS-PAUSED1 — 2026-09-30

## Scope

EKA2L1 emulator compatibility / preservation for Nokia 5800 RM-356 / Symbian S60v5.

Baseline remains:

- HOMEONLY2 / MENUUI36 NOJAVA / MANIC3
- HOMEONLY7 quote-aware CenRep tokenizer
- HOMEONLY8 AppList non-native registration
- HOMEONLY9 MMF playing-client P&S
- no NativeBoot / CompatBoot
- no CenRep 52 -> 26 change
- no firmware/AISCUT patch
- no panic suppression

Current research branch:

- `codex/menu3-homeonly10-mmfaudiops-paused1`

## HOMEONLY9 device result

HOMEONLY9 successfully removes the HOMEONLY8 access violation caused by missing
MMF property `0x101F457F:2`.

Confirmed:

- `[HOMEONLY9][MMF_AUDIO_PS] ... key=2 size=88 ... defined_now=1`
- no access violation at `0x00410000`
- no Home KERN-EXEC 3
- HOMEONLY8 WidgetRegistry/AppArc registration still succeeds
- Home stays alive
- iOS pointer path still reaches the real Home client

But Home does not consume the pointer after EventReady completion.

At the first Home tap:

```
INPUT_HIT ... client_thread=613
INPUT_FIFO_ENQUEUE ...
INPUT_FIFO ... qsize=1 listener_pending=1
[HOMEONLY4][EVENT_WAKE] ... pending=1
[HOMEONLY4][EVENT_WAKE] stage=after_complete ... status=0 ... request_count_after=0
```

No subsequent Home `INPUT_GET` occurs, so later pointer packets accumulate.

## Newly proven missing dependency

Immediately before MPXPlaybackServer startup HOMEONLY9 records:

```
Attach to property with category: 0x101f457f, key: 0x2
Attach to property with category: 0x101f457f, key: 0x4
Property (0x101f457f, 0x4) has not been defined before, undefined behavior may rise
Create session to unexist server: MPXPlaybackServer
```

Symbian source identifies key 4 as:

`KAudioPolicyApplicationAudioStatePaused`

and ProfileSettingsMonitor defines it with the same
`TAudioPolicyProcessIdListStruct` used by the playing-client property.

## HOMEONLY10 change

Add only the newly proven standard MMF property:

- category `0x101F457F`
- key `4`
- binary P&S
- package size `88`
- initial empty process list

HOMEONLY9 key 2 remains unchanged.

Files:

- `apply_homeonly10_mmfaudiops_paused1.py`
- `test_homeonly10_mmfaudiops_paused1.py`
- `docs/research/HOMEONLY10-MMFAUDIOPS-PAUSED-ROOTCAUSE-2026-09-30.md`

## Build

Build-host branch:

- `codex/m3home-homeonly2-build`

Workflow commit:

- `036d1f2d2a66f75ab811f29e5ac5ef76c568cee5`

GitHub Actions run:

- `36609632497`
- workflow: `Build HOMEONLY10 MMF Audio Paused P&S`
- result: GREEN / success
- job: `109547432433`

IPA artifact:

- name: `EKA2L1-HOMEONLY10-MMFAUDIOPS-PAUSED1-IPA`
- artifact id: `11053002050`
- filename: `EKA2L1-HOMEONLY10-MMFAUDIOPS-PAUSED1-unsigned.ipa`
- IPA SHA-256: `2ccd933d9cd7688e488eb38032ecb645f276f539630a9624eec56796af6acd21`

Artifact ZIP digest:

- `sha256:e168aad10f3c56135def5cae9f42059678f37bf8ed856a4e49c5ab532bfd4dee`

Audit artifact:

- id `11053345779`

## Device test

Prefer clean install.

1. Enter Menu3 -> Vào màn hình chính.
2. Wait until Home is stable.
3. Tap Telephone / Contacts / Home shortcuts repeatedly.
4. Confirm whether touch visually reacts.
5. If Telephone opens, exit it and confirm Home returns.
6. Keep the session alive for 1–2 minutes.
7. Export the standard logs.

PASS evidence:

1. `[HOMEONLY10][MMF_AUDIO_PS] ... key=4 size=88`
2. no warning that `0x101F457F:4` is undefined
3. no `0x00410000` access violation
4. Home remains alive
5. Home pointer wake is followed by Home `INPUT_GET`
6. FIFO does not monotonically accumulate
7. Telephone / Contacts respond visibly

If touch still stalls, inspect the next exact dependency after key 4; do not
preemptively define MMF keys 3/5/6 unless the next device log proves one of
them is required.
