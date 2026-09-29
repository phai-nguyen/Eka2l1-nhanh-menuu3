#!/usr/bin/env python3
"""HOMEONLY4 EVENTWAKEPROBE1 — diagnostic-only Home EventReady wake trace.

Device evidence from HOMEONLY3 proves iOS touch reaches the real Home window
(group 30 / Home UID3 0x102750F0), is queued in WindowServer, and the first
touch sees listener_pending=1.  Yet Home never calls GetEvent afterwards.

This patch changes no input/scheduler semantics.  It only traces:
  1. Home EventReady RequestStatus immediately before/after FIFO notification.
  2. The request semaphore path when a Home thread is actually dewoken.
  3. Home thread WaitForAnyRequest entry at the request-semaphore layer.
"""
from pathlib import Path
import sys

MARK = "HOMEONLY4-EVENTWAKEPROBE1"
HOME_UID = "0x102750F0U"

def fail(msg):
    raise SystemExit(f"{MARK}: {msg}")

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        fail(f"{label}: expected one anchor, found {n}")
    return text.replace(old, new, 1)

def add_include_once(text, anchor, include, label):
    if include in text:
        return text
    return replace_once(text, anchor, anchor + include, label)

def main():
    if len(sys.argv) != 2:
        fail("usage: apply_homeonly4_eventwakeprobe1.py <upstream-root>")
    up = Path(sys.argv[1]).resolve()

    fifo_p = up / "src/emu/services/src/window/fifo.cpp"
    sema_p = up / "src/emu/kernel/src/sema.cpp"
    root_p = up / "src/emu/ios/app/RootViewController.mm"
    for p in (fifo_p, sema_p, root_p):
        if not p.is_file():
            fail(f"required source missing: {p}")

    fifo = fifo_p.read_text(encoding="utf-8")
    sema = sema_p.read_text(encoding="utf-8")
    root = root_p.read_text(encoding="utf-8")

    # Authority gates: HOMEONLY3 on the clean MENUUI36/NOJAVA input stack.
    for needle in (
        "[HOMEONLY3][HOME_EXIT_KEEP_MENU3]",
        "[M3HOME1][TRIGGER]",
    ):
        if needle not in root:
            fail(f"HOMEONLY3 authority missing: {needle}")
    for needle in (
        "SYMBIAN-SYSTEMAPPS1 MENUUI14 INPUT_FIFO:",
        "SYMBIAN-SYSTEMAPPS1 MENUUI14 INPUT_WAKE:",
    ):
        if needle not in fifo:
            fail(f"MENUUI14 FIFO authority missing: {needle}")

    if "[HOMEONLY4][EVENT_WAKE]" in fifo or "[HOMEONLY4][SEMA_WAKE]" in sema:
        if "[HOMEONLY4][EVENT_WAKE]" in fifo and "[HOMEONLY4][SEMA_WAKE]" in sema:
            print(f"{MARK}: already applied")
            return
        fail("partial prior patch detected")

    behavior_before = {
        "fifo_queue": fifo.count("std::uint32_t result = queue_event_dont_care(evt);"),
        "fifo_trigger": fifo.count("trigger_notification();"),
        "sema_signal": sema.count("request_sema"),
        "sema_dewait": sema.count("ready_thread->get_scheduler()->dewait(ready_thread);"),
    }

    # fifo.cpp needs complete kernel thread/process types only for diagnostics.
    fifo = add_include_once(
        fifo,
        "#include <services/window/fifo.h>\n",
        "#include <kernel/process.h>\n#include <kernel/thread.h>\n",
        "FIFO kernel includes",
    )

    # Instrument only the existing touch queue path immediately around the
    # original trigger_notification(). nof is protected base_fifo state.
    old = """        trigger_notification();
        if (evt.type == epoc::event_code::touch) {
            LOG_WARN(SERVICE_WINDOW,
                "SYMBIAN-SYSTEMAPPS1 MENUUI14 INPUT_WAKE: handle={} evtype={} pointer={} trigger_notification=1",
                evt.handle, static_cast<int>(evt.adv_pointer_evt_.evtype),
                evt.adv_pointer_evt_.ptr_num);
        }
"""

    new = """        // HOMEONLY4 EVENTWAKEPROBE1: observe the exact EventReady listener that
        // the first Home touch is about to complete. Diagnostic only.
        kernel::thread *homeonly4_req_thr = nullptr;
        kernel::process *homeonly4_req_pr = nullptr;
        eka2l1::ptr<epoc::request_status> homeonly4_sts_ptr = 0;
        epoc::request_status *homeonly4_sts = nullptr;
        bool homeonly4_home_listener = false;
        std::int32_t homeonly4_req_before = 0;

        if ((evt.type == epoc::event_code::touch) && !nof.empty()) {
            homeonly4_req_thr = nof.requester;
            if (homeonly4_req_thr) {
                homeonly4_req_pr = homeonly4_req_thr->owning_process();
            }
            if (homeonly4_req_pr) {
                const auto homeonly4_uids = homeonly4_req_pr->get_uid_type();
                const std::uint32_t homeonly4_uid3 =
                    static_cast<std::uint32_t>(std::get<2>(homeonly4_uids));
                homeonly4_home_listener = (homeonly4_uid3 == 0x102750F0U);
            }
            if (homeonly4_home_listener) {
                homeonly4_sts_ptr = nof.sts;
                homeonly4_sts = homeonly4_sts_ptr.get(homeonly4_req_pr);
                homeonly4_req_before = homeonly4_req_thr->request_count();
                LOG_WARN(SERVICE_WINDOW,
                    "[HOMEONLY4][EVENT_WAKE] stage=before_complete handle={} evtype={} pointer={} qsize={} thread_uid={} thread={} status_ptr=0x{:08X} status={} flags=0x{:08X} active={} pending={} request_count={} listener_pending=1",
                    evt.handle, static_cast<int>(evt.adv_pointer_evt_.evtype),
                    evt.adv_pointer_evt_.ptr_num, q_.size(),
                    homeonly4_req_thr->unique_id(), homeonly4_req_thr->name(),
                    homeonly4_sts_ptr.ptr_address(),
                    homeonly4_sts ? homeonly4_sts->status : static_cast<std::int32_t>(0x7FFFFFFF),
                    homeonly4_sts ? static_cast<std::uint32_t>(homeonly4_sts->flags) : 0xFFFFFFFFU,
                    homeonly4_sts && (homeonly4_sts->flags & epoc::request_status::active) ? 1 : 0,
                    homeonly4_sts && (homeonly4_sts->flags & epoc::request_status::pending) ? 1 : 0,
                    homeonly4_req_before);
            }
        }

        trigger_notification();

        if (homeonly4_home_listener && homeonly4_req_thr) {
            epoc::request_status *homeonly4_after_sts =
                homeonly4_sts_ptr.get(homeonly4_req_pr);
            LOG_WARN(SERVICE_WINDOW,
                "[HOMEONLY4][EVENT_WAKE] stage=after_complete handle={} evtype={} pointer={} qsize={} thread_uid={} thread={} status_ptr=0x{:08X} status={} flags=0x{:08X} active={} pending={} request_count_before={} request_count_after={} listener_pending_after={}",
                evt.handle, static_cast<int>(evt.adv_pointer_evt_.evtype),
                evt.adv_pointer_evt_.ptr_num, q_.size(),
                homeonly4_req_thr->unique_id(), homeonly4_req_thr->name(),
                homeonly4_sts_ptr.ptr_address(),
                homeonly4_after_sts ? homeonly4_after_sts->status : static_cast<std::int32_t>(0x7FFFFFFF),
                homeonly4_after_sts ? static_cast<std::uint32_t>(homeonly4_after_sts->flags) : 0xFFFFFFFFU,
                homeonly4_after_sts && (homeonly4_after_sts->flags & epoc::request_status::active) ? 1 : 0,
                homeonly4_after_sts && (homeonly4_after_sts->flags & epoc::request_status::pending) ? 1 : 0,
                homeonly4_req_before, homeonly4_req_thr->request_count(),
                nof.empty() ? 0 : 1);
        }

        if (evt.type == epoc::event_code::touch) {
            LOG_WARN(SERVICE_WINDOW,
                "SYMBIAN-SYSTEMAPPS1 MENUUI14 INPUT_WAKE: handle={} evtype={} pointer={} trigger_notification=1",
                evt.handle, static_cast<int>(evt.adv_pointer_evt_.evtype),
                evt.adv_pointer_evt_.ptr_num);
        }
"""
    fifo = replace_once(fifo, old, new, "HOME EventReady complete probe")

    # semaphore.cpp: log only when signal() actually pops a waiting Home thread.
    sema = add_include_once(
        sema,
        "#include <kernel/kernel.h>\n",
        "#include <kernel/process.h>\n",
        "semaphore process include",
    )

    old = """                        kernel::thread *ready_thread = std::move(waits.top());
                        waits.pop();

                        assert(ready_thread->wait_obj == this);

                        ready_thread->end_timeout_early();
                        ready_thread->get_scheduler()->dewait(ready_thread);
                        ready_thread->wait_obj = nullptr;
"""
    new = """                        kernel::thread *ready_thread = std::move(waits.top());
                        waits.pop();

                        assert(ready_thread->wait_obj == this);

                        bool homeonly4_home_thread = false;
                        kernel::process *homeonly4_ready_pr =
                            ready_thread ? ready_thread->owning_process() : nullptr;
                        if (homeonly4_ready_pr) {
                            const auto homeonly4_uids = homeonly4_ready_pr->get_uid_type();
                            homeonly4_home_thread =
                                static_cast<std::uint32_t>(std::get<2>(homeonly4_uids))
                                    == 0x102750F0U;
                        }
                        if (homeonly4_home_thread) {
                            LOG_WARN(KERNEL,
                                "[HOMEONLY4][SEMA_WAKE] stage=before_dewait thread_uid={} thread={} sema_prev_count={} sema_current_count={} signal_count={} thread_state={} wait_obj_match={} waits_remaining={}",
                                ready_thread->unique_id(), ready_thread->name(),
                                prev_count, avail_count, signal_count,
                                static_cast<int>(ready_thread->current_state()),
                                ready_thread->wait_obj == this ? 1 : 0, waits.size());
                        }

                        ready_thread->end_timeout_early();
                        ready_thread->get_scheduler()->dewait(ready_thread);
                        ready_thread->wait_obj = nullptr;

                        if (homeonly4_home_thread) {
                            LOG_WARN(KERNEL,
                                "[HOMEONLY4][SEMA_WAKE] stage=after_dewait thread_uid={} thread={} sema_current_count={} request_count={} thread_state={} wait_obj_cleared={}",
                                ready_thread->unique_id(), ready_thread->name(),
                                avail_count, ready_thread->request_count(),
                                static_cast<int>(ready_thread->current_state()),
                                ready_thread->wait_obj == nullptr ? 1 : 0);
                        }
"""
    sema = replace_once(sema, old, new, "Home semaphore dewake probe")

    # Also log Home WaitForAnyRequest at the request-semaphore primitive. This
    # does not imply that the host function returns only after wake; it records
    # exactly when the Home thread consumes/decrements the request semaphore.
    thread_p = up / "src/emu/kernel/src/thread.cpp"
    if not thread_p.is_file():
        fail(f"required source missing: {thread_p}")
    thread = thread_p.read_text(encoding="utf-8")
    if "[HOMEONLY4][REQ_WAIT]" in thread:
        fail("thread probe already/partially present")
    thread = add_include_once(
        thread,
        "#include <kernel/kernel.h>\n",
        "#include <kernel/process.h>\n",
        "thread process include",
    )
    old = """        void thread::wait_for_any_request() {
            request_sema->wait(0);
        }
"""
    new = """        void thread::wait_for_any_request() {
            kernel::process *homeonly4_wait_pr = owning_process();
            bool homeonly4_home_thread = false;
            if (homeonly4_wait_pr) {
                const auto homeonly4_uids = homeonly4_wait_pr->get_uid_type();
                homeonly4_home_thread =
                    static_cast<std::uint32_t>(std::get<2>(homeonly4_uids))
                        == 0x102750F0U;
            }
            if (homeonly4_home_thread) {
                LOG_WARN(KERNEL,
                    "[HOMEONLY4][REQ_WAIT] stage=before_wait thread_uid={} thread={} request_count={} thread_state={}",
                    unique_id(), name(), request_count(), static_cast<int>(current_state()));
            }
            request_sema->wait(0);
            if (homeonly4_home_thread) {
                LOG_WARN(KERNEL,
                    "[HOMEONLY4][REQ_WAIT] stage=after_wait_primitive thread_uid={} thread={} request_count={} thread_state={}",
                    unique_id(), name(), request_count(), static_cast<int>(current_state()));
            }
        }
"""
    thread = replace_once(thread, old, new, "Home request wait probe")

    # Behavior-preservation gates.
    if fifo.count("trigger_notification();") != behavior_before["fifo_trigger"]:
        fail("FIFO trigger_notification count changed")
    if fifo.count("std::uint32_t result = queue_event_dont_care(evt);") != behavior_before["fifo_queue"]:
        fail("FIFO queue_event authority count changed")
    if sema.count("ready_thread->get_scheduler()->dewait(ready_thread);") != behavior_before["sema_dewait"]:
        fail("semaphore dewake authority count changed")
    if thread.count("request_sema->wait(0);") != 1:
        fail("request semaphore wait authority count changed")

    for needle, text in (
        ("[HOMEONLY4][EVENT_WAKE]", fifo),
        ("[HOMEONLY4][SEMA_WAKE]", sema),
        ("[HOMEONLY4][REQ_WAIT]", thread),
    ):
        if needle not in text:
            fail(f"post-apply marker missing: {needle}")

    fifo_p.write_text(fifo, encoding="utf-8")
    sema_p.write_text(sema, encoding="utf-8")
    thread_p.write_text(thread, encoding="utf-8")

    print(f"{MARK}: applied")
    print("behavior_change=NONE")
    print("target_uid=0x102750F0")
    print("probe=EVENTREADY_STATUS_TO_SEMAPHORE_TO_WAIT")
    print("touch_mapping=UNCHANGED")
    print("window_hit_test=UNCHANGED")
    print("event_fifo=UNCHANGED")
    print("scheduler=UNCHANGED")

if __name__ == "__main__":
    main()
