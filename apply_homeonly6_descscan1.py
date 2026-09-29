#!/usr/bin/env python3
"""HOMEONLY6 DESCSCAN1 — diagnostic-only descriptor scanner at Home USER/11.

HOMEONLY5 proved the panic crosses aiscutplugin.dll +0x475A immediately after
its TDes16::Copy import.  The missing fact is which source/target descriptor
was live at that call and whether its Length/MaxLength metadata is malformed.

This delta scans:
- every 4-byte stack slot in the HOMEONLY5 256-byte panic window as a possible
  inline Symbian descriptor;
- every stack word that looks like a guest pointer as a possible descriptor.

For plausible descriptors it logs type, length, max length, data pointer and a
small UTF-16 preview.  Guest memory is never modified.
"""
from pathlib import Path
import sys

MARK="HOMEONLY6-DESCSCAN1"

def fail(msg):
    raise SystemExit(f"{MARK}: {msg}")

def main():
    if len(sys.argv)!=2:
        fail("usage: apply_homeonly6_descscan1.py <upstream-root>")

    up=Path(sys.argv[1]).resolve()
    p=up/"src/emu/kernel/src/svc.cpp"
    if not p.is_file():
        fail(f"missing {p}")
    text=p.read_text(encoding="utf-8")

    for marker in (
        "[HOMEONLY5][USER11_CONTEXT]",
        "[HOMEONLY5][USER11_STACK]",
        "[HOMEONLY5][USER11_FRAME]",
    ):
        if marker not in text:
            fail(f"HOMEONLY5 authority missing: {marker}")

    if "[HOMEONLY6][DESC_SCAN]" in text:
        print(f"{MARK}: already applied")
        return

    anchor='''            auto homeonly5_log_code_addr =
                [&](const char *role, const std::int32_t index,
                    const std::uint32_t raw) {
'''

    if text.count(anchor)!=1:
        fail(f"HOMEONLY5 code-address anchor count={text.count(anchor)}")

    inject=r'''            // HOMEONLY6 DESCSCAN1: observe plausible 16-bit descriptors
            // that survived on the guest stack at the exact USER/11 panic.
            // This is deliberately read-only.
            auto homeonly6_scan_desc =
                [&](const char *origin, const std::int32_t index,
                    const std::uint32_t guest_addr) {
                    if (guest_addr < 0x10000U) {
                        return;
                    }

                    epoc::desc16 *candidate =
                        eka2l1::ptr<epoc::desc16>(guest_addr).get(caller_pr);
                    if (!candidate) {
                        return;
                    }

                    const std::uint32_t info = candidate->info;
                    const std::uint32_t dtype_raw = info >> 28;
                    const std::uint32_t len = info & 0x00FFFFFFU;

                    if (dtype_raw >= static_cast<std::uint32_t>(epoc::des_type_end)
                        || len > 4096U) {
                        return;
                    }

                    const epoc::des_type dtype =
                        static_cast<epoc::des_type>(dtype_raw);
                    const std::uint32_t max_len =
                        candidate->get_max_length(caller_pr);

                    if (max_len > 4096U
                        || ((dtype == epoc::ptr
                                || dtype == epoc::buf
                                || dtype == epoc::ptr_to_buf)
                            && max_len < len)) {
                        return;
                    }

                    char16_t *data = candidate->get_pointer(caller_pr);
                    if (!data && len != 0) {
                        return;
                    }

                    std::string preview;
                    std::string hex;
                    const std::uint32_t preview_units =
                        common::min<std::uint32_t>(len, 32U);
                    static constexpr char digits[] = "0123456789ABCDEF";
                    preview.reserve(preview_units);
                    hex.reserve(preview_units * 4);

                    for (std::uint32_t i = 0; i < preview_units; ++i) {
                        const std::uint16_t ch =
                            static_cast<std::uint16_t>(data[i]);

                        if (ch >= 0x20U && ch <= 0x7EU) {
                            preview.push_back(static_cast<char>(ch));
                        } else {
                            preview.push_back('.');
                        }

                        hex.push_back(digits[(ch >> 12) & 0xFU]);
                        hex.push_back(digits[(ch >> 8) & 0xFU]);
                        hex.push_back(digits[(ch >> 4) & 0xFU]);
                        hex.push_back(digits[ch & 0xFU]);
                    }

                    std::uint32_t raw_word1 = 0;
                    std::uint32_t raw_word2 = 0;
                    const std::uint32_t *word1 =
                        eka2l1::ptr<std::uint32_t>(guest_addr + 4U).get(caller_pr);
                    const std::uint32_t *word2 =
                        eka2l1::ptr<std::uint32_t>(guest_addr + 8U).get(caller_pr);
                    if (word1) {
                        raw_word1 = *word1;
                    }
                    if (word2) {
                        raw_word2 = *word2;
                    }

                    LOG_WARN(KERNEL,
                        "[HOMEONLY6][DESC_SCAN] origin={} index={} addr=0x{:08X} type={} len={} max={} info=0x{:08X} word1=0x{:08X} word2=0x{:08X} preview_units={} preview='{}' hex16={} behavior=OBSERVE_ONLY",
                        origin, index, guest_addr, dtype_raw, len, max_len,
                        info, raw_word1, raw_word2, preview_units,
                        preview, hex);
                };

            // The aiscutplugin frame contains both inline temporary descriptors
            // and pointers to caller-owned target descriptors.  Scan the same
            // bounded 64-word range HOMEONLY5 already snapshots.
            for (std::int32_t i = 0; i < 64; ++i) {
                const std::uint32_t slot_addr =
                    homeonly5_sp
                    + static_cast<std::uint32_t>(
                        i * sizeof(std::uint32_t));
                if (slot_addr < homeonly5_sp) {
                    break;
                }

                const std::uint32_t *slot =
                    eka2l1::ptr<std::uint32_t>(slot_addr).get(caller_pr);
                if (!slot) {
                    break;
                }

                // Stack-local TPtr/TBuf descriptors start directly at a stack
                // slot, while heap/object descriptors appear as raw pointers.
                homeonly6_scan_desc("stack_slot", i, slot_addr);
                homeonly6_scan_desc("stack_ptr", i, *slot);
            }

'''
    text=text.replace(anchor,inject+anchor,1)

    # Must remain diagnostic-only.
    for needle in (
        "[HOMEONLY6][DESC_SCAN]",
        "behavior=OBSERVE_ONLY",
        'homeonly6_scan_desc("stack_slot"',
        'homeonly6_scan_desc("stack_ptr"',
        "[HOMEONLY5][USER11_CONTEXT]",
    ):
        if needle not in text:
            fail(f"postcondition missing: {needle}")

    p.write_text(text,encoding="utf-8")
    print(f"{MARK}: applied")
    print("target=HOME_USER11_ONLY")
    print("descriptor_scan=STACK_INLINE_AND_POINTERS")
    print("guest_memory_write=NONE")
    print("panic_suppression=NO")
    print("cenrep_change=NONE")
    print("input_change=NONE")

if __name__=="__main__":
    main()
