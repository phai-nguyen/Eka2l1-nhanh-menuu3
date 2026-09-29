#!/usr/bin/env python3
"""HOMEONLY9 MMFAUDIOPS1 — initialize the missing MMF audio playing-client P&S package.

HOMEONLY8 gets the RM-356 Home process far enough to load frcpplugin.dll. The
plugin then attaches to Symbian's standard MMF audio-policy property
0x101F457F:2 (KAudioPolicyApplicationAudioStatePlaying). In a normal handset
boot ProfileSettingsMonitor defines this byte-array package. HOMEONLY does not
start that native provider, so the package is absent and the 5800 plug-in walks
an uninitialized TAudioPolicyProcessIdList off the end of its stack.

Mirror the HLE MMF server behaviour used by the native-shell compatibility fix:
provide one empty 88-byte playing-client package before guest clients attach.
No Home/Menu/firmware UID is special-cased.
"""
from pathlib import Path
import sys

MARK = "HOMEONLY9-MMFAUDIOPS1"
SOURCE_MARK = "[HOMEONLY9][MMF_AUDIO_PS]"


def fail(msg):
    raise SystemExit(f"{MARK}: {msg}")


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        fail(f"{label}: expected one anchor, found {n}")
    return text.replace(old, new, 1)


def main():
    if len(sys.argv) != 2:
        fail("usage: apply_homeonly9_mmfaudiops1.py <upstream-root>")

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

    # Keep HOMEONLY7 and HOMEONLY8 as authority gates.
    for needle in (
        "struct ini_token {",
        "return { trim1, true };",
        "if (ns.text.empty() && !ns.quoted)",
    ):
        if needle not in ini_text:
            fail(f"HOMEONLY7 authority missing: {needle}")

    for needle in (
        "[HOMEONLY8][APPLIST_NONNATIVE]",
        "case applist_request_register_non_native_app_type:",
        "case applist_request_deregister_non_native_app_type:",
    ):
        if needle not in app_text:
            fail(f"HOMEONLY8 authority missing: {needle}")

    for needle in (
        '#include <kernel/kernel.h>',
        '#include <kernel/libmanager.h>',
        'static const char *MMF_AUDIO_SERVER_NAME = "!MMFAudioServer";',
        'mmf_audio_server::mmf_audio_server(eka2l1::system *sys, mmf_dev_server *dev)',
    ):
        if needle not in c:
            fail(f"MMF baseline authority missing: {needle}")

    c = replace_once(
        c,
        '#include <kernel/libmanager.h>\n',
        '#include <kernel/libmanager.h>\n#include <kernel/property.h>\n',
        "property-include",
    )

    old_ctor = """    mmf_audio_server::mmf_audio_server(eka2l1::system *sys, mmf_dev_server *dev)
        : service::typical_server(sys, MMF_AUDIO_SERVER_NAME)
        , dev_(dev)
        , flags_(0) {
    }
"""

    new_ctor = """    mmf_audio_server::mmf_audio_server(eka2l1::system *sys, mmf_dev_server *dev)
        : service::typical_server(sys, MMF_AUDIO_SERVER_NAME)
        , dev_(dev)
        , flags_(0) {
        // S60 audio-policy observers use this standard P&S package as
        // TAudioPolicyProcessIdListStruct: TInt count, ABI padding, then ten
        // 64-bit TProcessId entries = 88 bytes on EKA2. On a handset,
        // ProfileSettingsMonitor defines it. The HLE boot path owns MMF
        // services instead, so publish the equivalent empty package here.
        static constexpr std::int32_t audio_policy_category = 0x101F457F;
        static constexpr std::int32_t audio_state_playing_key = 0x00000002;
        static constexpr std::uint32_t process_id_list_size = 88;

        kernel_system *kern = sys->get_kernel_system();
        service::property *playing = kern->get_prop(
            audio_policy_category, audio_state_playing_key);
        const bool existed = (playing != nullptr);

        if (!playing) {
            playing = kern->create<service::property>();
            playing->first = audio_policy_category;
            playing->second = audio_state_playing_key;
        }

        bool defined_now = false;
        if (!playing->is_defined()) {
            // property::define() zero-initializes the backing vector in this
            // EKA2L1 baseline, so count=0 and every process-id slot is zero.
            playing->define(service::property_type::bin_data, process_id_list_size);
            defined_now = true;
        }

        LOG_WARN(SERVICE_MMFAUD,
            "[HOMEONLY9][MMF_AUDIO_PS] category=0x{:08X} key={} size={} existed={} defined_now={}",
            static_cast<std::uint32_t>(audio_policy_category),
            audio_state_playing_key, process_id_list_size,
            existed ? 1 : 0, defined_now ? 1 : 0);
    }
"""
    c = replace_once(c, old_ctor, new_ctor, "mmf-audio-constructor")

    # Generic-scope gates: only standard MMF P&S protocol constants are allowed.
    for forbidden in (
        "0x102750F0",  # Home / ailaunch
        "0x101F4CD2",  # Menu3
        "0x10275104",  # Home CenRep
        "0xA0001000",
        "frcpplugin.dll",
    ):
        if forbidden in c:
            fail(f"target-specific literal leaked into generic MMF fix: {forbidden}")

    for required in (
        SOURCE_MARK,
        "audio_policy_category = 0x101F457F",
        "audio_state_playing_key = 0x00000002",
        "process_id_list_size = 88",
        "service::property_type::bin_data",
    ):
        if required not in c:
            fail(f"postcondition missing: {required}")

    cp.write_text(c, encoding="utf-8")

    print(f"{MARK}: applied")
    print("provider=HLE_MMF_AUDIO")
    print("category=0x101F457F")
    print("key=2")
    print("package_size=88")
    print("initial_count=0")
    print("home_uid_hardcode=NONE")
    print("input_pipeline=UNCHANGED")
    print("cenrep_abi=UNCHANGED")


if __name__ == "__main__":
    main()
