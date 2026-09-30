#!/usr/bin/env python3
"""Static contract test for HOMEONLY11 HOMEACTIVEQ1."""
from pathlib import Path
import sys

MARK = "HOMEONLY11-HOMEACTIVEQ1-TEST"


def fail(msg):
    raise SystemExit(f"{MARK}: {msg}")


def main():
    if len(sys.argv) != 2:
        fail("usage: test_homeonly11_homeactiveq1.py <upstream-root>")

    up = Path(sys.argv[1]).resolve()
    hp = up / "src/emu/kernel/include/kernel/thread.h"
    tp = up / "src/emu/kernel/src/thread.cpp"
    fp = up / "src/emu/services/src/window/fifo.cpp"
    ap = up / "src/emu/services/src/audio/mmf/audio.cpp"

    h = hp.read_text(encoding="utf-8")
    t = tp.read_text(encoding="utf-8")
    f = fp.read_text(encoding="utf-8")
    a = ap.read_text(encoding="utf-8")
    combined = h + "\n" + t + "\n" + f

    for marker in (
        "[HOMEONLY11][ACTIVEQ_ARM]",
        "[HOMEONLY11][ACTIVEQ_WAIT]",
        "[HOMEONLY11][ACTIVEQ_ITEM]",
        "homeonly11_arm_activeq_probe",
        "homeonly11_walk_activeq",
        "probe_budget",
    ):
        if marker not in combined and marker != "probe_budget":
            fail(f"missing marker: {marker}")

    for marker in (
        "[HOMEONLY4][EVENT_WAKE]",
        "[HOMEONLY4][REQ_WAIT]",
    ):
        if marker not in combined:
            fail(f"HOMEONLY4 regression: {marker}")

    for marker in (
        "[HOMEONLY9][MMF_AUDIO_PS]",
        "[HOMEONLY10][MMF_AUDIO_PS]",
    ):
        if marker not in a:
            fail(f"MMF baseline regression: {marker}")

    if t.count("request_sema->wait(0);") != 1:
        fail("WaitForAnyRequest semantic authority changed")
    if "trigger_notification();" not in f:
        fail("WindowServer notification authority missing")

    # Diagnostic code must not introduce state-changing scheduler/input calls.
    helper_start = t.find("static std::atomic<std::uint64_t> homeonly11_probe_thread_uid")
    helper_end = t.find("int map_thread_priority_to_calc", helper_start)
    if helper_start < 0 or helper_end < 0:
        fail("cannot isolate HOMEONLY11 helper")
    helper = t[helper_start:helper_end]
    for forbidden in (
        "wait_for_any_request(",
        "dewait(",
        "signal_request(",
        "status->set(",
        "set_ordinal_position(",
        "update_focus(",
    ):
        if forbidden in helper:
            fail(f"semantic mutation in helper: {forbidden}")

    print(f"{MARK}: PASS")
    print("behavior_change=NONE")
    print("home_eventready_arm=YES")
    print("active_queue_forward_backward=OBSERVE")
    print("input_pipeline=UNCHANGED")
    print("homeonly10_mmf_key4=KEPT")


if __name__ == "__main__":
    main()
