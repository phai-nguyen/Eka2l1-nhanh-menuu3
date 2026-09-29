#!/usr/bin/env python3
"""M3HOME2 CENREPDELRANGE1.

Implements Symbian Central Repository EDeleteRange / opcode 0x21 on top of
M3HOME1 + B29 transaction support.

Device evidence:
  Home screen -> repo 0x10275104 -> TransactionStart(mode=2) -> opcode 0x21.

ABI verified against the open Symbian Central Repository source:
  arg0 = partial key
  arg1 = mask
  arg2 = TPckg<TUint32> error key
  arg3 = EKA2L1 subsession id

No Home UID/repository/key is hardcoded in the implementation.
"""
from __future__ import annotations

import sys
from pathlib import Path

MARK = "M3HOME2-CENREPDELRANGE1"


def fail(msg: str) -> None:
    raise SystemExit(f"{MARK}: {msg}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: apply_m3home2_cenrepdeleterange1.py <upstream-root>")

    up = Path(sys.argv[1]).resolve()
    cen_cpp = up / "src/emu/services/src/centralrepo/centralrepo.cpp"
    repo_h = up / "src/emu/services/include/services/centralrepo/repo.h"
    repo_cpp = up / "src/emu/services/src/centralrepo/repo.cpp"
    bridge = up / "src/emu/ios/src/emu_bridge.mm"

    for p in (cen_cpp, repo_h, repo_cpp, bridge):
        if not p.is_file():
            fail(f"missing baseline file: {p}")

    if "[M3HOME1][APPARC_REQUEST]" not in bridge.read_text(encoding="utf-8"):
        fail("M3HOME1 baseline marker missing")

    cc = cen_cpp.read_text(encoding="utf-8")
    if "M3HOME2::CenRepDeleteRange" not in cc:
        reg_old = (
            '        REGISTER_IPC(central_repo_server, redirect_msg_to_session, '
            'cen_rep_transaction_commit, "NBOOT2::CenRepTransactionCommit");\n'
            '        REGISTER_IPC(central_repo_server, redirect_msg_to_session, '
            'cen_rep_transaction_cancel, "CenRep::TransactionCancel");\n'
        )
        reg_new = (
            '        REGISTER_IPC(central_repo_server, redirect_msg_to_session, '
            'cen_rep_transaction_commit, "NBOOT2::CenRepTransactionCommit");\n'
            '        REGISTER_IPC(central_repo_server, redirect_msg_to_session, '
            'cen_rep_delete_range, "M3HOME2::CenRepDeleteRange");\n'
            '        REGISTER_IPC(central_repo_server, redirect_msg_to_session, '
            'cen_rep_transaction_cancel, "CenRep::TransactionCancel");\n'
        )
        cc = replace_once(cc, reg_old, reg_new, "DeleteRange registration")

    if "case cen_rep_delete_range:" not in cc:
        route_old = """        case cen_rep_transaction_cancel:
            cancel_transaction(ctx);
            break;

        case cen_rep_get_find_res:
"""
        route_new = """        case cen_rep_transaction_cancel:
            cancel_transaction(ctx);
            break;

        case cen_rep_delete_range:
            delete_range(ctx);
            break;

        case cen_rep_get_find_res:
"""
        cc = replace_once(cc, route_old, route_new, "DeleteRange route")

    cen_cpp.write_text(cc, encoding="utf-8")

    rh = repo_h.read_text(encoding="utf-8")
    if "#include <unordered_set>" not in rh:
        rh = replace_once(
            rh,
            "#include <unordered_map>\n#include <vector>\n",
            "#include <unordered_map>\n#include <unordered_set>\n#include <vector>\n",
            "unordered_set include",
        )

    if "std::unordered_set<std::uint32_t> deleted_keys;" not in rh:
        rh = replace_once(
            rh,
            """    struct central_repo_transactor {
        std::unordered_map<std::uint32_t, central_repo_entry> changes;
        central_repo_client_subsession *session;
    };
""",
            """    struct central_repo_transactor {
        std::unordered_map<std::uint32_t, central_repo_entry> changes;
        // M3HOME2: transaction-local tombstones. CenRep DeleteRange must not
        // mutate committed state until CommitTransaction succeeds.
        std::unordered_set<std::uint32_t> deleted_keys;
        central_repo_client_subsession *session;
    };
""",
            "transaction tombstones",
        )

    if "void delete_range(service::ipc_context *ctx);" not in rh:
        rh = replace_once(
            rh,
            """        void get_find_result(service::ipc_context *ctx);
        void start_transaction(service::ipc_context *ctx);
""",
            """        void get_find_result(service::ipc_context *ctx);
        void delete_range(service::ipc_context *ctx);
        void start_transaction(service::ipc_context *ctx);
""",
            "DeleteRange declaration",
        )
    repo_h.write_text(rh, encoding="utf-8")

    rp = repo_cpp.read_text(encoding="utf-8")

    # Make transaction reads/writes honor a staged deletion.
    if "[M3HOME2][CEN_TX_TOMBSTONE_RECREATE]" not in rp:
        get_anchor = """        if (active) {
            auto changed = transactor.changes.find(key);
            if (changed != transactor.changes.end()) {
                return &(changed->second);
            }

            auto result = std::find_if(attach_repo->entries.begin(), attach_repo->entries.end(),
"""
        get_replacement = """        if (active) {
            auto deleted = transactor.deleted_keys.find(key);
            if (deleted != transactor.deleted_keys.end()) {
                if (mode == 0) {
                    return nullptr;
                }

                // Set after Delete in the same transaction recreates the key
                // rather than resurrecting the committed value.
                transactor.deleted_keys.erase(deleted);
                central_repo_entry recreated{};
                recreated.key = key;
                recreated.metadata_val = attach_repo->get_default_meta_for_new_key(key);
                recreated.data.etype = central_repo_entry_type::none;
                auto inserted = transactor.changes.emplace(key, recreated);
                LOG_WARN(SERVICE_CENREP,
                    "[M3HOME2][CEN_TX_TOMBSTONE_RECREATE] repo=0x{:X} key=0x{:X}",
                    attach_repo->uid, key);
                return &(inserted.first->second);
            }

            auto changed = transactor.changes.find(key);
            if (changed != transactor.changes.end()) {
                return &(changed->second);
            }

            auto result = std::find_if(attach_repo->entries.begin(), attach_repo->entries.end(),
"""
        rp = replace_once(rp, get_anchor, get_replacement, "transaction tombstone read/write")

    if "[M3HOME2][CEN_DELETE_RANGE]" not in rp:
        insert_anchor = """    // NATIVEBOOT2-B29 CENREPTX1:
    // Implement the synchronous transaction path used by S60 UIKON/FEP.
"""
        delete_impl = r'''    void central_repo_client_subsession::delete_range(service::ipc_context *ctx) {
        const std::optional<std::uint32_t> partial_arg =
            ctx->get_argument_value<std::uint32_t>(0);
        const std::optional<std::uint32_t> mask_arg =
            ctx->get_argument_value<std::uint32_t>(1);

        if (!partial_arg.has_value() || !mask_arg.has_value()) {
            ctx->complete(epoc::error_argument);
            return;
        }

        const std::uint32_t partial_key = partial_arg.value();
        const std::uint32_t mask = mask_arg.value();
        const std::uint32_t normalized = partial_key & mask;

        // Symbian WriteOperationsL promotes/uses a read-write transaction.
        // B29 models read-only as a hard write lock.
        if (is_active()
            && (get_transaction_mode() == central_repo_transaction_mode::read_only)) {
            ctx->write_data_to_descriptor_argument<std::uint32_t>(2, partial_key);
            LOG_WARN(SERVICE_CENREP,
                "[M3HOME2][CEN_DELETE_RANGE] repo=0x{:X} partial=0x{:X} mask=0x{:X} active=1 matched=0 result=LOCKED",
                attach_repo->uid, partial_key, mask);
            ctx->complete(epoc::error_locked);
            return;
        }

        std::vector<std::uint32_t> matches;
        matches.reserve(attach_repo->entries.size() + transactor.changes.size());

        auto maybe_add = [&](const std::uint32_t key) {
            if ((key & mask) != normalized) {
                return;
            }
            if (is_active() && (transactor.deleted_keys.find(key) != transactor.deleted_keys.end())) {
                return;
            }
            if (std::find(matches.begin(), matches.end(), key) == matches.end()) {
                matches.push_back(key);
            }
        };

        for (const central_repo_entry &entry : attach_repo->entries) {
            maybe_add(entry.key);
        }
        if (is_active()) {
            for (const auto &change : transactor.changes) {
                maybe_add(change.first);
            }
        }

        if (matches.empty()) {
            // Symbian CRepository::Delete(partial,mask,errorKey) returns
            // KErrNotFound without failing the surrounding transaction.
            ctx->write_data_to_descriptor_argument<std::uint32_t>(2, partial_key);
            LOG_WARN(SERVICE_CENREP,
                "[M3HOME2][CEN_DELETE_RANGE] repo=0x{:X} partial=0x{:X} mask=0x{:X} active={} matched=0 result=NOT_FOUND",
                attach_repo->uid, partial_key, mask, is_active());
            ctx->complete(epoc::error_not_found);
            return;
        }

        if (is_active()) {
            for (const std::uint32_t key : matches) {
                // A staged Set/Create followed by Delete is represented only by
                // the tombstone. Commit decides whether the key needs a
                // persistent deleted-settings entry.
                transactor.changes.erase(key);
                transactor.deleted_keys.insert(key);
            }

            LOG_WARN(SERVICE_CENREP,
                "[M3HOME2][CEN_DELETE_RANGE] repo=0x{:X} partial=0x{:X} mask=0x{:X} active=1 matched={} result=STAGED",
                attach_repo->uid, partial_key, mask, matches.size());
            ctx->complete(epoc::error_none);
            return;
        }

        std::vector<std::uint32_t> deleted_now;
        deleted_now.reserve(matches.size());
        for (const std::uint32_t key : matches) {
            auto ite = std::find_if(attach_repo->entries.begin(), attach_repo->entries.end(),
                [&](const central_repo_entry &entry) { return entry.key == key; });
            if (ite == attach_repo->entries.end()) {
                continue;
            }

            attach_repo->entries.erase(ite);
            if (std::find(attach_repo->deleted_settings.begin(),
                    attach_repo->deleted_settings.end(), key)
                == attach_repo->deleted_settings.end()) {
                attach_repo->deleted_settings.push_back(key);
            }
            deleted_now.push_back(key);
        }

        if (deleted_now.empty()) {
            ctx->write_data_to_descriptor_argument<std::uint32_t>(2, partial_key);
            ctx->complete(epoc::error_not_found);
            return;
        }

        write_changes(ctx->sys->get_io_system(), ctx->sys->get_device_manager());
        for (const std::uint32_t key : deleted_now) {
            modification_success(key);
        }

        LOG_WARN(SERVICE_CENREP,
            "[M3HOME2][CEN_DELETE_RANGE] repo=0x{:X} partial=0x{:X} mask=0x{:X} active=0 matched={} result=COMMITTED",
            attach_repo->uid, partial_key, mask, deleted_now.size());
        ctx->complete(epoc::error_none);
    }

'''
        rp = replace_once(rp, insert_anchor, delete_impl + insert_anchor, "DeleteRange implementation")

    # New transactions start with no stale tombstones.
    start_old = """        transactor.changes.clear();
        set_transaction_mode(mode);
        set_active(true);
"""
    start_new = """        transactor.changes.clear();
        transactor.deleted_keys.clear();
        set_transaction_mode(mode);
        set_active(true);
"""
    if "transactor.deleted_keys.clear();\n        set_transaction_mode(mode);" not in rp:
        rp = replace_once(rp, start_old, start_new, "transaction start tombstone clear")

    # Replace the full B29 commit method by stable function boundaries.
    # B83 later wraps completion calls for diagnostics, so matching the exact
    # body is intentionally avoided here.
    if "[M3HOME2][CEN_DELETE_COMMIT]" not in rp:
        commit_start = "    void central_repo_client_subsession::commit_transaction(service::ipc_context *ctx) {"
        cancel_start = "    void central_repo_client_subsession::cancel_transaction(service::ipc_context *ctx) {"
        si = rp.find(commit_start)
        ei = rp.find(cancel_start, si + len(commit_start))
        if si < 0 or ei < 0:
            fail("cannot locate bounded commit_transaction method")

        commit_method = r'''    void central_repo_client_subsession::commit_transaction(service::ipc_context *ctx) {
        if (!is_active()) {
            LOG_ERROR(SERVICE_CENREP,
                "[NBOOT2][CEN_TX_COMMIT] repo=0x{:X} active=false completion={}",
                attach_repo->uid, epoc::error_argument);
            complete_central_repo_ipc(ctx, epoc::error_argument);
            return;
        }

        io_system *io = ctx->sys->get_io_system();
        device_manager *mngr = ctx->sys->get_device_manager();

        std::vector<std::uint32_t> changed_keys;
        changed_keys.reserve(transactor.changes.size());
        std::vector<std::uint32_t> deleted_keys;
        deleted_keys.reserve(transactor.deleted_keys.size());

        // Apply transaction-local tombstones first. A key present in the
        // committed/ROM-derived view needs a persisted deleted-settings marker
        // so it does not reappear when the repository is reopened.
        for (const std::uint32_t key : transactor.deleted_keys) {
            auto result = std::find_if(attach_repo->entries.begin(), attach_repo->entries.end(),
                [&](const central_repo_entry &entry) { return entry.key == key; });

            if (result != attach_repo->entries.end()) {
                attach_repo->entries.erase(result);
                if (std::find(attach_repo->deleted_settings.begin(),
                        attach_repo->deleted_settings.end(), key)
                    == attach_repo->deleted_settings.end()) {
                    attach_repo->deleted_settings.push_back(key);
                }
                deleted_keys.push_back(key);
            }

            // Delete wins over any staged write to the same key.
            transactor.changes.erase(key);
        }

        for (auto &change : transactor.changes) {
            const std::uint32_t key = change.first;
            central_repo_entry &staged = change.second;

            auto result = std::find_if(attach_repo->entries.begin(), attach_repo->entries.end(),
                [&](const central_repo_entry &entry) { return entry.key == key; });

            if (result != attach_repo->entries.end()) {
                *result = staged;
            } else {
                attach_repo->entries.push_back(staged);
            }

            auto &deleted = attach_repo->deleted_settings;
            deleted.erase(std::remove(deleted.begin(), deleted.end(), key), deleted.end());
            changed_keys.push_back(key);
        }

        const std::uint32_t changed_count = static_cast<std::uint32_t>(
            changed_keys.size() + deleted_keys.size());

        transactor.changes.clear();
        transactor.deleted_keys.clear();
        set_active(false);

        // Persist once after all staged sets and deletes are installed.
        write_changes(io, mngr);

        for (const std::uint32_t key : changed_keys) {
            modification_success(key);
        }
        for (const std::uint32_t key : deleted_keys) {
            modification_success(key);
        }

        if (!deleted_keys.empty()) {
            LOG_WARN(SERVICE_CENREP,
                "[M3HOME2][CEN_DELETE_COMMIT] repo=0x{:X} deleted={} changed={}",
                attach_repo->uid, deleted_keys.size(), changed_keys.size());
        }

        // Preserve the B29 contract currently consumed by the guest.
        ctx->write_data_to_descriptor_argument<std::uint32_t>(0, changed_count);

        LOG_WARN(SERVICE_CENREP,
            "[NBOOT2][CEN_TX_COMMIT] repo=0x{:X} changed={} active=false completion=0",
            attach_repo->uid, changed_count);
        complete_central_repo_ipc(ctx, epoc::error_none);
    }

'''
        rp = rp[:si] + commit_method + rp[ei:]

    cancel_old = """        const std::size_t discarded = transactor.changes.size();
        transactor.changes.clear();
        set_active(false);

        LOG_WARN(SERVICE_CENREP,
            "[NBOOT2][CEN_TX_CANCEL] repo=0x{:X} discarded={} active=false completion=0",
            attach_repo->uid, discarded);
"""
    cancel_new = """        const std::size_t discarded =
            transactor.changes.size() + transactor.deleted_keys.size();
        transactor.changes.clear();
        transactor.deleted_keys.clear();
        set_active(false);

        LOG_WARN(SERVICE_CENREP,
            "[NBOOT2][CEN_TX_CANCEL] repo=0x{:X} discarded={} active=false completion=0",
            attach_repo->uid, discarded);
"""
    if "transactor.changes.size() + transactor.deleted_keys.size()" not in rp:
        rp = replace_once(rp, cancel_old, cancel_new, "transaction cancel DeleteRange support")

    repo_cpp.write_text(rp, encoding="utf-8")

    # Post-apply gates.
    cc = cen_cpp.read_text(encoding="utf-8")
    rh = repo_h.read_text(encoding="utf-8")
    rp = repo_cpp.read_text(encoding="utf-8")

    for needle in (
        'cen_rep_delete_range, "M3HOME2::CenRepDeleteRange"',
        "case cen_rep_delete_range:",
        "delete_range(ctx);",
    ):
        if needle not in cc:
            fail(f"centralrepo.cpp gate missing: {needle}")

    for needle in (
        "#include <unordered_set>",
        "std::unordered_set<std::uint32_t> deleted_keys;",
        "void delete_range(service::ipc_context *ctx);",
    ):
        if needle not in rh:
            fail(f"repo.h gate missing: {needle}")

    for needle in (
        "[M3HOME2][CEN_DELETE_RANGE]",
        "[M3HOME2][CEN_DELETE_COMMIT]",
        "[M3HOME2][CEN_TX_TOMBSTONE_RECREATE]",
        "transactor.deleted_keys.clear();",
        "ctx->write_data_to_descriptor_argument<std::uint32_t>(2, partial_key);",
        "(key & mask) != normalized",
    ):
        if needle not in rp:
            fail(f"repo.cpp gate missing: {needle}")

    # Keep this generic: the observed Home repo is evidence, not an implementation constant.
    if "0x10275104" in rp or "0x102750F0" in rp:
        fail("Home-specific UID/repository hardcoded into generic CenRep implementation")

    print(f"{MARK}: applied")
    print("opcode=0x21_EDeleteRange")
    print("abi=arg0_partial,arg1_mask,arg2_errorKey,arg3_subsession")
    print("transaction_delete=STAGED_UNTIL_COMMIT")
    print("not_found=KErrNotFound_TRANSACTION_PRESERVED")
    print("persistence=deleted_settings_plus_single_write_on_commit")
    print("home_specific_hardcode=NONE")
    print("focus_input=UNCHANGED")
    print("tfxserver=UNCHANGED")
    print("firmware=UNCHANGED")


if __name__ == "__main__":
    main()
