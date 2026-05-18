#!/usr/bin/env python3
"""Sync ASCII layer diagrams in a ZMK keymap file with its bindings.

The nickcoutsos keymap-editor (https://nickcoutsos.github.io/keymap-editor/)
only edits the `bindings = < ... >;` block, leaving the human-readable ASCII
diagram comment above `display-name = ...` untouched. This script regenerates
that diagram from the bindings so the two stay in sync.

Usage:
    python sync_layer_diagrams.py <path/to/file.keymap>

Layout is hardcoded for the Silakka54 (5 rows: 12, 12, 12, 14, 8 with 4
&none phantom positions). Cells are a uniform 7 characters wide.

Non-diagram comment lines (e.g., free-form notes) are preserved.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CELL = 7  # cell width (incl. padding) for the diagram

# Map ZMK &kp <KEY> codes to short display labels.
LABELS: dict[str, str] = {
    # Modifiers
    "LEFT_ALT": "ALT", "LALT": "ALT", "RIGHT_ALT": "ALT", "RALT": "ALT",
    "LEFT_CTRL": "CTRL", "LCTRL": "CTRL", "RIGHT_CTRL": "CTRL", "RCTRL": "CTRL",
    "LEFT_SHIFT": "SHIFT", "LSHFT": "SHIFT", "RIGHT_SHIFT": "SHIFT", "RSHFT": "SHIFT",
    "LEFT_GUI": "GUI", "LGUI": "GUI", "RIGHT_GUI": "GUI", "RGUI": "GUI",
    "LEFT_WIN": "WIN", "LWIN": "WIN", "RIGHT_WIN": "WIN", "RWIN": "WIN",
    # Common
    "RET": "ENTER", "RETURN": "ENTER", "ENTER": "ENTER",
    "BSPC": "BSPC", "BACKSPACE": "BSPC",
    "DEL": "DEL", "DELETE": "DEL",
    "SPACE": "SPACE", "TAB": "TAB",
    "ESC": "ESC", "ESCAPE": "ESC",
    "CAPS": "CAPS", "CAPSLOCK": "CAPS",
    "PRINTSCREEN": "PSCRN", "PSCRN": "PSCRN",
    "INS": "INS", "INSERT": "INS",
    # Navigation
    "LEFT": "LFT", "RIGHT": "RGT", "UP": "UP", "DOWN": "DWN",
    "HOME": "HOME", "END": "END",
    "PAGE_UP": "PG_UP", "PAGE_DOWN": "PG_DN", "PG_UP": "PG_UP", "PG_DN": "PG_DN",
    # Symbols
    "GRAVE": "`", "TILDE": "~",
    "MINUS": "-", "EQUAL": "=", "PLUS": "+",
    "UNDER": "_", "UNDERSCORE": "_",
    "LEFT_BRACKET": "[", "LBKT": "[",
    "RIGHT_BRACKET": "]", "RBKT": "]",
    "LEFT_BRACE": "{", "LBRC": "{",
    "RIGHT_BRACE": "}", "RBRC": "}",
    "LEFT_PARENTHESIS": "(", "LPAR": "(",
    "RIGHT_PARENTHESIS": ")", "RPAR": ")",
    "BSLH": "\\", "BACKSLASH": "\\",
    "FSLH": "/", "SLASH": "/",
    "PIPE": "|",
    "SEMI": ";", "SEMICOLON": ";",
    "SQT": "'", "APOSTROPHE": "'",
    "DQT": '"', "DOUBLE_QUOTES": '"',
    "COMMA": ",", "DOT": ".", "PERIOD": ".",
    "EXCL": "!", "EXCLAMATION": "!",
    "AT": "@", "HASH": "#", "POUND": "#",
    "DLLR": "$", "DOLLAR": "$",
    "PRCNT": "%", "PERCENT": "%",
    "CARET": "^",
    "AMPS": "&", "AMPERSAND": "&",
    "ASTRK": "*", "ASTERISK": "*",
    "QMARK": "?", "QUESTION": "?",
    # Media
    "K_MUTE": "MUTE", "C_MUTE": "MUTE",
    "C_VOLUME_UP": "VOL+", "C_VOL_UP": "VOL+",
    "C_VOLUME_DOWN": "VOL-", "C_VOL_DN": "VOL-",
    "C_BRIGHTNESS_INC": "BRI+", "C_BRI_UP": "BRI+",
    "C_BRIGHTNESS_DEC": "BRI-", "C_BRI_DN": "BRI-",
    "C_PLAY_PAUSE": "PLAY", "C_PP": "PLAY",
    "C_NEXT": "NEXT", "C_NXT": "NEXT",
    "C_PREVIOUS": "PREV", "C_PRV": "PREV",
}
for _i in range(10):
    LABELS[f"N{_i}"] = str(_i)
    LABELS[f"NUMBER_{_i}"] = str(_i)
for _i in range(1, 25):
    LABELS[f"F{_i}"] = f"F{_i}"

# Layer index → name. Matches the convention used in this repo.
LAYER_NAMES: dict[int, str] = {0: "BASE", 1: "LOWER", 2: "RAISE"}

# Silakka54: 12 + 12 + 12 + 14 + 8 = 58 positions.
# Row 4 has 2 &none placeholders at indices 6, 7 (the inner-thumb gap).
# Row 5 has 2 &none placeholders at indices 3, 4 (same gap on thumb row).
ROW_SIZES = [12, 12, 12, 14, 8]
TOTAL = sum(ROW_SIZES)


def label(binding: str) -> str:
    """Convert a ZMK binding (e.g. `&kp LEFT_BRACKET`) to a short display label."""
    parts = binding.split()
    if not parts:
        return ""
    head, *rest = parts
    if head in ("&trans", "&none"):
        return ""
    if head == "&kp" and rest:
        return LABELS.get(rest[0], rest[0])
    if head == "&mo" and rest:
        try:
            return LAYER_NAMES.get(int(rest[0]), f"MO{rest[0]}")
        except ValueError:
            return f"MO{rest[0]}"
    if head == "&to" and rest:
        return f"TO{rest[0]}"
    if head == "&tog" and rest:
        return f"TG{rest[0]}"
    if head == "&bt":
        if rest and rest[0] == "BT_CLR":
            return "BTCLR"
        if rest and rest[0] == "BT_CLR_ALL":
            return "BTCLRA"
        if len(rest) >= 2 and rest[0] == "BT_SEL":
            return f"BT{rest[1]}"
        if len(rest) >= 2 and rest[0] == "BT_DISC":
            return f"BD{rest[1]}"
        if rest and rest[0] == "BT_NXT":
            return "BT_NX"
        if rest and rest[0] == "BT_PRV":
            return "BT_PV"
        return rest[0] if rest else "BT"
    if head == "&out" and rest:
        return {"OUT_USB": "USB", "OUT_BLE": "BLE", "OUT_TOG": "OUT_TG"}.get(rest[0], rest[0])
    if head == "&sys_reset":
        return "RESET"
    if head == "&bootloader":
        return "BOOT"
    # Fallback: strip the leading & and uppercase
    return head.lstrip("&").upper()


def split_bindings(text: str) -> list[str]:
    """Split a bindings block into individual binding strings."""
    out: list[str] = []
    cur: list[str] = []
    for tok in text.split():
        if tok.startswith("&"):
            if cur:
                out.append(" ".join(cur))
            cur = [tok]
        else:
            cur.append(tok)
    if cur:
        out.append(" ".join(cur))
    return out


def cell(s: str) -> str:
    """Center s in a CELL-wide field, truncating if too long."""
    s = s[:CELL]
    pad = CELL - len(s)
    left = pad // 2
    return " " * left + s + " " * (pad - left)


PIPE = "|"
GAP = " " * 19
NA_MID = "  n/a   " + PIPE + "  " + PIPE + "  n/a  "  # 19 chars total
INDENT = "            "
DIVIDER = "// " + "-" * 108


def render_diagram(bindings: list[str]) -> list[str]:
    """Render the diagram body lines (without `//` prefix or indentation)."""
    if len(bindings) != TOTAL:
        raise ValueError(f"Expected {TOTAL} bindings, got {len(bindings)}")
    cells = [cell(label(b)) for b in bindings]

    lines: list[str] = []
    offset = 0
    # Rows 1-3: 12 cells, no n/a markers
    for _ in range(3):
        row = cells[offset:offset + 12]
        offset += 12
        lines.append(PIPE + PIPE.join(row[:6]) + PIPE + GAP + PIPE + PIPE.join(row[6:]) + PIPE)
    # Row 4: 14 cells with n/a markers at idx 6, 7
    row4 = cells[offset:offset + 14]
    offset += 14
    lines.append(
        PIPE + PIPE.join(row4[:6]) + PIPE + NA_MID + PIPE + PIPE.join(row4[8:]) + PIPE
    )
    # Row 5: 8 cells with n/a markers at idx 3, 4 (thumb row, indented to align
    # under cell 4 of row 4: (CELL + 1) * 3 = 24 chars of leading spaces)
    row5 = cells[offset:offset + 8]
    indent = " " * ((CELL + 1) * 3)
    lines.append(
        indent + PIPE + PIPE.join(row5[:3]) + PIPE + NA_MID + PIPE + PIPE.join(row5[5:]) + PIPE
    )
    return lines


def is_diagram_line(stripped: str) -> bool:
    """True if a comment line looks like part of the auto-generated diagram."""
    if not stripped.startswith("//"):
        return False
    body = stripped[2:].lstrip()
    return body == "" or body.startswith("|") or body.startswith("-")


def update_layer(text: str, layer_name: str, bindings: list[str]) -> str:
    """Replace the diagram block above the layer's display-name with a fresh one."""
    pat = re.compile(
        rf"({layer_name}\s*\{{\s*\n)"
        r"((?:[ \t]*//[^\n]*\n)*)"   # comment lines (may be empty)
        r"((?:[ \t]*\n)*)"           # any blank lines between comments and display-name
        r"([ \t]*display-name)",
        re.MULTILINE,
    )
    m = pat.search(text)
    if not m:
        return text
    existing_comment = m.group(2)

    diagram_lines = [INDENT + DIVIDER]
    for line in render_diagram(bindings):
        diagram_lines.append(INDENT + "// " + line)

    # Preserve non-diagram comment lines (e.g., "// Note: ..." entries)
    extras = [
        line for line in existing_comment.splitlines()
        if not is_diagram_line(line.strip())
    ]

    rebuilt = "\n".join(diagram_lines) + "\n"
    if extras:
        rebuilt += "\n".join(extras) + "\n"
    rebuilt += "\n"  # blank line before display-name

    # Replace both the comment block (group 2) and the trailing blank lines (group 3)
    return text[:m.start(2)] + rebuilt + text[m.end(3):]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: sync_layer_diagrams.py <keymap-file>", file=sys.stderr)
        return 1

    path = Path(sys.argv[1])
    original = path.read_text(encoding="utf-8")
    text = original

    layer_names = re.findall(r"(\w+_layer)\s*\{", text)
    for name in layer_names:
        bindings_pat = re.compile(
            rf"{name}\s*\{{.*?bindings\s*=\s*<\s*(.+?)\s*>;",
            re.DOTALL,
        )
        bm = bindings_pat.search(text)
        if not bm:
            continue
        bindings = split_bindings(bm.group(1))
        if len(bindings) != TOTAL:
            print(
                f"Skipping {name}: expected {TOTAL} bindings, got {len(bindings)}",
                file=sys.stderr,
            )
            continue
        text = update_layer(text, name, bindings)

    if text == original:
        print("No changes needed")
        return 0

    path.write_text(text, encoding="utf-8")
    print(f"Updated diagrams in {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
