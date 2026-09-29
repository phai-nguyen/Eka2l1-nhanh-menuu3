#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

UPSTREAM = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else None
if UPSTREAM is not None:
    sys.argv = [sys.argv[0]]


class M3Home2CenRepDeleteRangeTest(unittest.TestCase):
    def test_mask_match_semantics(self) -> None:
        partial = 0x5B003A06
        mask = 0xFF00FF0F
        keys = [0x5B113A16, 0x5B003A06, 0x5C003A06, 0x5B003B06]
        matched = [k for k in keys if (k & mask) == (partial & mask)]
        self.assertEqual(matched, [0x5B113A16, 0x5B003A06])

    def test_live_upstream_contract(self) -> None:
        if UPSTREAM is None:
            self.skipTest("FASTBUILD upstream argument not supplied")

        cen = (UPSTREAM / "src/emu/services/src/centralrepo/centralrepo.cpp").read_text(encoding="utf-8")
        hdr = (UPSTREAM / "src/emu/services/include/services/centralrepo/repo.h").read_text(encoding="utf-8")
        repo = (UPSTREAM / "src/emu/services/src/centralrepo/repo.cpp").read_text(encoding="utf-8")
        bridge = (UPSTREAM / "src/emu/ios/src/emu_bridge.mm").read_text(encoding="utf-8")

        self.assertIn("[M3HOME1][APPARC_REQUEST]", bridge)
        self.assertIn('cen_rep_delete_range, "M3HOME2::CenRepDeleteRange"', cen)
        self.assertIn("case cen_rep_delete_range:", cen)
        self.assertIn("delete_range(ctx);", cen)
        self.assertIn("std::unordered_set<std::uint32_t> deleted_keys;", hdr)
        self.assertIn("void delete_range(service::ipc_context *ctx);", hdr)
        self.assertIn("[M3HOME2][CEN_DELETE_RANGE]", repo)
        self.assertIn("[M3HOME2][CEN_DELETE_COMMIT]", repo)
        self.assertIn("(key & mask) != normalized", repo)
        self.assertIn("transactor.deleted_keys.insert(key);", repo)
        self.assertIn("attach_repo->deleted_settings.push_back(key);", repo)
        self.assertIn("write_changes(io, mngr);", repo)

    def test_no_home_specific_shortcut(self) -> None:
        if UPSTREAM is None:
            self.skipTest("FASTBUILD upstream argument not supplied")
        repo = (UPSTREAM / "src/emu/services/src/centralrepo/repo.cpp").read_text(encoding="utf-8")
        self.assertNotIn("0x10275104", repo)
        self.assertNotIn("0x102750F0", repo)


if __name__ == "__main__":
    unittest.main()
