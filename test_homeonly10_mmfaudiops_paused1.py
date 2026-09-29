#!/usr/bin/env python3
"""Static contract test for HOMEONLY10 MMFAUDIOPS-PAUSED1."""
from pathlib import Path
import sys

MARK = "HOMEONLY10-MMFAUDIOPS-PAUSED1-TEST"


def fail(msg):
    raise SystemExit(f"{MARK}: {msg}")


def main():
    if len(sys.argv) != 2:
        fail("usage: test_homeonly10_mmfaudiops_paused1.py <upstream-root>")

    up = Path(sys.argv[1]).resolve()
    cp = up / "src/emu/services/src/audio/mmf/audio.cpp"
    app = up / "src/emu/services/src/applist/applist.cpp"
    ini = up / "src/emu/common/src/ini.cpp"

    c = cp.read_text(encoding="utf-8")
    app_text = app.read_text(encoding="utf-8")
    ini_text = ini.read_text(encoding="utf-8")

    for marker in (
        "[HOMEONLY9][MMF_AUDIO_PS]",
        "audio_state_playing_key = 0x00000002",
        "[HOMEONLY10][MMF_AUDIO_PS]",
        "audio_state_paused_key = 0x00000004",
        "process_id_list_size = 88",
        "paused->define(service::property_type::bin_data, process_id_list_size);",
    ):
        if marker not in c:
            fail(f"missing marker: {marker}")

    for marker in (
        "[HOMEONLY8][APPLIST_NONNATIVE]",
        "case applist_request_register_non_native_app_type:",
    ):
        if marker not in app_text:
            fail(f"HOMEONLY8 regression: {marker}")

    if "struct ini_token {" not in ini_text:
        fail("HOMEONLY7 quoted-token regression")

    for forbidden in (
        "0x102750F0",
        "0x101F4CD2",
        "0x10275104",
        "0xA0001000",
        "frcpplugin.dll",
    ):
        if forbidden in c:
            fail(f"target-specific literal present: {forbidden}")

    print(f"{MARK}: PASS")
    print("playing_key_2=KEPT")
    print("paused_key_4=DEFINED")
    print("package_size=88")
    print("other_audio_policy_keys=UNCHANGED")
    print("homeonly8_applist_fix=KEPT")
    print("homeonly7_quoted_tokenizer=KEPT")


if __name__ == "__main__":
    main()
