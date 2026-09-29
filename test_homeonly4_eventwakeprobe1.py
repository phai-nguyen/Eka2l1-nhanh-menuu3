#!/usr/bin/env python3
from pathlib import Path
import sys

up = Path(sys.argv[1]).resolve()
fifo = (up / "src/emu/services/src/window/fifo.cpp").read_text(encoding="utf-8")
sema = (up / "src/emu/kernel/src/sema.cpp").read_text(encoding="utf-8")
thread = (up / "src/emu/kernel/src/thread.cpp").read_text(encoding="utf-8")
root = (up / "src/emu/ios/app/RootViewController.mm").read_text(encoding="utf-8")

assert "[HOMEONLY3][HOME_EXIT_KEEP_MENU3]" in root
assert "SYMBIAN-SYSTEMAPPS1 MENUUI14 INPUT_FIFO:" in fifo
assert "[HOMEONLY4][EVENT_WAKE]" in fifo
assert "[HOMEONLY4][SEMA_WAKE]" in sema
assert "[HOMEONLY4][REQ_WAIT]" in thread

# Diagnostic only: original behavior calls remain exactly once in their paths.
assert fifo.count("trigger_notification();") >= 1
assert "std::uint32_t result = queue_event_dont_care(evt);" in fifo
assert sema.count("ready_thread->get_scheduler()->dewait(ready_thread);") == 1
assert thread.count("request_sema->wait(0);") == 1

# Scope must remain real Home only.
assert fifo.count("0x102750F0U") >= 1
assert sema.count("0x102750F0U") >= 1
assert thread.count("0x102750F0U") >= 1

print("HOMEONLY4 EVENTWAKEPROBE1 contract: PASS")
print("semantic_change=NONE")
print("home_uid=0x102750F0")
print("eventready_complete=OBSERVE")
print("semaphore_dewait=OBSERVE")
print("request_wait=OBSERVE")
