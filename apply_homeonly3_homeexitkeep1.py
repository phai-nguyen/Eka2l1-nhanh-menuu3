#!/usr/bin/env python3
"""HOMEONLY3 HOMEEXITKEEP1.

Keep the successful Menu3 host session alive when the real Home Screen process
exits. The stock iOS frontend treats every launched guest UID as a game and
reboots the entire emulator from onAppExited(). That is correct for games but
wrong for M3HOME, where Menu3 deliberately remains alive underneath Home.

This patch changes only the host lifecycle reaction for Home UID 0x102750F0:
- do not call exitGame()/bridge::exit_game();
- keep gameRunning true so the emulator surface remains visible;
- restore currentGameUid to Menu3 UID 0x101F4CD2;
- restore Menu3 key bindings and frontend chrome;
- leave the guest/kernel untouched so the actual Home panic/exit stays visible
  in the persistent log.

All other guest UIDs keep the original reboot-on-exit behavior.
"""
from pathlib import Path
import sys

MARK = "HOMEONLY3-HOMEEXITKEEP1"

def fail(msg):
    raise SystemExit(f"{MARK}: {msg}")

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        fail(f"{label}: expected one anchor, found {n}")
    return text.replace(old, new, 1)

def main():
    if len(sys.argv) != 2:
        fail("usage: apply_homeonly3_homeexitkeep1.py <upstream-root>")
    up = Path(sys.argv[1]).resolve()
    root = up / "src/emu/ios/app/RootViewController.mm"
    if not root.is_file():
        fail(f"missing {root}")

    text = root.read_text(encoding="utf-8")
    if "[HOMEONLY3][HOME_EXIT_KEEP_MENU3]" in text:
        print(f"{MARK}: already applied")
        return
    if "[M3HOME1][TRIGGER]" not in text:
        fail("M3HOME1 baseline missing")

    old = """- (void)onAppExited {
    // The guest app ended on its own — either a clean quit or, commonly, a KERN-EXEC panic on
    // exit (the kernel kills the faulting process). Android's equivalent callback nukes the whole
    // process (Process.killProcess) so the activity relaunches from scratch; just flipping back to
    // the apps list over the SAME, still-running emulator instance leaves the dead app's guest
    // state behind (a half-torn-down window-server session / app-server registration), so it looks
    // "still running" and the next launch closes instantly. Reboot the instance in place — exactly
    // what the working "Exit Game" button does — for a guaranteed-clean slate.
    if (!self.gameRunning) {
        return;   // already being torn down (e.g. the user tapped Exit Game, which reboots itself)
    }
    NSLog(@"EKA2L1: guest app exited — rebooting the emulator instance for a clean relaunch");
    // Progress Sync: push a backup right after a game closes (no-op unless iCloud sync is on).
    [[EKASyncManager shared] saveUpOnGameClose];
    [self exitGame];
}
"""

    new = """- (void)onAppExited {
    // HOMEONLY3 HOMEEXITKEEP1:
    // Home is launched from Menu3 while Menu3 intentionally remains alive underneath.
    // Treating Home like an ordinary game would call exitGame(), tear down the whole
    // emulator, and create the observed Home -> app-list -> iOS-home failure chain.
    if (self.gameRunning && self.currentGameUid == 0x102750F0u) {
        NSLog(@"[HOMEONLY3][HOME_EXIT_KEEP_MENU3] home_uid=0x102750F0 action=keep_emulator restore_uid=0x101F4CD2");

        // Do not touch the guest/kernel here. Let the real Home process finish/panic
        // naturally so its final diagnostics remain in the persistent EKA2L1 log.
        // Menu3 was never exited, so restore only the host-side launch bookkeeping.
        self.currentGameUid = 0x101F4CD2u;
        [self.inputManager reloadBindingsForUid:0x101F4CD2u];
        self.gameRunning = YES;
        self.statusLabel.hidden = YES;
        self.appsTable.hidden = YES;
        [self updateChrome];
        [self.view setNeedsLayout];
        [self becomeFirstResponder];
        return;
    }

    // Original behavior for every non-Home guest UID.
    // The guest app ended on its own — either a clean quit or, commonly, a KERN-EXEC panic on
    // exit (the kernel kills the faulting process). Android's equivalent callback nukes the whole
    // process (Process.killProcess) so the activity relaunches from scratch; just flipping back to
    // the apps list over the SAME, still-running emulator instance leaves the dead app's guest
    // state behind (a half-torn-down window-server session / app-server registration), so it looks
    // "still running" and the next launch closes instantly. Reboot the instance in place — exactly
    // what the working "Exit Game" button does — for a guaranteed-clean slate.
    if (!self.gameRunning) {
        return;   // already being torn down (e.g. the user tapped Exit Game, which reboots itself)
    }
    NSLog(@"EKA2L1: guest app exited — rebooting the emulator instance for a clean relaunch");
    // Progress Sync: push a backup right after a game closes (no-op unless iCloud sync is on).
    [[EKASyncManager shared] saveUpOnGameClose];
    [self exitGame];
}
"""

    text = replace_once(text, old, new, "onAppExited lifecycle")
    root.write_text(text, encoding="utf-8")

    final = root.read_text(encoding="utf-8")
    for needle in (
        "[HOMEONLY3][HOME_EXIT_KEEP_MENU3]",
        "self.currentGameUid == 0x102750F0u",
        "self.currentGameUid = 0x101F4CD2u",
        "[self.inputManager reloadBindingsForUid:0x101F4CD2u]",
        "[self exitGame];",
    ):
        if needle not in final:
            fail(f"post-apply gate missing: {needle}")

    print(f"{MARK}: applied")
    print("home_exit=KEEP_EMULATOR")
    print("menu3_lifetime=PRESERVED")
    print("guest_panic=NOT_BYPASSED")
    print("nativeboot=NOT_USED")
    print("java=UNCHANGED_NOJAVA_BASELINE")

if __name__ == "__main__":
    main()
