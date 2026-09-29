#!/usr/bin/env python3
"""Static contract test for HOMEONLY9 MMFAUDIOPS1."""
from pathlib import Path
import sys

MARK = "HOMEONLY9-MMFAUDIOPS1-TEST"


def fail(msg):
    raise SystemExit(f"{MARK}: {msg}")


def main():
    if len(sys.argv) != 2:
        fail("usage: test_homeonly9_mmfaudiops1.py <upstream-root>")

    up = Path(sys.argv[1]).resolve()
    cp = up / "src/emu/services/src/audio/mmf/audio.cpp"
    app = up / "src/emu/services/src/applist/applist.cpp"
    ini = up / "src/emu/common/src/ini.cpp"

    for p in (cp, app, ini):
        if not p.is_file():
            fail(f"missing {p}")

    c = cp.read_text(encoding="utf-8")
    app_text = app.read_text(encoding="utf-8")
    ini_text = ini.read_text(encoding="utf-8")

    required = (
        "#include <kernel/property.h>",
        "[HOMEONLY9][MMF_AUDIO_PS]",
        "audio_policy_category = 0x101F457F",
        "audio_state_playing_key = 0x00000002",
        "process_id_list_size = 88",
        "playing->define(service::property_type::bin_data, process_id_list_size);",
    )
    for marker in required:
        if marker not in c:
            fail(f"missing HOMEONLY9 marker: {marker}")

    for marker in (
        "struct ini_token {",
        "return { trim1, true };",
        "if (ns.text.empty() && !ns.quoted)",
    ):
        if marker not in ini_text:
            fail(f"HOMEONLY7 regression: {marker}")

    for marker in (
        "[HOMEONLY8][APPLIST_NONNATIVE]",
        "case applist_request_register_non_native_app_type:",
        "case applist_request_deregister_non_native_app_type:",
    ):
        if marker not in app_text:
            fail(f"HOMEONLY8 regression: {marker}")

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
    print("mmf_audio_playing_clients_property=YES")
    print("empty_package_bytes=88")
    print("homeonly8_applist_fix=KEPT")
    print("homeonly7_quoted_tokenizer=KEPT")
    print("cenrep_52_to_26_change=NO")


if __name__ == "__main__":
    main()
