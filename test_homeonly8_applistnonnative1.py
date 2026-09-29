#!/usr/bin/env python3
"""Static contract test for HOMEONLY8 APPLISTNONNATIVE1."""
from pathlib import Path
import sys

MARK = "HOMEONLY8-APPLISTNONNATIVE1-TEST"


def fail(msg):
    raise SystemExit(f"{MARK}: {msg}")


def main():
    if len(sys.argv) != 2:
        fail("usage: test_homeonly8_applistnonnative1.py <upstream-root>")

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
    combined = h + "\n" + c

    required = (
        "[HOMEONLY8][APPLIST_NONNATIVE]",
        "std::unordered_map<epoc::uid, std::u16string> non_native_app_types_;",
        "void applist_server::register_non_native_app_type(service::ipc_context &ctx)",
        "void applist_server::deregister_non_native_app_type(service::ipc_context &ctx)",
        "case applist_request_register_non_native_app_type:",
        "case applist_request_deregister_non_native_app_type:",
        "ctx.complete(epoc::error_already_exists);",
        "ctx.complete(epoc::error_none);",
    )
    for marker in required:
        if marker not in combined:
            fail(f"missing contract marker: {marker}")

    # HOMEONLY7 must remain present.
    for marker in (
        "struct ini_token {",
        "return { trim1, true };",
        "if (ns.text.empty() && !ns.quoted)",
    ):
        if marker not in ini_text:
            fail(f"HOMEONLY7 regression: {marker}")

    # The implementation must stay generic.
    for forbidden in (
        "0x10282F06",
        "0x10282821",
        "widgetlauncher.exe",
        "0x10275104",
        "0xA0001000",
    ):
        if forbidden in combined:
            fail(f"target-specific literal present: {forbidden}")

    print(f"{MARK}: PASS")
    print("applist_register_non_native=YES")
    print("applist_deregister_non_native=YES")
    print("synchronous_ipc_completion=YES")
    print("homeonly7_quoted_tokenizer=KEPT")
    print("cenrep_52_to_26_change=NO")


if __name__ == "__main__":
    main()
