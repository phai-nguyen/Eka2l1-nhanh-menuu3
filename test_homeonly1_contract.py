#!/usr/bin/env python3
from pathlib import Path
import sys

up=Path(sys.argv[1]).resolve()
root=(up/"src/emu/ios/app/RootViewController.mm").read_text(encoding="utf-8")
bridge=(up/"src/emu/ios/src/emu_bridge.mm").read_text(encoding="utf-8")
cen=(up/"src/emu/services/src/centralrepo/centralrepo.cpp").read_text(encoding="utf-8")
repo=(up/"src/emu/services/src/centralrepo/repo.cpp").read_text(encoding="utf-8")
hdr=(up/"src/emu/services/include/services/centralrepo/repo.h").read_text(encoding="utf-8")

required=[
("[M3HOME1][TRIGGER]",root),
("[M3HOME1][APPARC_REQUEST]",bridge),
('HOMEONLY1::CenRepTransactionCommit',cen),
('HOMEONLY1::CenRepDeleteRange',cen),
('[HOMEONLY1][CEN_TX_START]',repo),
('[HOMEONLY1][CEN_TX_COMMIT]',repo),
('[HOMEONLY1][CEN_DELETE_RANGE]',repo),
('[HOMEONLY1][CEN_GET_STRING] phase=pre_write',repo),
('std::unordered_set<std::uint32_t> deleted_keys;',hdr),
]
for needle,text in required:
    assert needle in text, needle

# NativeBoot/CompatBoot UI and phone-start probes must not be introduced by HOMEONLY.
for banned in [
    "CompatBoot",
    "PHONEUITARGET",
    "Phone start-up failed",
    "STARTUPREPLAY",
    "DIRECTHOME",
]:
    assert banned not in root+bridge, banned

print("HOMEONLY1 contract: PASS")
print("nativeboot_frontend=ABSENT_FROM_HOMEONLY_PATCHSET")
print("compatboot_menu_probe=ABSENT_FROM_HOMEONLY_PATCHSET")
print("phoneui_probe=ABSENT_FROM_HOMEONLY_PATCHSET")
