#!/usr/bin/env python3
"""Static contract checks for HYBRIDHOME1 OLDOS-SHELL1."""
from __future__ import annotations

import sys
from pathlib import Path

MARK = "HYBRIDHOME1-CONTRACT1"


def fail(msg: str) -> None:
    raise SystemExit(f"{MARK}: {msg}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: test_hybridhome1_oldosshell.py <upstream-root>")

    root = Path(sys.argv[1]).resolve()
    src = root / "src/emu/ios/app/RootViewController.mm"
    if not src.is_file():
        fail("RootViewController.mm missing")

    text = src.read_text(encoding="utf-8")

    required = (
        "[HYBRIDHOME1][TRIGGER]",
        "[HYBRIDHOME1][SHOW]",
        "[HYBRIDHOME1][RETURN_MENU3]",
        "[HYBRIDHOME1][APP_CHOOSER]",
        "[HYBRIDHOME1][LAUNCH_REAL_APP]",
        "self.currentGameUid == 0x101F4CD2u",
        "app.uid == 0x102750F0u",
        "eka2l1::ios::bridge::get_apps()",
        "[self launchAppUid:uid]",
        "self.inputManager.enabled = self.gameRunning && !hybridVisible",
        "Hybrid Home (thử nghiệm)",
    )
    for needle in required:
        if needle not in text:
            fail(f"missing contract marker: {needle}")

    show_start = text.find("- (void)showHybridHome")
    chooser_start = text.find("- (void)showHybridAppChooser")
    if show_start < 0 or chooser_start < 0 or chooser_start <= show_start:
        fail("hybrid method boundaries missing")
    show_body = text[show_start:chooser_start]
    if "launchAppUid:0x102750F0" in show_body or "launch_app(0x102750F0" in show_body:
        fail("hybrid Home must not launch the real Nokia Home process")

    # Preserve the validated Menu3/Home comparison path and baseline independently.
    if "[M3HOME1][TRIGGER]" not in text:
        fail("M3HOME1 comparison path unexpectedly removed")

    if (root / "src/emu/j2me").exists():
        fail("NOJAVA contract violated")
    # HYBRIDHOME1 must not depend on the old NativeBoot/CompatBoot frontend paths.
    # Do not reject unrelated low-level compatibility code elsewhere in the inherited
    # emulator tree: this branch is layered on a validated backend cache.
    bridge = root / "src/emu/ios/src/emu_bridge.mm"
    for path in (src, bridge):
        s = path.read_text(encoding="utf-8", errors="ignore")
        if "[NBOOT2]" in s or "[COMPATBOOT]" in s or "CompatBoot Menu Probe" in s:
            fail(f"forbidden NativeBoot/CompatBoot frontend marker in {path}")

    print(f"{MARK}: PASS")
    print("home_shell=HOST_RENDERED")
    print("menu3_guest=PRESERVED")
    print("real_home_process=NOT_REQUIRED")
    print("app_registry=REAL")
    print("app_launch=REAL")


if __name__ == "__main__":
    main()
