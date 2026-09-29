# HOMEONLY9 — Home KERN-EXEC 3 / MMF audio P&S root cause — 2026-09-29

## Scope

EKA2L1 emulator compatibility and preservation for Nokia 5800 RM-356 / Symbian S60v5.

Baseline retained:

- HOMEONLY2 / MENUUI36 NOJAVA / MANIC3
- HOMEONLY7 quote-aware CenRep tokenizer fix
- HOMEONLY8 AppList non-native registration fix
- no NativeBoot / CompatBoot
- no CenRep 52 -> 26 conversion
- no firmware or AISCUT patch
- no panic suppression

## HOMEONLY8 device result

HOMEONLY8 is a real advance:

1. Home Screen renders.
2. Touch reaches and is consumed by the Home process.
3. System/Home content becomes interactive.
4. HOMEONLY8 marker confirms WidgetRegistry's AppArc registration is completed.

However, the Home process does not remain alive.

## Exact crash

Immediately before Home terminates:

```
Attach to property with category: 0x101f457f, key: 0x2
Property (0x101f457f, 0x2) has not been defined before, undefined behavior may rise
Access violation reading address 0x410000 in thread Home screen
pc=0x8029a63c
lr=0x80298a88
sp=0x0040fa1c
r0=0x00908b80
r1=0x00410000
r2=0x00000008
...
Thread Home screen ... KERN-EXEC, exit code: 3
```

Home's local stack chunk is:

- base: `0x00400000`
- size: `0x00010000`

Therefore `0x00410000` is exactly the one-past-end address of Home's 64 KiB
stack. The source pointer used by the faulting copy is precisely the stack end.

## Exact EUser path

The RM-356 EUser runtime code base is `0x80295448`.

Crash offsets:

- PC `0x8029A63C` -> EUser `+0x51F4`
- LR `0x80298A88` -> EUser `+0x3640`

EABI ordinal 48 is:

`RArrayBase::Append(void const*)`

The RM-356 implementation at `0x80298A60` prepares an append and calls the
internal copy helper at `0x8029A608`. The faulting instruction is:

```
0x8029A638  ldm r1,{r2,r3}
```

The append element size is 8 bytes. At the fault:

- source = `0x00410000`
- element size = 8

So the Home process is appending one 8-byte object from beyond the end of a
stack-backed array/package.

## Meaning of 0x101F457F:2

This is not a Home-specific property.

Symbian's `AudioClientsListPSKeys.h` defines:

- category `KPSUidMMFAudioServer = 0x101F457F`
- key 2 = `KAudioPolicyApplicationAudioStatePlaying`

`AudioClientsListPSData.h` defines the package as:

```cpp
struct TAudioPolicyProcessIdListStruct
    {
    TInt iNumOfProcesses;
    TProcessId iProcessList[10];
    };
```

On this EKA2 ABI the package occupies 88 bytes:

- 4-byte count
- ABI alignment/padding
- ten 64-bit process IDs

That is consistent with the faulting 8-byte RArray append.

## Missing handset provider

A normal handset boot runs `ProfileSettingsMonitor.exe`. Its
`InitializeAudioClientsListPSKeysL()` defines the MMF audio-policy byte-array
properties, including category `0x101F457F`, key 2, before consumers attach.

HOMEONLY uses HLE MMF services and does not start that native provider.

The HOMEONLY8 log therefore creates an undefined property only when the client
attaches. A native audio-policy observer then works with an uninitialized
stack package and eventually reads past the stack boundary.

## Independent EKA2L1 confirmation

The public EKA2L1-WEB fork commit
`dc33445307de8130ab04061d2f798f31394f1ec1` ("Fix native S60 phone shell
startup") independently contains the same compatibility fix in
`src/emu/services/src/audio/mmf/audio.cpp`.

Its own debugging notes explicitly state that the 5800 FRCP plug-in reads the
audio-policy process list and that an absent provider leaves the stack package
uninitialized. It initializes category `0x101F457F`, key 2 as an empty
88-byte package.

This independently matches the HOMEONLY8 device crash address, EUser append
path, and Symbian MMF source.

## Why the screenshot showed Menu3 after tapping Telephone

HOMEONLY3 deliberately keeps Menu3 alive below Home as a diagnostic fallback.

When Home dies with KERN-EXEC 3:

1. the last Home framebuffer remains visible;
2. Window Server focus returns to the surviving Menu3 group;
3. a later tap is delivered to Menu3, not Home;
4. Menu3's Options popup appears over the stale Home image;
5. selecting Exit exits Menu3, so there is no living Home process to reveal.

Therefore the screenshot is not Telephone's UI. It is Menu3's Options menu
rendered over Home's last frame.

## HOMEONLY9 fix

Use the HLE MMF audio server as the missing provider for the standard playing
client property:

- category `0x101F457F`
- key `2`
- byte-array package size `88`
- initial process count = 0
- no firmware/Home/Menu UID hard-code
- no input/focus workaround
- no crash suppression

Files:

- `apply_homeonly9_mmfaudiops1.py`
- `test_homeonly9_mmfaudiops1.py`

The fix is deliberately limited to the exact missing provider proven by the
HOMEONLY8 crash. Other audio-policy properties are not guessed in this step.

## Device PASS criteria

1. `[HOMEONLY9][MMF_AUDIO_PS] ... key=2 size=88` appears during service init.
2. No warning that `0x101F457F:2` was undefined.
3. No access violation at `0x00410000`.
4. Home thread/process remains alive after the point where HOMEONLY8 died.
5. Pointer events continue to be consumed by the Home client.
6. Tapping Telephone produces a real Home/AppArc launch transition rather than Menu3 Options.
7. Exiting a launched system app reveals the still-live Home screen.
8. HOMEONLY8 WidgetRegistry registration remains working.
9. HOMEONLY7 CenRep value remains full length and no AISCUT USER/11 returns.
