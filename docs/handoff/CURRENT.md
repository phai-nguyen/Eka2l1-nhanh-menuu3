# Hướng 1 — Menu3 / Symbian emulation — CURRENT

Updated: 2026-09-29

Authoritative full project checkpoint:

[PROJECT-STATE-2026-09-29.md](PROJECT-STATE-2026-09-29.md)

Detailed HOMEONLY5/AISCUT handoff:

[NEWCHAT-HOMEONLY5-AISCUT-2026-09-29.md](NEWCHAT-HOMEONLY5-AISCUT-2026-09-29.md)

Repository:

`phai-nguyen/Eka2l1-nhanh-menuu3`

## Scope / Safety clarification

This is a **Symbian/S60v5 emulation and compatibility project**.

Primary purpose:

- boot and run the real Nokia 5800 RM-356 Menu3 environment inside EKA2L1;
- reproduce legitimate guest OS behavior required for application compatibility;
- diagnose firmware/application ABI, IPC, CenRep, WindowServer, input/focus and startup behavior;
- use the stable Menu3 baseline for controlled compatibility experiments such as launching the real Home Screen.

This project is **not related to exploitation, unauthorized access, malware, credential theft, malicious persistence, command-and-control, lateral movement, network attacks, phishing, data exfiltration or compromise of external systems**.

References to guest processes, startup, IPC, servers, firmware internals or persistent guest state describe behavior **inside the emulated Symbian environment**.

## Current baseline

The correct Hướng 1 baseline is:

`MENUUI36 WINFOCUS1 + NOJAVA + MANIC3`

Do not return to HOMEONLY1/MENUUI14.
Do not replay NativeBoot/CompatBoot/B29-B98 for this line unless explicitly requested.

Key UIDs:

- Menu3: `0x101F4CD2`
- Home Screen: `0x102750F0`

Current route:

```text
normal EKA2L1
    ↓
Menu3
    ↓
existing launcher/HLE path
    ↓
real Home Screen
```

The real Home Screen has rendered with Nokia wallpaper, status bar, Home content and a real WindowServer group/focus.

## Current promoted runtime state — HOMEONLY5

HOMEONLY5 is the latest promoted device-evidence state.

It adds targeted stack capture for Home panic:

- category: `USER`
- reason: `11`
- Home UID: `0x102750F0`

Build authority:

- workflow run: `36553079575`
- IPA SHA256: `0b7737d9f3e38403dc52698c15f506e142674b6e8066f347a41a6e32ab25391b`
- cache: `eka2l1-homeonly5-user11stack-macos15-v1`

Source baseline:

`codex/menu3-homeonly5`

Later experiment branches exist, but they are not automatically promoted without device evidence.

## Latest device findings

HOMEONLY5 produced two important runs:

1. Home remained alive for more than one minute with no USER/11 panic.
2. A later run reproduced USER/11 and captured a useful stack.

Immediately before the reproduced panic, CenRep GetString completed successfully for:

- repo `0x10275104`
- key `0xA0001000`
- entry length 52 bytes
- destination max 2048
- write length 52
- status 0

This is correlation, not proof of causation.

Multiple captured stack frames map into exact firmware module:

`Z:\\sys\\bin\\aiscutplugin.dll`

Priority offsets:

- `0x6F64`
- `0x475A`
- `0x6F60`
- `0x4A20`
- `0x4E68`
- `0x0D76`

## Important corrected conclusions

- HOMEONLY2/HOMEONLY3 device video did not prove an automatic crash to iOS Home; the user manually swiped to iOS Home.
- An Options menu drawn over the Home image does not prove Home touch works. Home may already have panicked, leaving a stale framebuffer while Menu3 receives the touch.
- TfxServer is not a hard barrier for this Menu3 → Home route because real Home has already rendered without it.
- CenRep string length 52 bytes must **not** be changed to 26 at the server boundary. Symbian's TDes16 client wrapper converts the raw byte length.
- Do not suppress USER/11 as a cosmetic workaround.
- Do not hardcode the observed Home CenRep key as a production fix.

## Next

Continue from HOMEONLY5:

1. reverse-engineer exact RM-356 `aiscutplugin.dll`;
2. map the captured offsets to functions/instructions/imports;
3. identify the descriptor operation causing USER/11;
4. distinguish guest-state/input failure from an EKA2L1 ABI mismatch;
5. add only a small generic diagnostic/fix delta when evidence supports it.

For full state, firmware hashes, build/cache chain, branch map and invariants, read:

[PROJECT-STATE-2026-09-29.md](PROJECT-STATE-2026-09-29.md)
