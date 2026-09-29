#!/usr/bin/env python3
"""HOMEONLY7 CENREPQUOTED1.

Backport the upstream EKA2L1 INI tokenizer fix needed by RM-356 Central
Repository text files.  The old generic tokenizer splits '=' even inside a
quoted token, turning for example

    "localapp:0x101F4CD2?iconid=270501603;7110&toolbar=1"

into the truncated value

    localapp:0x101F4CD2?iconid

before Central Repository ever sees it.

This patch changes only common::ini_linestream tokenization. It does not alter
CenRep Get/Set lengths, IPC ABI, repository keys, firmware, Home/AISCUT code,
focus/input/scheduler behavior, or panic handling.
"""

from pathlib import Path
import sys

MARK = "HOMEONLY7-CENREPQUOTED1"


def fail(msg: str) -> None:
    raise SystemExit(f"{MARK}: {msg}")


FIXED_BLOCK = r'''    struct ini_token {
        std::string text;
        bool quoted{ false };
    };

    struct ini_linestream {
        std::string line;
        int counter;

        bool ignore_spaces{ true };

        std::deque<ini_token> waits;

        explicit ini_linestream(const std::string &l)
            : line(l)
            , counter(0) {
            if ((line.length() > 0) && (line.back() == '\r')) {
                line.erase(line.length() - 1, 1);
            }
        }

        ini_token next_token() {
            if (!waits.empty()) {
                ini_token tok = std::move(waits.front());
                waits.pop_front();

                return tok;
            }

            if (ignore_spaces) {
                while (counter < line.length() && (line[counter] == ' ' || line[counter] == '\t')) {
                    counter++;
                }
            }

            if (counter >= line.length()) {
                return {};
            }

            if (line[counter] == ',') {
                counter++;
                return { ",", false };
            }

            char cto_stop = ' ';

            if (!ignore_spaces) {
                cto_stop = '\0';
            }

            bool quoted = false;

            if (line[counter] == '"') {
                quoted = true;
                cto_stop = '"';
                counter += 1;
            } else if (line[counter] == '[') {
                cto_stop = ']';
            }

            std::size_t begin = counter;

            // Quoted Central Repository values are literal.  In particular,
            // '=', comma and tab are data until the closing quote.
            while (counter < line.length() && line[counter] != cto_stop
                && (quoted || (line[counter] != ',' && line[counter] != '\t'))) {
                counter++;
            }

            std::size_t len = counter - begin + (cto_stop == ']' ? 1 : 0);

            // Consume the closing quote so the next token begins after it.
            if (quoted && (counter < line.length())) {
                counter++;
            }

            std::string trim1 = line.substr(begin, len);

            if (quoted) {
                // Never key=value-split text that was inside quotes.
                return { trim1, true };
            }

            std::size_t equal_pos = trim1.find('=');

            if ((trim1 != "=") && (equal_pos != std::string::npos)) {
                if (equal_pos != 0) {
                    waits.push_back({ "=", false });
                }

                if (trim1.length() - 1 > equal_pos) {
                    waits.push_back({ trim1.substr(equal_pos + 1, trim1.length() - equal_pos), false });
                }

                return { equal_pos != 0 ? trim1.substr(0, equal_pos) : "=", false };
            }

            return { trim1, false };
        }

        std::string next_string() {
            return next_token().text;
        }

        std::optional<std::string> peek_string() {
            if (eof()) {
                return std::nullopt;
            }

            ini_token ns = next_token();

            // Empty quoted strings are real values, not end-of-line.
            if (ns.text.empty() && !ns.quoted) {
                return std::nullopt;
            }

            waits.push_front(ns);

            return ns.text;
        }

        bool eof() {
            return (counter >= line.length()) && (waits.empty());
        }
    };

'''


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: apply_homeonly7_cenrepquoted1.py <upstream-root>")

    up = Path(sys.argv[1]).resolve()
    p = up / "src/emu/common/src/ini.cpp"
    if not p.is_file():
        fail(f"missing baseline file: {p}")

    text = p.read_text(encoding="utf-8")

    if "struct ini_token {" in text and "Quoted Central Repository values are literal" in text:
        print(f"{MARK}: already applied")
        return

    # Authority gates for the exact old tokenizer implicated by RM-356.
    for needle in (
        "struct ini_linestream {",
        "std::deque<std::string> waits;",
        "std::string next_string()",
        "std::size_t equal_pos = trim1.find('=');",
        "waits.push_back(trim1.substr(equal_pos + 1, trim1.length() - equal_pos));",
    ):
        if needle not in text:
            fail(f"old tokenizer authority missing: {needle}")

    start = text.find("    struct ini_linestream {")
    end = text.find("    int ini_file::load", start)
    if start < 0 or end < 0:
        fail("cannot bound ini_linestream region")

    old_region = text[start:end]
    if old_region.count("std::size_t equal_pos = trim1.find('=');") != 1:
        fail("unexpected equal-split count in old tokenizer")

    text = text[:start] + FIXED_BLOCK + text[end:]

    # Post-apply semantic gates.
    for needle in (
        "struct ini_token {",
        "bool quoted{ false };",
        "std::deque<ini_token> waits;",
        "if (quoted) {",
        "Never key=value-split text that was inside quotes.",
        "return { trim1, true };",
        "if (ns.text.empty() && !ns.quoted)",
    ):
        if needle not in text:
            fail(f"postcondition missing: {needle}")

    # The old bug must be gone from the replaced tokenizer.
    new_region = text[text.find("    struct ini_token {"):text.find("    int ini_file::load")]
    if "std::deque<std::string> waits;" in new_region:
        fail("old string-only token queue remains")
    if "waits.push_back(trim1.substr(equal_pos + 1" in new_region:
        fail("old untyped wait token remains")

    p.write_text(text, encoding="utf-8")

    print(f"{MARK}: applied")
    print("scope=COMMON_INI_QUOTED_TOKENIZER")
    print("rm356_cenrep_quoted_equals=PRESERVED")
    print("cenrep_get_length=UNCHANGED")
    print("cenrep_set_length=UNCHANGED")
    print("cenrep_ipc_abi=UNCHANGED")
    print("firmware=UNCHANGED")
    print("aiscutplugin=UNCHANGED")
    print("panic_suppression=NO")
    print("nativeboot=ABSENT")
    print("compatboot=ABSENT")


if __name__ == "__main__":
    main()
