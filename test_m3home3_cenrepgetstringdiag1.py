#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

UPSTREAM = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else None
if UPSTREAM is not None:
    sys.argv = [sys.argv[0]]


class M3Home3CenRepGetStringDiagTest(unittest.TestCase):
    def test_live_contract(self) -> None:
        if UPSTREAM is None:
            self.skipTest("FASTBUILD upstream argument not supplied")
        repo = (UPSTREAM / "src/emu/services/src/centralrepo/repo.cpp").read_text(encoding="utf-8")
        bridge = (UPSTREAM / "src/emu/ios/src/emu_bridge.mm").read_text(encoding="utf-8")

        self.assertIn("[M3HOME1][APPARC_REQUEST]", bridge)
        self.assertIn("[M3HOME2][CEN_DELETE_RANGE]", repo)
        self.assertIn("[M3HOME3][CEN_GET_STRING] phase=pre_write", repo)
        self.assertIn("[M3HOME3][CEN_GET_STRING] phase=complete", repo)
        self.assertIn("behavior=OBSERVE_ONLY", repo)
        self.assertIn("common::min(entry->data.strd.length(), buffer_length)", repo)
        self.assertIn("complete_central_repo_ipc(ctx, epoc::error_overflow);", repo)

    def test_no_home_specific_shortcut(self) -> None:
        if UPSTREAM is None:
            self.skipTest("FASTBUILD upstream argument not supplied")
        repo = (UPSTREAM / "src/emu/services/src/centralrepo/repo.cpp").read_text(encoding="utf-8")
        start = repo.index("[M3HOME3][CEN_GET_STRING] phase=pre_write")
        window = repo[max(0, start - 6000):start + 12000]
        self.assertNotIn("0x10275104", window)
        self.assertNotIn("0x102750F0", window)

    def test_probe_records_descriptor_boundary(self) -> None:
        if UPSTREAM is None:
            self.skipTest("FASTBUILD upstream argument not supplied")
        repo = (UPSTREAM / "src/emu/services/src/centralrepo/repo.cpp").read_text(encoding="utf-8")
        for token in (
            "entry_len={}",
            "dst_max={}",
            "write_len={}",
            "len_desc_present={}",
            "len_desc_max={}",
            "len_before={}",
            "hex8=",
        ):
            self.assertIn(token, repo)


if __name__ == "__main__":
    unittest.main()
