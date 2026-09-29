#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATCHER = HERE / "apply_m3home1_homebridge.py"

ROOT_FIXTURE = r'''- (void)launchAppUid:(std::uint32_t)uid {
    self.currentGameUid = uid;
    eka2l1::ios::bridge::launch_app(uid);
}

- (void)onMenuController {
    GameMenuView *menu = [[GameMenuView alloc] initWithTitle:EKAL(@"Game Menu")];
    [menu addOption:EKAL(@"Switch Key Layout") destructive:NO handler:^{ [self showLayoutChooserController]; }];
    [menu addOption:EKAL(@"Exit Game") destructive:YES handler:^{ [self exitGame]; }];
    [menu addOption:EKAL(@"Cancel") destructive:NO handler:nil];
    [self presentGameMenu:menu];
}
'''

BRIDGE_FIXTURE = r'''    void launch_app(std::uint32_t uid) {
        std::lock_guard<std::mutex> guard(g_mutex);
        if (g_state && g_state->launcher_) {
            g_state->launcher_->launch_app(uid);
        }
    }
'''


class M3Home1HomeBridgeTest(unittest.TestCase):
    def make_tree(self, root: Path) -> tuple[Path, Path]:
        rv = root / "src/emu/ios/app/RootViewController.mm"
        br = root / "src/emu/ios/src/emu_bridge.mm"
        rv.parent.mkdir(parents=True)
        br.parent.mkdir(parents=True)
        rv.write_text(ROOT_FIXTURE, encoding="utf-8")
        br.write_text(BRIDGE_FIXTURE, encoding="utf-8")
        return rv, br

    def run_patcher(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(PATCHER), str(root)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_menu_uid_gets_home_action_and_existing_launcher_route(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rv, br = self.make_tree(root)
            run = self.run_patcher(root)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

            root_text = rv.read_text(encoding="utf-8")
            bridge_text = br.read_text(encoding="utf-8")
            self.assertIn("self.currentGameUid == 0x101F4CD2u", root_text)
            self.assertIn("[self launchAppUid:0x102750F0u]", root_text)
            self.assertIn("Vào màn hình chính", root_text)
            self.assertIn("[M3HOME1][TRIGGER]", root_text)
            self.assertIn("g_state->launcher_->launch_app(uid);", bridge_text)
            self.assertIn("[M3HOME1][APPARC_REQUEST]", bridge_text)
            self.assertIn("[M3HOME1][APPARC_DISPATCHED]", bridge_text)
            self.assertIn("[M3HOME1][GUARD_REJECT]", bridge_text)

    def test_scope_does_not_add_nativeboot_shortcuts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rv, br = self.make_tree(root)
            run = self.run_patcher(root)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            changed = rv.read_text(encoding="utf-8") + br.read_text(encoding="utf-8")
            self.assertNotIn("ailaunch.exe", changed)
            self.assertNotIn("TfxServer", changed)
            self.assertNotIn("Phone start-up failed", changed)
            self.assertNotIn("start_native_phone()", changed)

    def test_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_tree(root)
            first = self.run_patcher(root)
            second = self.run_patcher(root)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)


if __name__ == "__main__":
    unittest.main()
