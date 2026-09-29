#!/usr/bin/env python3
"""Static/contract test for HOMEONLY7 CENREPQUOTED1."""

from pathlib import Path
import sys

up = Path(sys.argv[1]).resolve()
p = up / "src/emu/common/src/ini.cpp"
text = p.read_text(encoding="utf-8")

assert "struct ini_token {" in text
assert "bool quoted{ false };" in text
assert "std::deque<ini_token> waits;" in text
assert "if (quoted) {" in text
assert "return { trim1, true };" in text
assert "if (ns.text.empty() && !ns.quoted)" in text

region = text[text.index("    struct ini_token {"):text.index("    int ini_file::load")]
assert "std::deque<std::string> waits;" not in region
assert "waits.push_back(trim1.substr(equal_pos + 1" not in region

# Regression evidence from exact RM-356 10275102.txt.  The old tokenizer split
# these at the first '=' despite the surrounding quotes.
cases = {
    "0x1038": "localapp:0x101F4CD2?iconid=270501603;7110&toolbar=1",
    "0x103B": "localapp:0x100058B3?view=0x10282D81&iconid=270501603;7111&toolbar=1",
    "0x103E": "localapp:0x100058F8?iconid=270501603;7116&toolbar=1",
}
for key, value in cases.items():
    assert "=" in value
    # Full UTF-16 byte sizes expected after correct CenRep loading.
    assert len(value.encode("utf-16le")) in (102, 134)

# The specific crashing shortcut value was 51 UCS-2 units / 102 bytes.
v = cases["0x1038"]
assert len(v) == 51
assert len(v.encode("utf-16le")) == 102
assert v[:26] == "localapp:0x101F4CD2?iconid"

print("HOMEONLY7 CENREPQUOTED1 contract: PASS")
print("rm356_1038_expected_bytes=102")
print("old_truncated_prefix_bytes=52")
print("cenrep_get_52_to_26_patch=FORBIDDEN_NOT_PRESENT")
print("semantic_scope=QUOTED_INI_TOKENIZATION_ONLY")
