#!/usr/bin/env python3
"""Apply M3HOME1: launch the real Symbian Home Screen from a running Menu3 session.

The device evidence for this experiment is the stable normal/HLE frontend path:
Menu UID 0x101F4CD2 is already running, AppList has registered Home Screen UID
0x102750F0, and iOS already exposes launchAppUid -> bridge::launch_app -> launcher.
M3HOME1 therefore adds only a guarded frontend action and target-specific logging.
"""
from __future__ import annotations

import sys
from pathlib import Path

MARK = "M3HOME1-HOMEBRIDGE1"
MENU_UID = "0x101F4CD2u"
HOME_UID = "0x102750F0u"


def fail(msg: str) -> None:
    raise SystemExit(f"{MARK}: {msg}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def patch_root_view(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "[M3HOME1][TRIGGER]" in text:
        return

    if "- (void)launchAppUid:(std::uint32_t)uid" not in text:
        fail("RootViewController launchAppUid baseline missing")

    anchor = """    GameMenuView *menu = [[GameMenuView alloc] initWithTitle:EKAL(@"Game Menu")];
    [menu addOption:EKAL(@"Switch Key Layout") destructive:NO handler:^{ [self showLayoutChooserController]; }];
    [menu addOption:EKAL(@"Exit Game") destructive:YES handler:^{ [self exitGame]; }];
    [menu addOption:EKAL(@"Cancel") destructive:NO handler:nil];
    [self presentGameMenu:menu];
"""
    replacement = """    GameMenuView *menu = [[GameMenuView alloc] initWithTitle:EKAL(@"Game Menu")];
    [menu addOption:EKAL(@"Switch Key Layout") destructive:NO handler:^{ [self showLayoutChooserController]; }];

    // M3HOME1 HOMEBRIDGE1: the successful device path is normal/HLE EKA2L1 with
    // Menu3 (UID 0x101F4CD2) already running. Reuse the exact same frontend
    // launcher used by the app library to start the registered Home Screen UID.
    // Keep Menu3 alive underneath: do not exit/reboot the emulator first.
    if (self.currentGameUid == 0x101F4CD2u) {
        [menu addOption:@"Vào màn hình chính" destructive:NO handler:^{
            NSLog(@"[M3HOME1][TRIGGER] source_uid=0x101F4CD2 target_uid=0x102750F0");
            // Let GameMenuView finish its selection/dismiss choreography first.
            dispatch_async(dispatch_get_main_queue(), ^{
                [self launchAppUid:0x102750F0u];
            });
        }];
    }

    [menu addOption:EKAL(@"Exit Game") destructive:YES handler:^{ [self exitGame]; }];
    [menu addOption:EKAL(@"Cancel") destructive:NO handler:nil];
    [self presentGameMenu:menu];
"""
    text = replace_once(text, anchor, replacement, "Menu3 Home action")
    path.write_text(text, encoding="utf-8")


def patch_bridge(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "[M3HOME1][APPARC_REQUEST]" in text:
        return

    anchor = """    void launch_app(std::uint32_t uid) {
        std::lock_guard<std::mutex> guard(g_mutex);
        if (g_state && g_state->launcher_) {
            g_state->launcher_->launch_app(uid);
        }
    }
"""
    replacement = """    void launch_app(std::uint32_t uid) {
        std::lock_guard<std::mutex> guard(g_mutex);
        const bool m3home_target = (uid == 0x102750F0u);
        if (m3home_target) {
            LOG_WARN(FRONTEND_CMDLINE,
                "[M3HOME1][APPARC_REQUEST] uid=0x102750F0 route=existing_ios_launcher keep_menu3_alive=1");
        }
        if (g_state && g_state->launcher_) {
            g_state->launcher_->launch_app(uid);
            if (m3home_target) {
                LOG_WARN(FRONTEND_CMDLINE,
                    "[M3HOME1][APPARC_DISPATCHED] uid=0x102750F0 route=existing_ios_launcher");
            }
        } else if (m3home_target) {
            LOG_ERROR(FRONTEND_CMDLINE,
                "[M3HOME1][GUARD_REJECT] reason=no_active_launcher uid=0x102750F0");
        }
    }
"""
    text = replace_once(text, anchor, replacement, "bridge launch_app instrumentation")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: apply_m3home1_homebridge.py <upstream-root>")

    upstream = Path(sys.argv[1]).resolve()
    root = upstream / "src/emu/ios/app/RootViewController.mm"
    bridge = upstream / "src/emu/ios/src/emu_bridge.mm"
    if not root.is_file() or not bridge.is_file():
        fail("required iOS frontend source missing")

    patch_root_view(root)
    patch_bridge(bridge)

    root_text = root.read_text(encoding="utf-8")
    bridge_text = bridge.read_text(encoding="utf-8")
    for needle in (
        "[M3HOME1][TRIGGER]",
        "0x101F4CD2u",
        "0x102750F0u",
        "Vào màn hình chính",
    ):
        if needle not in root_text:
            fail(f"RootViewController post-apply gate missing: {needle}")
    for needle in (
        "[M3HOME1][APPARC_REQUEST]",
        "[M3HOME1][APPARC_DISPATCHED]",
        "[M3HOME1][GUARD_REJECT]",
    ):
        if needle not in bridge_text:
            fail(f"emu_bridge post-apply gate missing: {needle}")

    print(f"{MARK}: applied")
    print("source_uid=0x101F4CD2")
    print("target_uid=0x102750F0")
    print("route=EXISTING_IOS_LAUNCHER")
    print("menu3_lifetime=PRESERVED")
    print("phoneui=UNCHANGED")
    print("ailaunch=NOT_USED")
    print("tfxserver=NOT_SHIMMED")
    print("firmware=UNCHANGED")


if __name__ == "__main__":
    main()
