# Hướng 1 Menu3 → Home — CURRENT

Updated: 2026-09-29

Authoritative handoff:

`docs/handoff/NEWCHAT-HOMEONLY5-AISCUT-2026-09-29.md`

Repository:

`phai-nguyen/Eka2l1-nhanh-menuu3`

Current source branch:

`codex/menu3-homeonly5`

Build host:

`phai-nguyen/Eka2l1_bot_menu_simbiam` / `codex/m3home-homeonly2-build`

## Current baseline

HOMEONLY2 / MENUUI36 WINFOCUS1 + NOJAVA + MANIC3 is the correct semantic baseline.

Do not return to HOMEONLY1/MENUUI14.
Do not return to NativeBoot/CompatBoot/DirectHome unless explicitly requested.

Current runtime stack includes:
- M3HOME1 Menu3 -> real Home UID 0x102750F0
- CenRep transaction support
- generic DeleteRange
- GetString diagnostics
- HOMEONLY3 post-exit containment
- HOMEONLY4 EventReady/request-semaphore probes
- HOMEONLY5 USER/11 stack capture

## Latest device result

HOMEONLY5 reproduced real Home panic:

- category: USER
- reason: 11
- time: ~17:25:14.279
- immediately after CenRep GetString:
  - repo 0x10275104
  - key 0xA0001000
  - entry_len 52
  - dst_max 2048
  - write_len 52
  - status 0

HOMEONLY5 stack maps multiple frames into exact firmware module:

`Z:\\sys\\bin\\aiscutplugin.dll`

Important offsets:
- 0x6F64
- 0x475A
- 0x6F60
- 0x4A20
- 0x4E68
- 0x0D76

## Important ABI conclusion

Do NOT change CenRep length 52 -> 26.

Symbian source for `CRepository::Get(TDes16&, TInt&)` wraps the target in `TPtr8`, receives raw byte length, then divides both descriptor length and actual length by 2 client-side.

Therefore the CenRep server returning 52 bytes is ABI-consistent.

## Current task

Reverse-engineer the exact RM-356 `aiscutplugin.dll` and map the HOMEONLY5 stack offsets to functions/instructions/imports to find the descriptor operation that triggers USER/11.

Exact binary was extracted in the current runtime; hashes and paths are recorded in the authoritative handoff.

Do not suppress USER/11 and do not hardcode Home CenRep keys as a final fix.

## Build authority

HOMEONLY5:
- Actions run: 36553079575
- IPA SHA256:
  `0b7737d9f3e38403dc52698c15f506e142674b6e8066f347a41a6e32ab25391b`
- cache:
  `eka2l1-homeonly5-user11stack-macos15-v1`

Future HOMEONLY6 should restore HOMEONLY5 cache and apply only the next delta.
