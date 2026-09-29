#!/usr/bin/env python3
"""HOMEONLY6 CENREPQUOTED1 — preserve '=' inside quoted INI/CenRep values.

The HOMEONLY5 RM-356 evidence shows the guest receives a 52-byte prefix of a
quoted Central Repository string whose first '=' occurs after 26 UTF-16 code
units. The baseline EKA2L1 INI tokenizer splits '=' even while scanning a
quoted token, and it does not consume the closing quote.

Backport only the generic quote-aware tokenization semantics. No repository,
key, UID or firmware value is hard-coded.
"""
from pathlib import Path
import sys

MARK = "HOMEONLY6-CENREPQUOTED1"
SOURCE_MARK = "HOMEONLY6 CENREPQUOTED1: quoted tokens are literal"


def fail(msg):
    raise SystemExit(f"{MARK}: {msg}")


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        fail(f"{label}: expected one anchor, found {n}")
    return text.replace(old, new, 1)


def main():
    if len(sys.argv) != 2:
        fail("usage: apply_homeonly6_cenrepquoted1.py <upstream-root>")

    up = Path(sys.argv[1]).resolve()
    p = up / "src/emu/common/src/ini.cpp"
    if not p.is_file():
        fail(f"missing {p}")

    text = p.read_text(encoding="utf-8")

    if SOURCE_MARK in text:
        print(f"{MARK}: already applied")
        return

    for authority in (
        "struct ini_linestream {",
        "std::deque<std::string> waits;",
        "std::size_t equal_pos = trim1.find('=');",
    ):
        if authority not in text:
            fail(f"baseline authority missing: {authority}")

    text = replace_once(
        text,
        """            char cto_stop = ' ';

            if (!ignore_spaces) {
                cto_stop = '\\0';
            }

            if (line[counter] == '"') {
                cto_stop = '"';
                counter += 1;
            } else if (line[counter] == '[') {
                cto_stop = ']';
            }
""",
        """            char cto_stop = ' ';

            if (!ignore_spaces) {
                cto_stop = '\\0';
            }

            // HOMEONLY6 CENREPQUOTED1: quoted tokens are literal. In
            // particular, '=', comma and tab inside quotes are payload,
            // not INI/CenRep separators.
            bool quoted = false;

            if (line[counter] == '"') {
                quoted = true;
                cto_stop = '"';
                counter += 1;
            } else if (line[counter] == '[') {
                cto_stop = ']';
            }
""",
        "quoted-state",
    )

    text = replace_once(
        text,
        """            while (counter < line.length() && line[counter] != cto_stop
                && line[counter] != ',' && line[counter] != '\\t') {
                counter++;
            }

            std::size_t len = counter - begin + (cto_stop == ']' ? 1 : 0);

            // Stage 1 of tokenizing
            std::string trim1 = line.substr(begin, len);
            std::size_t equal_pos = trim1.find('=');
""",
        """            while (counter < line.length() && line[counter] != cto_stop
                && (quoted || (line[counter] != ',' && line[counter] != '\\t'))) {
                counter++;
            }

            std::size_t len = counter - begin + (cto_stop == ']' ? 1 : 0);

            // Consume the closing quote. Without this, the next token starts
            // on the same quote and the remainder of the line is misparsed.
            if (quoted && (counter < line.length())) {
                counter++;
            }

            // Stage 1 of tokenizing
            std::string trim1 = line.substr(begin, len);

            // Do not split key=value syntax inside a quoted literal.
            if (quoted) {
                return trim1;
            }

            std::size_t equal_pos = trim1.find('=');
""",
        "quoted-token-body",
    )

    for must in (
        SOURCE_MARK,
        "bool quoted = false;",
        "quoted || (line[counter] != ',' && line[counter] != '\\t')",
        "if (quoted && (counter < line.length()))",
        "if (quoted) {\n                return trim1;\n            }",
    ):
        if must not in text:
            fail(f"postcondition missing: {must}")

    # Scope gate: the implementation must stay generic.
    for forbidden in (
        "0x10275104",
        "0xA0001000",
        "0x102750F0",
        "localapp:0x101F4CD2",
    ):
        if forbidden in text:
            fail(f"unexpected target-specific literal in ini.cpp: {forbidden}")

    p.write_text(text, encoding="utf-8")
    print(f"{MARK}: applied")
    print("scope=GENERIC_INI_QUOTED_TOKENIZER")
    print("quoted_equals=LITERAL")
    print("quoted_comma_tab=LITERAL")
    print("closing_quote=CONSUMED")
    print("cenrep_length_semantics=UNCHANGED")
    print("target_hardcode=NONE")


if __name__ == "__main__":
    main()
