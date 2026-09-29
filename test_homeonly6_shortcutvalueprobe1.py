#!/usr/bin/env python3
from pathlib import Path
import sys

up=Path(sys.argv[1]).resolve()
repo=(up/"src/emu/services/src/centralrepo/repo.cpp").read_text(encoding="utf-8")

assert "[HOMEONLY1][CEN_GET_STRING] phase=pre_write" in repo
assert "[HOMEONLY6][CEN_SHORTCUT_VALUE]" in repo
assert "0x10275104U" in repo
assert "homeonly6_hex" in repo
assert "homeonly6_text" in repo
assert "behavior=OBSERVE_ONLY" in repo

# Preserve the existing generic GetString behavior.
assert "common::min(entry->data.strd.length(), buffer_length)" in repo
assert "ctx->complete(epoc::error_overflow);" in repo

# Diagnostic must not truncate or rewrite the repository value.
block=repo[repo.index("// HOMEONLY6 SHORTCUTVALUEPROBE1"):]
for forbidden in (
    "entry->data.strd.resize(",
    "entry->data.strd =",
    "entry->data.strd.erase(",
    "write_length =",
):
    assert forbidden not in block.split("ctx->write_data_to_descriptor_argument(",1)[0]

print("HOMEONLY6 SHORTCUTVALUEPROBE1 contract: PASS")
print("semantic_change=NONE")
print("target_repo=0x10275104")
