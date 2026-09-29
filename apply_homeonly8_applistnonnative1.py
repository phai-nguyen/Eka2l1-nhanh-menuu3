#!/usr/bin/env python3
"""HOMEONLY8 APPLISTNONNATIVE1 — implement AppArc non-native type registration.

RM-356 HOMEONLY7 device evidence shows WidgetRegistry.exe blocks before
RProcess::Rendezvous because its synchronous AppArc request opcode 0x42
(EAppListServRegisterNonNativeApplicationType) reaches EKA2L1's AppList
default case and is never completed.

Implement the generic AppArc semantics needed here:
- register application-type UID -> native launcher descriptor;
- duplicate registration returns KErrAlreadyExists;
- deregistration removes the mapping and succeeds even if absent;
- every handled IPC is completed.

No Widget/Home UID, executable name, firmware value, or input event is
hard-coded.
"""
from pathlib import Path
import sys

MARK = "HOMEONLY8-APPLISTNONNATIVE1"
SOURCE_MARK = "[HOMEONLY8][APPLIST_NONNATIVE]"


def fail(msg):
    raise SystemExit(f"{MARK}: {msg}")


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        fail(f"{label}: expected one anchor, found {n}")
    return text.replace(old, new, 1)


def main():
    if len(sys.argv) != 2:
        fail("usage: apply_homeonly8_applistnonnative1.py <upstream-root>")

    up = Path(sys.argv[1]).resolve()
    hp = up / "src/emu/services/include/services/applist/applist.h"
    cp = up / "src/emu/services/src/applist/applist.cpp"
    ini = up / "src/emu/common/src/ini.cpp"
    for p in (hp, cp, ini):
        if not p.is_file():
            fail(f"missing {p}")

    h = hp.read_text(encoding="utf-8")
    c = cp.read_text(encoding="utf-8")
    ini_text = ini.read_text(encoding="utf-8")

    if SOURCE_MARK in c:
        print(f"{MARK}: already applied")
        return

    # HOMEONLY7 authority gate: keep the quoted CenRep root fix.
    for needle in (
        "struct ini_token {",
        "return { trim1, true };",
        "if (ns.text.empty() && !ns.quoted)",
    ):
        if needle not in ini_text:
            fail(f"HOMEONLY7 authority missing: {needle}")

    # AppList baseline authority.
    for needle in (
        "std::unordered_map<epoc::uid, std::u16string> uids_app_to_executable;",
        "void get_native_executable_name_if_non_native(service::ipc_context &ctx);",
    ):
        if needle not in h:
            fail(f"applist header authority missing: {needle}")

    for needle in (
        "case applist_request_rule_based_launching:",
        'LOG_ERROR(SERVICE_APPLIST, "Unimplemented applist opcode 0x{:X}", ctx->msg->function);',
    ):
        if needle not in c:
            fail(f"applist source authority missing: {needle}")

    if "#include <unordered_map>" not in h:
        h = replace_once(
            h,
            "#include <mutex>\n#include <vector>",
            "#include <mutex>\n#include <unordered_map>\n#include <vector>",
            "unordered-map-include",
        )

    h = replace_once(
        h,
        "        std::unordered_map<epoc::uid, std::u16string> uids_app_to_executable;\n",
        """        std::unordered_map<epoc::uid, std::u16string> uids_app_to_executable;
        // AppArc non-native application type -> native launcher mapping.
        // Symbian AppList keeps this registry so clients such as WidgetRegistry
        // can register their launcher before exposing their own server.
        std::unordered_map<epoc::uid, std::u16string> non_native_app_types_;
""",
        "mapping-field",
    )

    h = replace_once(
        h,
        "        void get_native_executable_name_if_non_native(service::ipc_context &ctx);\n",
        """        void get_native_executable_name_if_non_native(service::ipc_context &ctx);
        void register_non_native_app_type(service::ipc_context &ctx);
        void deregister_non_native_app_type(service::ipc_context &ctx);
""",
        "method-declarations",
    )

    method_anchor = "    void applist_server::get_native_executable_name_if_non_native(service::ipc_context &ctx) {"
    mi = c.find(method_anchor)
    if mi < 0:
        fail("cannot locate get_native_executable_name_if_non_native")

    injected = r'''    void applist_server::register_non_native_app_type(service::ipc_context &ctx) {
        const std::optional<epoc::uid> application_type =
            ctx.get_argument_value<epoc::uid>(0);
        const std::optional<std::u16string> native_executable =
            ctx.get_argument_value<std::u16string>(1);

        if (!application_type.has_value() || !native_executable.has_value()) {
            LOG_WARN(SERVICE_APPLIST,
                "[HOMEONLY8][APPLIST_NONNATIVE] op=register result=bad_argument");
            ctx.complete(epoc::error_argument);
            return;
        }

        const auto inserted = non_native_app_types_.emplace(
            application_type.value(), native_executable.value());

        LOG_WARN(SERVICE_APPLIST,
            "[HOMEONLY8][APPLIST_NONNATIVE] op=register type_uid=0x{:08X} exe={} inserted={}",
            application_type.value(),
            common::ucs2_to_utf8(native_executable.value()),
            inserted.second ? 1 : 0);

        if (!inserted.second) {
            ctx.complete(epoc::error_already_exists);
            return;
        }

        ctx.complete(epoc::error_none);
    }

    void applist_server::deregister_non_native_app_type(service::ipc_context &ctx) {
        const std::optional<epoc::uid> application_type =
            ctx.get_argument_value<epoc::uid>(0);

        if (!application_type.has_value()) {
            LOG_WARN(SERVICE_APPLIST,
                "[HOMEONLY8][APPLIST_NONNATIVE] op=deregister result=bad_argument");
            ctx.complete(epoc::error_argument);
            return;
        }

        const std::size_t erased =
            non_native_app_types_.erase(application_type.value());

        LOG_WARN(SERVICE_APPLIST,
            "[HOMEONLY8][APPLIST_NONNATIVE] op=deregister type_uid=0x{:08X} erased={}",
            application_type.value(), erased);

        // Symbian's DeregisterNonNativeApplicationTypeL is a no-op when the
        // type is absent, so KErrNone is the compatible result here.
        ctx.complete(epoc::error_none);
    }

'''
    c = c[:mi] + injected + c[mi:]

    switch_anchor = """            case applist_request_rule_based_launching:
                server<applist_server>()->is_accepted_to_run(*ctx);
                break;
"""
    switch_new = switch_anchor + """
            case applist_request_register_non_native_app_type:
                server<applist_server>()->register_non_native_app_type(*ctx);
                break;

            case applist_request_deregister_non_native_app_type:
                server<applist_server>()->deregister_non_native_app_type(*ctx);
                break;
"""
    c = replace_once(c, switch_anchor, switch_new, "modern-applist-switch")

    # Scope gates.
    combined = h + "\n" + c
    for required in (
        SOURCE_MARK,
        "non_native_app_types_",
        "applist_request_register_non_native_app_type",
        "applist_request_deregister_non_native_app_type",
        "ctx.complete(epoc::error_already_exists);",
        "ctx.complete(epoc::error_none);",
    ):
        if required not in combined:
            fail(f"postcondition missing: {required}")

    for forbidden in (
        "0x10282F06",  # WidgetRegistry server
        "0x10282821",  # widget launcher type
        "widgetlauncher.exe",
        "0x10275104",
        "0xA0001000",
    ):
        if forbidden in combined:
            fail(f"target-specific literal leaked into generic AppList fix: {forbidden}")

    hp.write_text(h, encoding="utf-8")
    cp.write_text(c, encoding="utf-8")

    print(f"{MARK}: applied")
    print("scope=GENERIC_APPLIST_NON_NATIVE_TYPE_REGISTRY")
    print("opcode_0x42=HANDLED_AND_COMPLETED")
    print("opcode_0x43=HANDLED_AND_COMPLETED")
    print("duplicate_register=KErrAlreadyExists")
    print("deregister_missing=KErrNone")
    print("home_widget_hardcode=NONE")
    print("input_pipeline=UNCHANGED")
    print("cenrep_abi=UNCHANGED")


if __name__ == "__main__":
    main()
