#!/usr/bin/env python3
from pathlib import Path
import sys

up = Path(sys.argv[1]).resolve()
root = (up / "src/emu/ios/app/RootViewController.mm").read_text(encoding="utf-8")

assert "[M3HOME1][TRIGGER]" in root
assert "[HOMEONLY3][HOME_EXIT_KEEP_MENU3]" in root
assert "self.currentGameUid == 0x102750F0u" in root
assert "self.currentGameUid = 0x101F4CD2u" in root
assert "[self.inputManager reloadBindingsForUid:0x101F4CD2u]" in root

start = root.index("- (void)onAppExited {")
end = root.index("// ---- Launch / exit", start)
body = root[start:end]

home_if = body.index("self.currentGameUid == 0x102750F0u")
home_return = body.index("return;", home_if)
exit_call = body.index("[self exitGame];")
assert home_return < exit_call, "Home guard must return before ordinary exitGame path"

# Keep ordinary game behavior intact after the Home-specific guard.
assert 'EKA2L1: guest app exited' in body
assert "[self exitGame];" in body

print("HOMEONLY3 lifecycle contract: PASS")
print("home_exit_reboot=DISABLED_ONLY_FOR_HOME")
print("ordinary_game_exit_reboot=PRESERVED")
print("menu3_restore_uid=0x101F4CD2")
