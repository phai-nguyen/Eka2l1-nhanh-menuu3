#!/usr/bin/env python3
"""HOMEONLY1 CENREPGETSTRINGDIAG1.

Diagnostic-only probe for the Home Screen USER 11 boundary observed after
M3HOME2. Instruments Central Repository GetString without changing its
completion, copy length, repository contents, focus, TfxServer, or firmware.
"""
from __future__ import annotations

import sys
from pathlib import Path

MARK = "HOMEONLY1-CENREPGETSTRINGDIAG1"


def fail(msg: str) -> None:
    raise SystemExit(f"{MARK}: {msg}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: apply_m3home3_cenrepgetstringdiag1.py <upstream-root>")

    up = Path(sys.argv[1]).resolve()
    repo_path = up / "src/emu/services/src/centralrepo/repo.cpp"
    bridge_path = up / "src/emu/ios/src/emu_bridge.mm"
    if not repo_path.is_file() or not bridge_path.is_file():
        fail("missing baseline source")

    bridge = bridge_path.read_text(encoding="utf-8")
    if "[M3HOME1][APPARC_REQUEST]" not in bridge:
        fail("M3HOME1 baseline marker missing")

    repo = repo_path.read_text(encoding="utf-8")
    if "[HOMEONLY1][CEN_DELETE_RANGE]" not in repo:
        fail("M3HOME2 baseline marker missing")

    if "[HOMEONLY1][CEN_GET_STRING]" in repo:
        print(f"{MARK}: already applied")
        return

    method_start = "    void central_repo_client_subsession::get_value(service::ipc_context *ctx) {"
    method_end = "#ifdef _MSC_VER\n#pragma optimize(\"\", on)\n#endif"
    si = repo.find(method_start)
    if si < 0:
        fail("cannot locate get_value method")
    ei = repo.find(method_end, si)
    if ei < 0:
        fail("cannot locate get_value method end")

    method = repo[si:ei]
    case_start = method.find("        case cen_rep_get_string: {")
    if case_start < 0:
        fail("cannot locate cen_rep_get_string case")
    case_end = method.find("\n        default:", case_start)
    if case_end < 0:
        fail("cannot locate cen_rep_get_string case end")

    old_case = method[case_start:case_end]
    if "ctx->complete(epoc::error_overflow);" not in old_case:
        fail("expected GetString completion site is missing")
    if "ctx->write_data_to_descriptor_argument(1" not in old_case:
        fail("GetString write path missing")

    new_case = r'''        case cen_rep_get_string: {
            if (entry->data.etype == central_repo_entry_type::string) {
                std::optional<std::uint32_t> wanted_length =
                    ctx->get_argument_data_from_descriptor<std::uint32_t>(2);
                const std::uint32_t wanted_before =
                    wanted_length.has_value() ? wanted_length.value() : 0;
                const std::size_t wanted_desc_max =
                    ctx->get_argument_max_data_size(2);

                if (wanted_length.has_value()) {
                    wanted_length.value() =
                        static_cast<std::uint32_t>(entry->data.strd.length());
                    ctx->write_data_to_descriptor_argument<std::uint32_t>(
                        2, wanted_length.value());
                }

                const std::size_t buffer_length =
                    ctx->get_argument_max_data_size(1);
                const std::uint32_t write_length =
                    static_cast<std::uint32_t>(
                        common::min(entry->data.strd.length(), buffer_length));

                auto preview_byte = [&](const std::size_t index) -> std::uint32_t {
                    if (index >= entry->data.strd.length()) {
                        return 0;
                    }
                    return static_cast<std::uint32_t>(
                        static_cast<std::uint8_t>(entry->data.strd[index]));
                };

                LOG_WARN(SERVICE_CENREP,
                    "[HOMEONLY1][CEN_GET_STRING] phase=pre_write msg={} thread={} repo=0x{:08X} key=0x{:08X} entry_len={} dst_max={} write_len={} len_desc_present={} len_desc_max={} len_before={} hex8={:02X}{:02X}{:02X}{:02X}{:02X}{:02X}{:02X}{:02X} behavior=OBSERVE_ONLY",
                    ctx->msg->id, ctx->msg->own_thr->name(),
                    attach_repo ? attach_repo->uid : 0, the_key.value(),
                    entry->data.strd.length(), buffer_length, write_length,
                    wanted_length.has_value() ? 1 : 0, wanted_desc_max,
                    wanted_before,
                    preview_byte(0), preview_byte(1), preview_byte(2), preview_byte(3),
                    preview_byte(4), preview_byte(5), preview_byte(6), preview_byte(7));

                ctx->write_data_to_descriptor_argument(
                    1,
                    reinterpret_cast<std::uint8_t *>(&entry->data.strd[0]),
                    write_length);

                if (buffer_length < entry->data.strd.length()) {
                    LOG_WARN(SERVICE_CENREP,
                        "[HOMEONLY1][CEN_GET_STRING] phase=complete msg={} repo=0x{:08X} key=0x{:08X} status={} entry_len={} dst_max={} write_len={} behavior=OBSERVE_ONLY",
                        ctx->msg->id, attach_repo ? attach_repo->uid : 0,
                        the_key.value(), epoc::error_overflow,
                        entry->data.strd.length(), buffer_length, write_length);
                    ctx->complete(epoc::error_overflow);
                    return;
                }

                LOG_WARN(SERVICE_CENREP,
                    "[HOMEONLY1][CEN_GET_STRING] phase=complete msg={} repo=0x{:08X} key=0x{:08X} status={} entry_len={} dst_max={} write_len={} behavior=OBSERVE_ONLY",
                    ctx->msg->id, attach_repo ? attach_repo->uid : 0,
                    the_key.value(), epoc::error_none,
                    entry->data.strd.length(), buffer_length, write_length);
            } else {
                LOG_WARN(SERVICE_CENREP,
                    "[HOMEONLY1][CEN_GET_STRING] phase=type_mismatch msg={} repo=0x{:08X} key=0x{:08X} actual_type={} status={} behavior=OBSERVE_ONLY",
                    ctx->msg->id, attach_repo ? attach_repo->uid : 0,
                    the_key.value(), static_cast<int>(entry->data.etype),
                    epoc::error_argument);
                ctx->complete(epoc::error_argument);
                return;
            }

            break;
        }
'''

    method = method[:case_start] + new_case + method[case_end:]
    repo = repo[:si] + method + repo[ei:]
    repo_path.write_text(repo, encoding="utf-8")

    # Gates: diagnostics only; retain the original copy/error behavior.
    final = repo_path.read_text(encoding="utf-8")
    for needle in (
        "[HOMEONLY1][CEN_GET_STRING] phase=pre_write",
        "[HOMEONLY1][CEN_GET_STRING] phase=complete",
        "behavior=OBSERVE_ONLY",
        "common::min(entry->data.strd.length(), buffer_length)",
        "ctx->complete(epoc::error_overflow);",
        "ctx->complete(epoc::error_argument);",
        "[HOMEONLY1][CEN_DELETE_RANGE]",
    ):
        if needle not in final:
            fail(f"gate missing: {needle}")

    if "0x10275104" in new_case or "0x102750F0" in new_case:
        fail("Home-specific UID/repository hardcoded into diagnostic")

    print(f"{MARK}: applied")
    print("scope=CENREP_GETSTRING_DIAGNOSTICS_ONLY")
    print("copy_length=UNCHANGED_MIN_ENTRYLEN_DSTMAX")
    print("completion_semantics=UNCHANGED")
    print("repository_contents=UNCHANGED")
    print("home_specific_hardcode=NONE")
    print("focus_input=UNCHANGED")
    print("tfxserver=UNCHANGED")
    print("firmware=UNCHANGED")


if __name__ == "__main__":
    main()
