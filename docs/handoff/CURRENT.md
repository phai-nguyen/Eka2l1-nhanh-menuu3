# Hướng 1 Menu3 → Home — CURRENT

Updated: 2026-09-29

Authoritative handoff:

`docs/handoff/NEWCHAT-HOMEONLY7-CENREPQUOTED1-2026-09-29.md`

Repository:

`phai-nguyen/Eka2l1-nhanh-menuu3`

Current source branch:

`codex/menu3-homeonly7-cenrepquoted1`

Build host:

`phai-nguyen/Eka2l1_bot_menu_simbiam` / `codex/m3home-homeonly2-build`

## Baseline

HOMEONLY2 / MENUUI36 WINFOCUS1 + NOJAVA + MANIC3 remains the semantic baseline.

Preserve:
- M3HOME1 Menu3 → real Home UID `0x102750F0`
- HOMEONLY3 Home-exit containment
- HOMEONLY4 event/wake diagnostics
- HOMEONLY5 USER/11 diagnostics
- firmware RM-356 v60.0.003 unchanged
- NativeBoot/CompatBoot/J2ME absent

## Root cause — resolved

Exact RM-356 `aiscutplugin.dll` reverse engineering maps HOMEONLY5 `+0x475A` to the return after euser ordinal 953:

`TDes16::Copy(const TDesC16&)`

USER/11 is `ETDes16Overflow`.

AISCUT is parsing shortcut URI metadata. The stack proves the failing field is `iconid`; `+0x6F60/+0x6F64` are the static UTF-16 descriptor/literal `"iconid"`, not call frames.

The correct RM-356 shortcut value is:

`localapp:0x101F4CD2?iconid=270501603;7110&toolbar=1`

It is 51 UTF-16 units / 102 bytes.

The old EKA2L1 generic INI tokenizer split `=` even inside quoted tokens, truncating it to:

`localapp:0x101F4CD2?iconid`

This prefix is 26 UTF-16 units / exactly 52 bytes, matching HOMEONLY5 runtime `entry_len=52`.

AISCUT then receives query `iconid` without a value and reaches the invalid descriptor Copy path that panics USER/11.

## HOMEONLY7

HOMEONLY7 backports the current upstream quoted-token tokenizer behavior in `src/emu/common/src/ini.cpp`.

It does not change:
- CenRep Get/Set byte ABI
- 52→26 behavior
- repository keys
- firmware
- AISCUT
- focus/input/scheduler
- panic semantics

Source runtime fix:
`2f54cf599b5fd7f138768b77cc33edbac76eeae3`

Regression gates:
`fb2f19156273efe971e324b09a3d6817f0ed61f9`

## Build

Actions run:

`36564131999`

Result:

**GREEN**

Build source HEAD:
`fb2f19156273efe971e324b09a3d6817f0ed61f9`

IPA:
`EKA2L1-HOMEONLY7-CENREPQUOTED1-unsigned.ipa`

IPA SHA-256:
`7a73c76a1446c4c0e541ab8d837f7c87bbdc1f672b01e014c80f886b68a6ebf4`

Artifacts:
- IPA: `11031671131`
- AUDIT: `11031141639`

Cache:
`eka2l1-homeonly7-cenrepquoted1-macos15-v1`

## Next device test

Use a **clean CenRep state** for the authoritative HOMEONLY7 validation.

Reason: EKA2L1 loads persisted `.CRE` before ROM/default `.TXT`. Existing HOMEONLY5 app data may already contain the malformed 52-byte value, so an overlay install can keep reproducing USER/11 even though the parser fix is correct.

Preferred validation:
1. clean-install HOMEONLY7;
2. install the same RM-356 firmware;
3. Menu3 → **Vào màn hình chính**;
4. wait 15–20 seconds without touching;
5. if Home stays alive, test Telephone, Contacts and Set up e-mail one at a time;
6. export all four logs.

Do not use an old-state overlay failure as evidence against HOMEONLY7 until stale persisted CenRep state is excluded.

## Forbidden regressions

- Do not change CenRep 52→26.
- Do not hardcode key `0xA0001000`.
- Do not truncate URI values.
- Do not patch `aiscutplugin.dll`.
- Do not suppress USER/11.
- Do not return to NativeBoot/CompatBoot/DirectHome.
