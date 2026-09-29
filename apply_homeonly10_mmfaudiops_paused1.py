#!/usr/bin/env python3
"""HOMEONLY10 MMFAUDIOPS-PAUSED1 — define the missing paused-client MMF P&S package.

HOMEONLY9 prevents the first FRCP stack overrun by providing
KAudioPolicyApplicationAudioStatePlaying (0x101F457F:2). The HOMEONLY9 device
log then proves the next standard MMF dependency: the same Home process
immediately attaches to 0x101F457F:4 and EKA2L1 reports it undefined.

Symbian AudioClientsListPSKeys.h identifies key 4 as
KAudioPolicyApplicationAudioStatePaused. ProfileSettingsMonitor defines it with
the same TAudioPolicyProcessIdListStruct size as key 2.

This patch adds only the dependency proven by the device log.
"""
from pathlib import Path
import sys

MARK = "HOMEONLY10-MMFAUDIOPS-PAUSED1"
SOURCE_MARK = "[HOMEONLY10][MMF_AUDIO_PS]"


def fail(msg):
    raise SystemExit(f"{MARK}: {msg}")


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        fail(f"{label}: expected one anchor, found {n}")
    return text.replace(old, new, 1)


def main():
    if len(sys.argv) != 2:
        fail("usage: apply_homeonly10_mmfaudiops_paused1.py <upstream-root>")

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

    if SOURCE_MARK in c:
        print(f"{MARK}: already applied")
        return

    # Preserve prior proven fixes.
    for needle in (
        "[HOMEONLY9][MMF_AUDIO_PS]",
        "audio_policy_category = 0x101F457F",
        "audio_state_playing_key = 0x00000002",
        "process_id_list_size = 88",
    ):
        if needle not in c:
            fail(f"HOMEONLY9 authority missing: {needle}")

    for needle in (
        "[HOMEONLY8][APPLIST_NONNATIVE]",
        "case applist_request_register_non_native_app_type:",
    ):
        if needle not in app_text:
            fail(f"HOMEONLY8 authority missing: {needle}")

    if "struct ini_token {" not in ini_text:
        fail("HOMEONLY7 quoted-token authority missing")

    anchor = """        LOG_WARN(SERVICE_MMFAUD,
            "[HOMEONLY9][MMF_AUDIO_PS] category=0x{:08X} key={} size={} existed={} defined_now={}",
            static_cast<std::uint32_t>(audio_policy_category),
            audio_state_playing_key, process_id_list_size,
            existed ? 1 : 0, defined_now ? 1 : 0);
"""

    injected = anchor + """
        // HOMEONLY9 device evidence shows the same RM-356 Home process next
        // attaches to KAudioPolicyApplicationAudioStatePaused (key 4). A real
        // ProfileSettingsMonitor defines this with the same process-id package.
        static constexpr std::int32_t audio_state_paused_key = 0x00000004;

        service::property *paused = kern->get_prop(
            audio_policy_category, audio_state_paused_key);
        const bool paused_existed = (paused != nullptr);

        if (!paused) {
            paused = kern->create<service::property>();
            paused->first = audio_policy_category;
            paused->second = audio_state_paused_key;
        }

        bool paused_defined_now = false;
        if (!paused->is_defined()) {
            paused->define(service::property_type::bin_data, process_id_list_size);
            paused_defined_now = true;
        }

        LOG_WARN(SERVICE_MMFAUD,
            "[HOMEONLY10][MMF_AUDIO_PS] category=0x{:08X} key={} size={} existed={} defined_now={}",
            static_cast<std::uint32_t>(audio_policy_category),
            audio_state_paused_key, process_id_list_size,
            paused_existed ? 1 : 0, paused_defined_now ? 1 : 0);
"""

    c = replace_once(c, anchor, injected, "homeonly9-log-anchor")

    for required in (
        SOURCE_MARK,
        "audio_state_paused_key = 0x00000004",
        "paused->define(service::property_type::bin_data, process_id_list_size);",
    ):
        if required not in c:
            fail(f"postcondition missing: {required}")

    # Keep this generic to the standard MMF P&S contract.
    for forbidden in (
        "0x102750F0",
        "0x101F4CD2",
        "0x10275104",
        "0xA0001000",
        "frcpplugin.dll",
    ):
        if forbidden in c:
            fail(f"target-specific literal leaked: {forbidden}")

    cp.write_text(c, encoding="utf-8")

    print(f"{MARK}: applied")
    print("category=0x101F457F")
    print("playing_key=2 kept")
    print("paused_key=4 added")
    print("package_size=88")
    print("initial_count=0")
    print("other_audio_policy_keys=UNCHANGED")
    print("input_pipeline=UNCHANGED")
    print("cenrep_abi=UNCHANGED")


if __name__ == "__main__":
    main()
