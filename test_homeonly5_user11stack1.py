#!/usr/bin/env python3
from pathlib import Path
import sys

up = Path(sys.argv[1]).resolve()
svc = (up / "src/emu/kernel/src/svc.cpp").read_text(encoding="utf-8")

sig = "    BRIDGE_FUNC(std::int32_t, thread_kill, kernel::handle h, kernel::entity_exit_type etype, std::int32_t reason, eka2l1::ptr<desc8> reason_des) {"
start = svc.index(sig)
end = svc.index("\n    BRIDGE_FUNC(", start + len(sig))
body = svc[start:end]

assert "SYMBIAN-SYSTEMAPPS1 MENUUI4 THREADKILL:" in body
assert "[HOMEONLY5][USER11_CONTEXT]" in body
assert "[HOMEONLY5][USER11_FRAME]" in body
assert "[HOMEONLY5][USER11_STACK]" in body
assert "0x102750F0U" in body
assert "reason == 11" in body
assert 'exit_category == "USER"' in body

# Preserve the actual panic behavior.
assert body.count("thr->kill(etype, common::utf8_to_ucs2(exit_category), reason);") == 1

# Diagnostic delta may read registers/stack only. It must not write CPU state,
# suppress the panic, or alter the reason inside thread_kill.
for forbidden in (
    "cpu->set_reg(",
    "cpu->set_pc(",
    "cpu->set_cpsr(",
    "reason = 0;",
    "etype =",
):
    assert forbidden not in body

print("HOMEONLY5 USER11STACK1 contract: PASS")
print("semantic_change=NONE")
print("panic_behavior=PRESERVED")
