# CURRENT — HOMEONLY9 MMFAUDIOPS1 — 2026-09-30

## Project scope

EKA2L1 emulator compatibility / preservation for Nokia 5800 RM-356, Symbian S60v5.

This branch is strictly for Menu3 -> Home Screen compatibility analysis on firmware supplied by the project owner. It is not a security exploitation, intrusion, malware, persistence, credential, or third-party attack project.

## Authority

Semantic baseline remains:

- HOMEONLY2 / MENUUI36 NOJAVA / MANIC3
- HOMEONLY7 CenRep quoted-token compatibility fix
- HOMEONLY8 AppList non-native registration fix
- no NativeBoot / CompatBoot
- no CenRep 52 -> 26 conversion
- no firmware patch
- no AISCUT patch
- no panic suppression

Current research branch:

- `codex/menu3-homeonly9-mmfaudiops1`

Current HOMEONLY9 source HEAD:

- `82571f95e674346afe5a6f393990ab8dceca44c4`

Build-host branch:

- `codex/m3home-homeonly2-build`

Build-host workflow commit:

- `d4c1d15fd593f676a97dadbce1635bee73da3cf0`

## HOMEONLY8 device result

HOMEONLY8 proved several milestones at once:

1. Home Screen renders.
2. Home receives and consumes touch input.
3. Home content is interactive.
4. WidgetRegistry / AppArc non-native registration succeeds.
5. A later tap that appeared to open a Menu3 Options popup was not a normal Telephone launch result.

The critical remaining failure was Home liveness.

## Exact HOMEONLY8 crash

Immediately before Home termination:

- P&S attach: category `0x101F457F`, key `0x2`
- property absent / undefined
- access violation read at `0x00410000`
- Home stack chunk = `0x00400000 .. 0x0040FFFF`
- therefore `0x00410000` is exactly one byte past the stack mapping
- Home exits `KERN-EXEC 3`

EUser runtime base on this RM-356 firmware:

- `0x80295448`

Crash mapping:

- PC `0x8029A63C` -> EUser `+0x51F4`
- LR `0x80298A88` -> EUser `+0x3640`

The path is an 8-byte `RArrayBase::Append(void const*)` copy whose source points to the one-past-end stack address.

## Property identity

Symbian MMF source identifies:

- category `0x101F457F` = `KPSUidMMFAudioServer`
- key `2` = `KAudioPolicyApplicationAudioStatePlaying`

The package is `TAudioPolicyProcessIdListStruct`:

- `TInt iNumOfProcesses`
- `TProcessId iProcessList[10]`

On this EKA2 ABI its package size is 88 bytes.

On a real handset, `ProfileSettingsMonitor.exe` defines the MMF audio-policy P&S properties before consumers attach. HOMEONLY owns MMF through HLE and does not launch that native provider.

## HOMEONLY9 fix

HOMEONLY9 provides the missing standard MMF playing-client package in the HLE MMF audio server:

- category: `0x101F457F`
- key: `2`
- type: binary P&S
- size: `88` bytes
- initial process count: `0`
- package contents initially zeroed

No Home/Menu UID is special-cased.

Files:

- `apply_homeonly9_mmfaudiops1.py`
- `test_homeonly9_mmfaudiops1.py`
- `docs/research/HOMEONLY9-MMFAUDIOPS-ROOTCAUSE-2026-09-29.md`

## Independent confirmation

Public fork `zixing131/EKA2L1-WEB`, commit
`dc33445307de8130ab04061d2f798f31394f1ec1` ("Fix native S60 phone shell startup")
contains the same MMF property compatibility fix and explicitly documents the
5800 FRCP audio-policy list failure caused by an absent provider.

This independently matches the HOMEONLY8 device crash.

## HOMEONLY9 build

GitHub Actions run:

- `36599037719`
- workflow: `Build HOMEONLY9 MMF Audio P&S`
- result: GREEN / success
- job: `109511329305`

Build checks passed:

- HOMEONLY8 cache restored
- HOMEONLY7 quote-aware tokenizer retained
- HOMEONLY8 AppList fix retained
- HOMEONLY9 static contract PASS
- incremental iOS build PASS
- binary contains `[HOMEONLY9][MMF_AUDIO_PS]`
- NativeBoot / CompatBoot markers absent
- J2ME remains removed
- IPA packaging PASS

Artifact:

- name: `EKA2L1-HOMEONLY9-MMFAUDIOPS1-IPA`
- artifact id: `11048936564`
- IPA file: `EKA2L1-HOMEONLY9-MMFAUDIOPS1-unsigned.ipa`
- IPA SHA-256: `b487cfdf3c9a45eb2ada77898f14db978fe7859679149f7f88a7cb1a5b7e32bf`

Artifact ZIP digest:

- `sha256:b41f8defd8f44dab4806e70e03fd5d6071279bb9ae17e8bdda57080f68e780d0`

Do not confuse the artifact ZIP digest with the IPA file SHA-256.

Audit artifact:

- name: `EKA2L1-HOMEONLY9-MMFAUDIOPS1-AUDIT`
- artifact id: `11049121439`

## Device-test priority

Use a clean install for the first HOMEONLY9 run.

Test sequence:

1. Launch EKA2L1.
2. Enter Menu3.
3. Use the existing `Vào màn hình chính` path.
4. Wait for Home Screen to settle.
5. Touch Home widgets / shortcuts to confirm input remains live.
6. Tap `Telephone`.
7. If Telephone opens, select its Exit / Back path.
8. Verify that the still-live Home Screen is revealed again.
9. Keep the app alive for at least 1–2 minutes and repeat a few Home interactions.
10. Export the standard EKA2L1 logs.

## HOMEONLY9 PASS criteria

1. Marker `[HOMEONLY9][MMF_AUDIO_PS]` appears.
2. No warning that `0x101F457F:2` is undefined.
3. No access violation at `0x00410000`.
4. Home thread remains alive beyond the HOMEONLY8 failure point.
5. Pointer events continue to be consumed by Home.
6. Telephone launch is a genuine AppArc transition, not a Menu3 popup over a stale Home framebuffer.
7. Exiting Telephone reveals Home again.
8. HOMEONLY8 non-native AppList registration remains intact.
9. HOMEONLY7 full CenRep URI remains intact and AISCUT USER/11 does not return.

## If HOMEONLY9 still fails

Do not revert to NativeBoot/CompatBoot and do not alter CenRep 52 -> 26.

Use the new device logs to identify the next exact missing service/property/ABI contract. In particular, distinguish:

- Home process death vs. focus/z-order loss,
- genuine Telephone process launch vs. stale framebuffer,
- a new P&S dependency vs. the fixed `0x101F457F:2` dependency,
- guest panic vs. emulator-side KERN-EXEC / access violation.

The current fix should not be broadened to other audio-policy keys unless a new device log proves one is required.
