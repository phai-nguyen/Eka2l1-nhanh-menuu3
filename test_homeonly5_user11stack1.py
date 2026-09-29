#!/usr/bin/env python3
from pathlib import Path
import sys

up = Path(sys.argv[1]).resolve()
svc = (up / "src/emu/kernel/src/svc.cpp").read_text(encoding="utf-8")

assert "SYMBIAN-SYSTEMAPPS1 MENUUI4 THREADKILL:" in svc
assert "[HOMEONLY5][USER11_CONTEXT]" in svc
assert "[HOMEONLY5][USER11_FRAME]" in svc
assert "[HOMEONLY5][USER11_STACK]" in svc
assert "0x102750F0U" in svc
assert "reason == 11" in svc
assert 'exit_category == "USER"' in svc

# Preserve the actual panic behavior.
assert "thr->kill(etype, common::utf8_to_ucs2(exit_category), reason);" in svc

# Do not mutate descriptors / registers / scheduler in this diagnostic.
for forbidden in (
    "cpu->set_reg(",
    "cpu->set_pc(",
    "reason = 0;",
    "return epoc::error_none; // HOMEONLY5",
):
    assert forbidden not in svc

print("HOMEONLY5 USER11STACK1 contract: PASS")
print("semantic_change=NONE")
print("panic_behavior=PRESERVED")
