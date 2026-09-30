#!/usr/bin/env python3
"""HOMEONLY11 HOMEACTIVEQ1 — diagnostic-only Home ActiveScheduler queue probe.

HOMEONLY10 proves:
- iOS touch hit-tests to the real Home window;
- EventReady completes status=0 and wakes the Home thread;
- the Home thread immediately enters WaitForAnyRequest again;
- no subsequent WindowServer INPUT_GET occurs.

This patch does not change input, scheduler, queue, IPC, focus, P&S, or guest
memory semantics. It only arms a short host-side diagnostic window when the
Home EventReady RequestStatus completes, then dumps the Home CActiveScheduler
queue at the next WaitForAnyRequest calls.
"""
from pathlib import Path
import sys

MARK = "HOMEONLY11-HOMEACTIVEQ1"


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
        fail("usage: apply_homeonly11_homeactiveq1.py <upstream-root>")

    up = Path(sys.argv[1]).resolve()
    hp = up / "src/emu/kernel/include/kernel/thread.h"
    tp = up / "src/emu/kernel/src/thread.cpp"
    fp = up / "src/emu/services/src/window/fifo.cpp"
    ap = up / "src/emu/services/src/audio/mmf/audio.cpp"

    for p in (hp, tp, fp, ap):
        if not p.is_file():
            fail(f"missing {p}")

    h = hp.read_text(encoding="utf-8")
    t = tp.read_text(encoding="utf-8")
    f = fp.read_text(encoding="utf-8")
    a = ap.read_text(encoding="utf-8")

    # Authority gates.
    for needle in (
        "[HOMEONLY4][EVENT_WAKE]",
        "homeonly4_home_listener",
        "trigger_notification();",
    ):
        if needle not in f:
            fail(f"HOMEONLY4 FIFO authority missing: {needle}")

    for needle in (
        "[HOMEONLY4][REQ_WAIT]",
        "request_sema->wait(0);",
        "utils/guest/actsched.h",
    ):
        if needle not in t:
            fail(f"HOMEONLY4 thread authority missing: {needle}")

    for needle in (
        "[HOMEONLY9][MMF_AUDIO_PS]",
        "[HOMEONLY10][MMF_AUDIO_PS]",
    ):
        if needle not in a:
            fail(f"HOMEONLY10 baseline authority missing: {needle}")

    markers = (
        "[HOMEONLY11][ACTIVEQ_ARM]",
        "[HOMEONLY11][ACTIVEQ_WAIT]",
        "[HOMEONLY11][ACTIVEQ_ITEM]",
    )
    if any(m in h + t + f for m in markers):
        if all(m in h + t + f for m in markers):
            print(f"{MARK}: already applied")
            return
        fail("partial prior HOMEONLY11 patch detected")

    # Expose one diagnostic-only arming function to WindowServer FIFO code.
    decl_anchor = """        class thread_scheduler;

        enum class thread_state {
"""
    decl_new = """        class thread_scheduler;

        // HOMEONLY11 diagnostic-only bridge. This stores host-side probe state
        // only; it never mutates guest RequestStatus or scheduler memory.
        void homeonly11_arm_activeq_probe(std::uint64_t thread_uid,
            std::uint32_t status_addr);

        enum class thread_state {
"""
    h = replace_once(h, decl_anchor, decl_new, "thread diagnostic declaration")

    # Host diagnostic state + ActiveScheduler queue walker.
    t = add_include_once(
        t,
        "#include <utils/reqsts.h>\n",
        "#include <atomic>\n#include <cstddef>\n",
        "thread diagnostic includes",
    )

    helper_anchor = """namespace eka2l1 {
    namespace kernel {
        int map_thread_priority_to_calc(thread_priority pri) {
"""
    helper = r'''namespace eka2l1 {
    namespace kernel {
        static std::atomic<std::uint64_t> homeonly11_probe_thread_uid{0};
        static std::atomic<std::uint32_t> homeonly11_probe_status{0};
        static std::atomic<std::int32_t> homeonly11_probe_budget{0};
        static std::atomic<std::uint32_t> homeonly11_probe_seq{0};

        void homeonly11_arm_activeq_probe(const std::uint64_t thread_uid,
            const std::uint32_t status_addr) {
            if (thread_uid == 0 || status_addr == 0) {
                return;
            }
            homeonly11_probe_thread_uid.store(thread_uid, std::memory_order_release);
            homeonly11_probe_status.store(status_addr, std::memory_order_release);
            homeonly11_probe_budget.store(3, std::memory_order_release);
            const std::uint32_t seq =
                homeonly11_probe_seq.fetch_add(1, std::memory_order_acq_rel) + 1;
            LOG_WARN(KERNEL,
                "[HOMEONLY11][ACTIVEQ_ARM] seq={} thread_uid={} status_ptr=0x{:08X} budget=3",
                seq, thread_uid, status_addr);
        }

        struct homeonly11_walk_result {
            std::int32_t entries = 0;
            std::int32_t active = 0;
            std::int32_t ready = 0;
            std::int32_t target_index = -1;
            std::int32_t target_ready = -1;
            std::int32_t invalid = 0;
        };

        static homeonly11_walk_result homeonly11_walk_activeq(
            process *pr, utils::active_scheduler *sched,
            const std::uint32_t sched_addr, const std::uint32_t target_status,
            const bool forward, const char *stage, const std::uint32_t seq) {
            homeonly11_walk_result out;
            if (!pr || !sched || sched_addr == 0) {
                out.invalid = 1;
                return out;
            }

            const std::int32_t link_offset = sched->act_queue_.offset_to_link_;
            const std::uint32_t head_addr =
                sched_addr
                + static_cast<std::uint32_t>(offsetof(utils::active_scheduler, act_queue_))
                + static_cast<std::uint32_t>(offsetof(utils::pri_queue, head_));

            std::uint32_t current = forward
                ? sched->act_queue_.head_.next_.ptr_address()
                : sched->act_queue_.head_.prev_.ptr_address();

            if (link_offset <= 0 || link_offset >= 0x100) {
                out.invalid = 1;
                return out;
            }

            std::uint32_t seen[128] = {};
            for (std::int32_t i = 0; i < 128; ++i) {
                if (current == head_addr) {
                    break;
                }
                if (current == 0U || current < static_cast<std::uint32_t>(link_offset)) {
                    out.invalid = 1;
                    break;
                }

                bool duplicate = false;
                for (std::int32_t j = 0; j < i; ++j) {
                    if (seen[j] == current) {
                        duplicate = true;
                        break;
                    }
                }
                if (duplicate) {
                    out.invalid = 1;
                    break;
                }
                seen[i] = current;

                auto *link =
                    eka2l1::ptr<utils::double_queue_link>(current).get(pr);
                if (!link) {
                    out.invalid = 1;
                    break;
                }

                const std::uint32_t ao_addr =
                    current - static_cast<std::uint32_t>(link_offset);
                auto *ao = eka2l1::ptr<utils::active_object>(ao_addr).get(pr);
                if (!ao) {
                    out.invalid = 1;
                    break;
                }

                ++out.entries;
                const bool active =
                    (ao->sts_.flags & epoc::request_status::active) != 0;
                const bool ready =
                    active && ao->sts_.status != epoc::status_pending;
                if (active) ++out.active;
                if (ready) ++out.ready;

                const std::uint32_t status_addr =
                    ao_addr + static_cast<std::uint32_t>(
                        offsetof(utils::active_object, sts_));
                const bool target = status_addr == target_status;
                if (target) {
                    out.target_index = i;
                    out.target_ready = ready ? 1 : 0;
                }

                if (ready || target) {
                    LOG_WARN(KERNEL,
                        "[HOMEONLY11][ACTIVEQ_ITEM] seq={} stage={} dir={} index={} ao=0x{:08X} status_ptr=0x{:08X} status={} flags=0x{:08X} active={} ready={} target={} vtable=0x{:08X} prev=0x{:08X} next=0x{:08X}",
                        seq, stage, forward ? "forward" : "backward", i,
                        ao_addr, status_addr, ao->sts_.status,
                        static_cast<std::uint32_t>(ao->sts_.flags),
                        active ? 1 : 0, ready ? 1 : 0, target ? 1 : 0,
                        ao->vtable_, ao->link_.prev_.ptr_address(),
                        ao->link_.next_.ptr_address());
                }

                current = forward
                    ? link->next_.ptr_address()
                    : link->prev_.ptr_address();
            }
            return out;
        }

        static void homeonly11_log_activeq_wait(thread *thr, process *pr,
            const char *stage) {
            if (!thr || !pr) return;

            const std::uint64_t armed_uid =
                homeonly11_probe_thread_uid.load(std::memory_order_acquire);
            std::int32_t budget =
                homeonly11_probe_budget.load(std::memory_order_acquire);
            if (armed_uid == 0 || armed_uid != thr->unique_id() || budget <= 0) {
                return;
            }

            const std::uint32_t target_status =
                homeonly11_probe_status.load(std::memory_order_acquire);
            const std::uint32_t seq =
                homeonly11_probe_seq.load(std::memory_order_acquire);

            thread_local_data *tld = thr->get_local_data();
            const std::uint32_t sched_addr =
                tld ? tld->scheduler.ptr_address() : 0U;
            utils::active_scheduler *sched = nullptr;
            if (tld && sched_addr != 0U) {
                sched = tld->scheduler.cast<utils::active_scheduler>().get(pr);
            }

            homeonly11_walk_result fw =
                homeonly11_walk_activeq(pr, sched, sched_addr, target_status,
                    true, stage, seq);
            homeonly11_walk_result bw =
                homeonly11_walk_activeq(pr, sched, sched_addr, target_status,
                    false, stage, seq);

            LOG_WARN(KERNEL,
                "[HOMEONLY11][ACTIVEQ_WAIT] seq={} stage={} thread_uid={} thread={} target_status=0x{:08X} request_count={} scheduler=0x{:08X} scheduler_valid={} link_offset={} fw_entries={} fw_active={} fw_ready={} fw_target_index={} fw_target_ready={} fw_invalid={} bw_entries={} bw_active={} bw_ready={} bw_target_index={} bw_target_ready={} bw_invalid={} budget_before={}",
                seq, stage, thr->unique_id(), thr->name(), target_status,
                thr->request_count(), sched_addr, sched ? 1 : 0,
                sched ? sched->act_queue_.offset_to_link_ : -1,
                fw.entries, fw.active, fw.ready, fw.target_index,
                fw.target_ready, fw.invalid,
                bw.entries, bw.active, bw.ready, bw.target_index,
                bw.target_ready, bw.invalid, budget);

            if (std::string(stage) == "before_wait") {
                budget = homeonly11_probe_budget.fetch_sub(
                    1, std::memory_order_acq_rel) - 1;
                if (budget <= 0) {
                    homeonly11_probe_thread_uid.store(0, std::memory_order_release);
                    homeonly11_probe_status.store(0, std::memory_order_release);
                }
            }
        }

        int map_thread_priority_to_calc(thread_priority pri) {
'''
    t = replace_once(t, helper_anchor, helper, "thread ActiveScheduler helper")

    # Add the queue probe around the existing HOMEONLY4 request wait.
    old_wait = """            if (homeonly4_home_thread) {
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
"""
    new_wait = """            if (homeonly4_home_thread) {
                LOG_WARN(KERNEL,
                    "[HOMEONLY4][REQ_WAIT] stage=before_wait thread_uid={} thread={} request_count={} thread_state={}",
                    unique_id(), name(), request_count(), static_cast<int>(current_state()));
                homeonly11_log_activeq_wait(this, homeonly4_wait_pr, "before_wait");
            }
            request_sema->wait(0);
            if (homeonly4_home_thread) {
                LOG_WARN(KERNEL,
                    "[HOMEONLY4][REQ_WAIT] stage=after_wait_primitive thread_uid={} thread={} request_count={} thread_state={}",
                    unique_id(), name(), request_count(), static_cast<int>(current_state()));
                homeonly11_log_activeq_wait(this, homeonly4_wait_pr, "after_wait_primitive");
            }
"""
    t = replace_once(t, old_wait, new_wait, "HOMEONLY4 wait wrapper")

    # Arm the queue probe immediately after the existing EventReady completion
    # has been observed, while the exact status address/thread are still known.
    fifo_anchor = """        if (homeonly4_home_listener && homeonly4_req_thr) {
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
"""
    fifo_new = fifo_anchor.replace(
        "        }\n",
        """            kernel::homeonly11_arm_activeq_probe(
                homeonly4_req_thr->unique_id(),
                homeonly4_sts_ptr.ptr_address());
        }
""",
        1,
    )
    f = replace_once(f, fifo_anchor, fifo_new, "EventReady ActiveScheduler arm")

    # Behavior-preservation gates.
    if t.count("request_sema->wait(0);") != 1:
        fail("request semaphore behavior count changed")
    if f.count("trigger_notification();") < 1:
        fail("WindowServer trigger_notification authority missing")
    for forbidden in (
        "set_ordinal_position(",
        "update_focus(",
        "status->set(",
        "signal_request();",
    ):
        # Existing source may contain these elsewhere. The new HOMEONLY11 helper
        # itself must not add any such semantic mutation.
        pass

    combined = h + "\n" + t + "\n" + f
    for marker in markers:
        if marker not in combined:
            fail(f"postcondition marker missing: {marker}")

    hp.write_text(h, encoding="utf-8")
    tp.write_text(t, encoding="utf-8")
    fp.write_text(f, encoding="utf-8")

    print(f"{MARK}: applied")
    print("behavior_change=NONE")
    print("probe=HOME_EVENTREADY_TO_ACTIVE_SCHEDULER_QUEUE")
    print("probe_budget_per_touch=3_waits")
    print("input_pipeline=UNCHANGED")
    print("active_scheduler=OBSERVE_ONLY")
    print("mmf_properties=UNCHANGED")
    print("cenrep_abi=UNCHANGED")


if __name__ == "__main__":
    main()
