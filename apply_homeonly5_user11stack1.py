#!/usr/bin/env python3
"""HOMEONLY5 USER11STACK1 — diagnostic-only panic stack capture.

HOMEONLY4 device evidence proves the real Home process (UID3 0x102750F0)
still panics USER/11 before the later touch.  The last CenRep GetString
completes successfully and fits its destination (52 <= 2048), so do not
change CenRep semantics.  Capture the guest call context at thread_kill
for the exact Home USER/11 panic instead.

No guest state, descriptor, IPC, scheduler, focus or input behavior changes.
"""
from pathlib import Path
import sys

MARK = "HOMEONLY5-USER11STACK1"

def fail(msg):
    raise SystemExit(f"{MARK}: {msg}")

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        fail(f"{label}: expected one anchor, found {n}")
    return text.replace(old, new, 1)

def main():
    if len(sys.argv) != 2:
        fail("usage: apply_homeonly5_user11stack1.py <upstream-root>")

    up = Path(sys.argv[1]).resolve()
    svc_p = up / "src/emu/kernel/src/svc.cpp"
    if not svc_p.is_file():
        fail(f"missing {svc_p}")

    text = svc_p.read_text(encoding="utf-8")

    for marker in (
        "SYMBIAN-SYSTEMAPPS1 MENUUI4 THREADKILL:",
        "SYMBIAN-SYSTEMAPPS1 MENUUI22 SCHEDRUN_SVC:",
    ):
        if marker not in text:
            fail(f"authority marker missing: {marker}")

    if "[HOMEONLY5][USER11_CONTEXT]" in text:
        print(f"{MARK}: already applied")
        return

    sig = "    BRIDGE_FUNC(std::int32_t, thread_kill, kernel::handle h, kernel::entity_exit_type etype, std::int32_t reason, eka2l1::ptr<desc8> reason_des) {"
    start = text.find(sig)
    if start < 0:
        fail("thread_kill signature missing")
    end = text.find("\n    BRIDGE_FUNC(", start + len(sig))
    if end < 0:
        fail("thread_kill end anchor missing")
    body = text[start:end]

    anchor = "        thr->kill(etype, common::utf8_to_ucs2(exit_category), reason);\n"
    if body.count(anchor) != 1:
        fail(f"thread_kill dispatch anchor count={body.count(anchor)}")

    inject = r'''        // HOMEONLY5 USER11STACK1: capture the exact guest call context for
        // the real Home USER/11 panic. Diagnostic only; the original kill below
        // remains unchanged.
        bool homeonly5_target = false;
        if (caller_pr && target_pr && caller_pr == target_pr
            && static_cast<std::int32_t>(etype) == 2
            && reason == 11 && exit_category == "USER") {
            const auto homeonly5_uids = caller_pr->get_uid_type();
            homeonly5_target =
                static_cast<std::uint32_t>(std::get<2>(homeonly5_uids))
                    == 0x102750F0U;
        }

        if (homeonly5_target && cpu) {
            const std::uint32_t homeonly5_pc = cpu->get_pc();
            const std::uint32_t homeonly5_lr = cpu->get_reg(14);
            const std::uint32_t homeonly5_sp = cpu->get_reg(13);

            LOG_WARN(KERNEL,
                "[HOMEONLY5][USER11_CONTEXT] process={} thread={} pc=0x{:08X} lr=0x{:08X} sp=0x{:08X} cpsr=0x{:08X} request_count={} r0=0x{:08X} r1=0x{:08X} r2=0x{:08X} r3=0x{:08X} r4=0x{:08X} r5=0x{:08X} r6=0x{:08X} r7=0x{:08X} r8=0x{:08X} r9=0x{:08X} r10=0x{:08X} r11=0x{:08X} r12=0x{:08X}",
                caller_pr->name(), caller_thr ? caller_thr->name() : "<null>",
                homeonly5_pc, homeonly5_lr, homeonly5_sp,
                cpu->get_cpsr(), caller_thr ? caller_thr->request_count() : 0,
                cpu->get_reg(0), cpu->get_reg(1), cpu->get_reg(2), cpu->get_reg(3),
                cpu->get_reg(4), cpu->get_reg(5), cpu->get_reg(6), cpu->get_reg(7),
                cpu->get_reg(8), cpu->get_reg(9), cpu->get_reg(10), cpu->get_reg(11),
                cpu->get_reg(12));

            auto homeonly5_log_code_addr =
                [&](const char *role, const std::int32_t index,
                    const std::uint32_t raw) {
                    const std::uint32_t addr = raw & ~1U;
                    if (addr < 0x10000U) {
                        return;
                    }

                    codeseg_ptr seg = get_codeseg_from_addr(
                        kern, caller_pr, addr, false);
                    if (seg) {
                        const std::uint32_t base =
                            seg->get_code_run_addr(caller_pr);
                        LOG_WARN(KERNEL,
                            "[HOMEONLY5][USER11_FRAME] role={} index={} raw=0x{:08X} addr=0x{:08X} module={} base=0x{:08X} offset=0x{:08X}",
                            role, index, raw, addr,
                            common::ucs2_to_utf8(seg->get_full_path()),
                            base, addr - base);
                        return;
                    }

                    const auto path = get_dll_full_path(kern, addr);
                    if (path.has_value()) {
                        LOG_WARN(KERNEL,
                            "[HOMEONLY5][USER11_FRAME] role={} index={} raw=0x{:08X} addr=0x{:08X} module={} base=UNKNOWN offset=UNKNOWN",
                            role, index, raw, addr,
                            common::ucs2_to_utf8(path.value()));
                    }
                };

            homeonly5_log_code_addr("pc", -2, homeonly5_pc);
            homeonly5_log_code_addr("lr", -1, homeonly5_lr);

            // Snapshot a bounded window of the guest stack.  Emit every readable
            // raw word plus a second line only for values that resolve into a
            // loaded code segment / ROM image.  64 words = 256 bytes.
            for (std::int32_t i = 0; i < 64; ++i) {
                const std::uint32_t slot_addr =
                    homeonly5_sp
                    + static_cast<std::uint32_t>(i * sizeof(std::uint32_t));
                if (slot_addr < homeonly5_sp) {
                    break;
                }

                const std::uint32_t *slot =
                    eka2l1::ptr<std::uint32_t>(slot_addr).get(caller_pr);
                if (!slot) {
                    LOG_WARN(KERNEL,
                        "[HOMEONLY5][USER11_STACK_END] index={} slot=0x{:08X} reason=unmapped",
                        i, slot_addr);
                    break;
                }

                const std::uint32_t raw = *slot;
                LOG_WARN(KERNEL,
                    "[HOMEONLY5][USER11_STACK] index={} slot=0x{:08X} raw=0x{:08X}",
                    i, slot_addr, raw);
                homeonly5_log_code_addr("stack", i, raw);
            }
        }

'''
    body = body.replace(anchor, inject + anchor, 1)
    text = text[:start] + body + text[end:]

    # Diagnostic-only contract.
    if text.count(anchor) < 1:
        fail("original thread kill dispatch disappeared")
    for marker in (
        "[HOMEONLY5][USER11_CONTEXT]",
        "[HOMEONLY5][USER11_FRAME]",
        "[HOMEONLY5][USER11_STACK]",
        "0x102750F0U",
    ):
        if marker not in text:
            fail(f"postcondition missing: {marker}")

    svc_p.write_text(text, encoding="utf-8")
    print(f"{MARK}: applied")
    print("target=HOME_UID_0x102750F0_USER_11")
    print("behavior_change=NONE")
    print("panic_suppression=NO")
    print("cenrep_change=NONE")
    print("input_change=NONE")

if __name__ == "__main__":
    main()
