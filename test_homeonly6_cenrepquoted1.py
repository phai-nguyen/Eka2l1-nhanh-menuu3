#!/usr/bin/env python3
"""Static contract test for HOMEONLY6 CENREPQUOTED1."""
from pathlib import Path
import sys

MARK = "HOMEONLY6-CENREPQUOTED1-TEST"


def fail(msg):
    raise SystemExit(f"{MARK}: {msg}")


def main():
    if len(sys.argv) != 2:
        fail("usage: test_homeonly6_cenrepquoted1.py <upstream-root>")

    up = Path(sys.argv[1]).resolve()
    p = up / "src/emu/common/src/ini.cpp"
    if not p.is_file():
        fail(f"missing {p}")

    text = p.read_text(encoding="utf-8")

    required = (
        "HOMEONLY6 CENREPQUOTED1: quoted tokens are literal",
        "bool quoted = false;",
        "quoted || (line[counter] != ',' && line[counter] != '\\t')",
        "if (quoted && (counter < line.length()))",
        "if (quoted) {\n                return trim1;\n            }",
        "std::size_t equal_pos = trim1.find('=');",
    )
    for marker in required:
        if marker not in text:
            fail(f"missing contract marker: {marker}")

    # The baseline bug had unconditional comma/tab termination inside quotes.
    old_loop = """while (counter < line.length() && line[counter] != cto_stop
                && line[counter] != ',' && line[counter] != '\\t')"""
    if old_loop in text:
        fail("old quote-insensitive token loop still present")

    for forbidden in (
        "0x10275104",
        "0xA0001000",
        "0x102750F0",
        "localapp:0x101F4CD2",
    ):
        if forbidden in text:
            fail(f"target-specific literal leaked into generic parser: {forbidden}")

    print(f"{MARK}: PASS")
    print("generic_quote_aware_parser=YES")
    print("cenrep_52_to_26_change=NO")


if __name__ == "__main__":
    main()
