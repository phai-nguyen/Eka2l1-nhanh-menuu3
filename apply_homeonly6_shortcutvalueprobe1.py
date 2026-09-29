#!/usr/bin/env python3
"""HOMEONLY6 SHORTCUTVALUEPROBE1.

Diagnostic-only probe for repo 0x10275104 after HOMEONLY5 proved that
aiscutplugin.dll panics USER/11 in TDes16::Copy after extracting a substring
with TDesC16::Mid.

The existing HOMEONLY1 GetString probe logs only the first 8 bytes.  This
delta logs the complete small shortcut value as hex plus an ASCII rendering.
It does not change repository data, returned data, lengths, completion codes,
focus, input, scheduler or guest execution.
"""
from pathlib import Path
import sys

MARK = "HOMEONLY6-SHORTCUTVALUEPROBE1"

def fail(msg):
    raise SystemExit(f"{MARK}: {msg}")

def main():
    if len(sys.argv) != 2:
        fail("usage: apply_homeonly6_shortcutvalueprobe1.py <upstream-root>")

    up = Path(sys.argv[1]).resolve()
    p = up / "src/emu/services/src/centralrepo/repo.cpp"
    if not p.is_file():
        fail(f"missing {p}")

    text = p.read_text(encoding="utf-8")

    for marker in (
        "[HOMEONLY1][CEN_GET_STRING] phase=pre_write",
        "[HOMEONLY1][CEN_GET_STRING] phase=complete",
        "[HOMEONLY1][CEN_DELETE_RANGE]",
    ):
        if marker not in text:
            fail(f"authority marker missing: {marker}")

    if "[HOMEONLY6][CEN_SHORTCUT_VALUE]" in text:
        print(f"{MARK}: already applied")
        return

    anchor = '''                LOG_WARN(SERVICE_CENREP,
                    "[HOMEONLY1][CEN_GET_STRING] phase=pre_write msg={} thread={} repo=0x{:08X} key=0x{:08X} entry_len={} dst_max={} write_len={} len_desc_present={} len_desc_max={} len_before={} hex8={:02X}{:02X}{:02X}{:02X}{:02X}{:02X}{:02X}{:02X} behavior=OBSERVE_ONLY",
                    ctx->msg->id, ctx->msg->own_thr->name(),
                    attach_repo ? attach_repo->uid : 0, the_key.value(),
                    entry->data.strd.length(), buffer_length, write_length,
                    wanted_length.has_value() ? 1 : 0, wanted_desc_max,
                    wanted_before,
                    preview_byte(0), preview_byte(1), preview_byte(2), preview_byte(3),
                    preview_byte(4), preview_byte(5), preview_byte(6), preview_byte(7));

'''

    if text.count(anchor) != 1:
        fail(f"GetString diagnostic anchor count={text.count(anchor)}")

    inject = r'''                // HOMEONLY6 SHORTCUTVALUEPROBE1: temporary diagnostic for the
                // Active Idle shortcut repository implicated by the exact
                // aiscutplugin.dll USER/11 call stack.  The value is observed
                // before the existing descriptor write and is never modified.
                if (attach_repo && attach_repo->uid == 0x10275104U
                    && entry->data.strd.length() <= 256) {
                    static constexpr char homeonly6_hex_digits[] =
                        "0123456789ABCDEF";

                    std::string homeonly6_hex;
                    homeonly6_hex.reserve(entry->data.strd.length() * 2);
                    for (const char raw_ch : entry->data.strd) {
                        const std::uint8_t b =
                            static_cast<std::uint8_t>(raw_ch);
                        homeonly6_hex.push_back(
                            homeonly6_hex_digits[(b >> 4) & 0xF]);
                        homeonly6_hex.push_back(
                            homeonly6_hex_digits[b & 0xF]);
                    }

                    // These repository values are UTF-16LE.  The current
                    // shortcut strings are ASCII-compatible ("localapp:...")
                    // so render readable low-byte characters while preserving
                    // the full hex form above as the authoritative payload.
                    std::string homeonly6_text;
                    homeonly6_text.reserve(
                        (entry->data.strd.length() + 1) / 2);
                    for (std::size_t i = 0;
                         i + 1 < entry->data.strd.length(); i += 2) {
                        const std::uint8_t lo =
                            static_cast<std::uint8_t>(
                                entry->data.strd[i]);
                        const std::uint8_t hi =
                            static_cast<std::uint8_t>(
                                entry->data.strd[i + 1]);

                        if (hi == 0 && lo >= 0x20 && lo <= 0x7E) {
                            homeonly6_text.push_back(
                                static_cast<char>(lo));
                        } else {
                            homeonly6_text.push_back('?');
                        }
                    }

                    LOG_WARN(SERVICE_CENREP,
                        "[HOMEONLY6][CEN_SHORTCUT_VALUE] repo=0x{:08X} key=0x{:08X} bytes={} utf16_units={} text='{}' hex={} behavior=OBSERVE_ONLY",
                        attach_repo->uid, the_key.value(),
                        entry->data.strd.length(),
                        (entry->data.strd.length() + 1) / 2,
                        homeonly6_text, homeonly6_hex);
                }

'''
    text=text.replace(anchor,anchor+inject,1)

    # Semantic-preservation gates.
    for needle in (
        "[HOMEONLY6][CEN_SHORTCUT_VALUE]",
        "behavior=OBSERVE_ONLY",
        "0x10275104U",
        "common::min(entry->data.strd.length(), buffer_length)",
        "ctx->write_data_to_descriptor_argument(",
        "ctx->complete(epoc::error_overflow);",
    ):
        if needle not in text:
            fail(f"postcondition missing: {needle}")

    p.write_text(text,encoding="utf-8")
    print(f"{MARK}: applied")
    print("target_repo=0x10275104")
    print("probe=FULL_GETSTRING_VALUE_HEX_AND_ASCII")
    print("behavior_change=NONE")
    print("cenrep_return_bytes=UNCHANGED")
    print("cenrep_actual_length=UNCHANGED")
    print("input_focus_scheduler=UNCHANGED")

if __name__ == "__main__":
    main()
