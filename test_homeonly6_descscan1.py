#!/usr/bin/env python3
from pathlib import Path
import sys

up=Path(sys.argv[1]).resolve()
svc=(up/"src/emu/kernel/src/svc.cpp").read_text(encoding="utf-8")

assert "[HOMEONLY5][USER11_CONTEXT]" in svc
assert "[HOMEONLY6][DESC_SCAN]" in svc
assert 'homeonly6_scan_desc("stack_slot"' in svc
assert 'homeonly6_scan_desc("stack_ptr"' in svc
assert "epoc::desc16" in svc
assert "get_max_length(caller_pr)" in svc
assert "get_pointer(caller_pr)" in svc
assert "behavior=OBSERVE_ONLY" in svc

# HOMEONLY6 may only inspect descriptor state. It must not mutate descriptor
# metadata, guest memory, CPU registers, panic reason or scheduler state.
block=svc[svc.index("// HOMEONLY6 DESCSCAN1"):svc.index("auto homeonly5_log_code_addr",svc.index("// HOMEONLY6 DESCSCAN1"))]
for forbidden in (
    "set_length(",
    "set_max_length(",
    "assign(",
    "memcpy(",
    "cpu->set_",
    "reason =",
    "etype =",
    "dewait(",
    "signal_request(",
):
    assert forbidden not in block, forbidden

# Existing panic path must remain.
assert "thr->kill(etype, common::utf8_to_ucs2(exit_category), reason);" in svc

print("HOMEONLY6 DESCSCAN1 contract: PASS")
print("semantic_change=NONE")
print("panic_behavior=PRESERVED")
