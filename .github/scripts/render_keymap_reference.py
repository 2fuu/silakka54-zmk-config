#!/usr/bin/env python3
"""Generate the printable HTML keymap reference card from a ZMK keymap.

Output is `reference/keymap-reference.html`: a single self-contained file with
the Silakka54 split rendered as physical keycaps. Each key shows its Base
binding centered, Lower in the bottom-left corner, Raise in the top-right.

Usage:
    python render_keymap_reference.py <path/to/file.keymap> [<output.html>]

Layout assumes Silakka54 (5 rows: 12, 12, 12, 14, 8 with 4 &none phantoms),
same as sync_layer_diagrams.py. Triggered by the same CI workflow so the card
stays in sync with bindings edited via the keymap-editor web tool.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

# Reuse the binding tokenizer from the sibling script — single source of truth
# for how to split a `bindings = < ... >` block into individual bindings.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_layer_diagrams import split_bindings, ROW_SIZES, TOTAL  # noqa: E402

# ZMK keycode -> HTML display label. Mixed case, Unicode glyphs where useful.
LABEL: dict[str, str] = {
    # Numbers
    "N0": "0", "N1": "1", "N2": "2", "N3": "3", "N4": "4",
    "N5": "5", "N6": "6", "N7": "7", "N8": "8", "N9": "9",
    # Modifiers
    "LCTRL": "Ctrl", "LEFT_CTRL": "Ctrl", "RCTRL": "Ctrl", "RIGHT_CTRL": "Ctrl",
    "LSHFT": "Shft", "LEFT_SHIFT": "Shft", "RSHFT": "Shft", "RIGHT_SHIFT": "Shft",
    "LEFT_ALT": "Alt", "LALT": "Alt", "RALT": "RAlt", "RIGHT_ALT": "RAlt",
    "LGUI": "Gui", "LEFT_GUI": "Gui", "RGUI": "Gui", "RIGHT_GUI": "Gui",
    "LEFT_WIN": "Win", "LWIN": "Win", "RIGHT_WIN": "Win", "RWIN": "Win",
    # Common keys
    "ESC": "Esc", "ESCAPE": "Esc",
    "TAB": "Tab",
    "RET": "Enter", "RETURN": "Enter", "ENTER": "Enter",
    "SPACE": "Space",
    "BACKSPACE": "Bksp", "BSPC": "Bksp",
    "DELETE": "Del", "DEL": "Del",
    "CAPS": "Caps", "CAPSLOCK": "Caps",
    "INS": "Ins", "INSERT": "Ins",
    "PRINTSCREEN": "PrtSc", "PSCRN": "PrtSc",
    # Punctuation
    "BACKSLASH": "\\", "BSLH": "\\",
    "SEMI": ";", "SEMICOLON": ";",
    "SQT": "'", "APOSTROPHE": "'",
    "DQT": '"', "DOUBLE_QUOTES": '"',
    "COMMA": ",", "DOT": ".", "PERIOD": ".",
    "FSLH": "/", "SLASH": "/",
    "MINUS": "−", "EQUAL": "=", "PLUS": "+",
    "UNDER": "_", "UNDERSCORE": "_",
    "LEFT_BRACKET": "[", "LBKT": "[",
    "RIGHT_BRACKET": "]", "RBKT": "]",
    "LEFT_BRACE": "{", "LBRC": "{",
    "RIGHT_BRACE": "}", "RBRC": "}",
    "LEFT_PARENTHESIS": "(", "LPAR": "(",
    "RIGHT_PARENTHESIS": ")", "RPAR": ")",
    "GRAVE": "`", "TILDE": "~", "PIPE": "|",
    # Arrows & nav (Unicode)
    "LEFT": "←", "RIGHT": "→", "UP": "↑", "DOWN": "↓",
    "HOME": "Home", "END": "End",
    "PAGE_UP": "PgUp", "PG_UP": "PgUp",
    "PAGE_DOWN": "PgDn", "PG_DN": "PgDn",
    # Media / system
    "K_MUTE": "Mute", "C_MUTE": "Mute",
    "C_VOLUME_UP": "Vol+", "C_VOL_UP": "Vol+",
    "C_VOLUME_DOWN": "Vol−", "C_VOL_DN": "Vol−",
    "C_BRIGHTNESS_INC": "Bri+", "C_BRI_UP": "Bri+",
    "C_BRIGHTNESS_DEC": "Bri−", "C_BRI_DN": "Bri−",
    "C_PLAY_PAUSE": "Play", "C_PP": "Play",
    "C_NEXT": "Next", "C_NXT": "Next",
    "C_PREVIOUS": "Prev", "C_PRV": "Prev",
}
for _i in range(1, 25):
    LABEL[f"F{_i}"] = f"F{_i}"

# Codes that should get the .mod CSS class (warm yellow background).
MODIFIERS = {
    "LCTRL", "LEFT_CTRL", "RCTRL", "RIGHT_CTRL",
    "LSHFT", "LEFT_SHIFT", "RSHFT", "RIGHT_SHIFT",
    "LEFT_ALT", "LALT", "RALT", "RIGHT_ALT",
    "LGUI", "LEFT_GUI", "RGUI", "RIGHT_GUI",
    "LEFT_WIN", "LWIN", "RIGHT_WIN", "RWIN",
}

# Layer index → display-name, populated from the keymap at runtime.
LAYER_DISPLAY_NAMES: dict[int, str] = {}


def html_label(binding: str) -> str | None:
    """Return display label for a binding, or None if it produces no visible
    annotation (i.e. &trans or &none)."""
    parts = binding.split()
    if not parts:
        return None
    head, *rest = parts
    if head in ("&trans", "&none"):
        return None
    if head == "&kp" and rest:
        code = rest[0]
        if code in LABEL:
            return LABEL[code]
        if len(code) == 1:
            return code  # single letter A-Z
        return code  # unknown code: render as-is
    if head == "&mo" and rest:
        try:
            return LAYER_DISPLAY_NAMES.get(int(rest[0]), f"L{rest[0]}")
        except ValueError:
            return f"L{rest[0]}"
    if head == "&to" and rest:
        return LAYER_DISPLAY_NAMES.get(int(rest[0]), f"To{rest[0]}") if rest[0].isdigit() else f"To{rest[0]}"
    if head == "&tog" and rest:
        return f"Tg{rest[0]}"
    if head == "&bt":
        if rest and rest[0] == "BT_CLR":
            return "BTclr"
        if rest and rest[0] == "BT_CLR_ALL":
            return "BTclrA"
        if len(rest) >= 2 and rest[0] == "BT_SEL":
            return f"BT{rest[1]}"
        if rest and rest[0] == "BT_NXT":
            return "BT→"
        if rest and rest[0] == "BT_PRV":
            return "BT←"
        return rest[0] if rest else "BT"
    if head == "&out" and rest:
        return {"OUT_USB": "USB", "OUT_BLE": "BLE", "OUT_TOG": "Out"}.get(rest[0], rest[0])
    if head == "&sys_reset":
        return "Reset"
    if head == "&bootloader":
        return "Boot"
    return head.lstrip("&")


def is_mod(binding: str) -> bool:
    parts = binding.split()
    return len(parts) >= 2 and parts[0] == "&kp" and parts[1] in MODIFIERS


def _strip_comments(text: str) -> str:
    """Remove // line and /* block */ comments. Necessary because the diagram
    comments above each layer can contain literal '{' or '}' characters when
    those keys are mapped (e.g. Raise layer's brace keys), which would
    otherwise confuse the [^{}] guard in the layer regex below."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return text


def parse_layers(text: str) -> list[tuple[str, str, list[str]]]:
    """Return [(layer_id, display_name, bindings)] in declaration order."""
    text = _strip_comments(text)
    pattern = re.compile(
        r"(\w+_layer)\s*\{[^{}]*?"
        r'display-name\s*=\s*"([^"]+)"\s*;[^{}]*?'
        r"bindings\s*=\s*<\s*(.+?)\s*>;",
        re.DOTALL,
    )
    out = []
    for m in pattern.finditer(text):
        layer_id, display_name, bindings_text = m.groups()
        bindings = split_bindings(bindings_text)
        out.append((layer_id, display_name, bindings))
    return out


def render_key(base_b: str, lower_b: str, raise_b: str, *, thumb: bool = False) -> str:
    base_label = html_label(base_b) or ""
    lower_label = html_label(lower_b)
    raise_label = html_label(raise_b)
    # Suppress annotations that would just duplicate the Base label — the
    # cheat sheet's job is to highlight what each layer CHANGES.
    if lower_label == base_label:
        lower_label = None
    if raise_label == base_label:
        raise_label = None
    classes = ["k"]
    if is_mod(base_b):
        classes.append("mod")
    if thumb:
        classes.append("thb")
    parts: list[str] = []
    if raise_label:
        parts.append(f'<div class="ra">{html.escape(raise_label, quote=False)}</div>')
    parts.append(f'<div class="base">{html.escape(base_label, quote=False)}</div>')
    if lower_label:
        parts.append(f'<div class="lo">{html.escape(lower_label, quote=False)}</div>')
    return f'<div class="{" ".join(classes)}">{"".join(parts)}</div>'


def slice_layer(bindings: list[str]) -> dict:
    """Slice a 58-binding layer into the Silakka54 physical positions.

    Returns dict with:
      main_rows[r] = (left_6, right_6)  for r in 0..3
      thumb        = (left_3, right_3)
    The 4 &none phantom positions (row 3 mid 2, thumb mid 2) are skipped.
    """
    assert len(bindings) == TOTAL, f"expected {TOTAL} bindings, got {len(bindings)}"
    return {
        "main_rows": [
            (bindings[r * 12 : r * 12 + 6], bindings[r * 12 + 6 : r * 12 + 12])
            for r in range(3)
        ] + [
            (bindings[36:42], bindings[44:50])  # row 3: skip indices 42, 43
        ],
        "thumb": (bindings[50:53], bindings[55:58]),  # skip indices 53, 54
    }


def render_body(base: dict, lower: dict, raise_: dict) -> str:
    lines: list[str] = []
    lines.append('  <div class="layer">')
    lines.append('    <div class="split">')

    for side_idx, side_name in [(0, "l"), (1, "r")]:
        lines.append('      <div class="half">')
        for r in range(4):
            lines.append('        <div class="row">')
            for col in range(6):
                lines.append("          " + render_key(
                    base["main_rows"][r][side_idx][col],
                    lower["main_rows"][r][side_idx][col],
                    raise_["main_rows"][r][side_idx][col],
                ))
            lines.append('        </div>')
        lines.append(f'        <div class="thumbs {side_name}">')
        for i in range(3):
            lines.append("          " + render_key(
                base["thumb"][side_idx][i],
                lower["thumb"][side_idx][i],
                raise_["thumb"][side_idx][i],
                thumb=True,
            ))
        lines.append('        </div>')
        lines.append('      </div>')

    lines.append('    </div>')
    lines.append('  </div>')
    return "\n".join(lines)


# CSS braces are doubled for str.format(). Substitutions: {body}, {base_name},
# {lower_name}, {raise_name}.
HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Silakka54 keymap reference</title>
<style>
  :root {{
    --keysize: 3.6rem;
    --gap: 0.22rem;
    --radius: 6px;
    --ink: #0f172a;
    --muted: #94a3b8;
    --border: #cbd5e1;
    --plain: #ffffff;
    --lo: #b45309;
    --ra: #1d4ed8;
    --mod: #fef3c7;
    --modBorder: #f59e0b;
    --thb: #fce7f3;
    --thbBorder: #f472b6;
  }}
  html, body {{ margin: 0; padding: 0; background: #f1f5f9; color: var(--ink); }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 1rem; }}
  h1 {{ font-size: 1.1rem; margin: 0 0 0.4rem; }}
  .meta {{ color: var(--muted); font-size: 0.78rem; margin-bottom: 0.6rem; }}
  .legend {{ font-size: 0.8rem; color: #334155; margin-bottom: 1rem; text-align: center; }}
  .legend b.lo {{ color: var(--lo); }}
  .legend b.ra {{ color: var(--ra); }}
  .legend kbd {{ display: inline-block; background: #f1f5f9; border: 1px solid var(--border); border-radius: 3px; padding: 1px 5px; font-size: 0.72rem; font-family: inherit; margin: 0 2px; }}
  .layer {{ background: #fff; border-radius: 8px; padding: 1rem 1.1rem 1.2rem; box-shadow: 0 1px 2px rgba(15,23,42,0.06); }}
  .split {{ display: flex; gap: 2.4rem; justify-content: center; align-items: flex-start; }}
  .half {{ display: flex; flex-direction: column; gap: var(--gap); }}
  .row {{ display: flex; gap: var(--gap); justify-content: center; }}

  .k {{
    position: relative;
    width: var(--keysize); height: var(--keysize);
    border: 1px solid var(--border); border-radius: var(--radius);
    background: var(--plain);
    overflow: hidden;
  }}
  .k .base {{
    position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 1rem; color: var(--ink);
    line-height: 1; text-align: center;
  }}
  .k .lo {{
    position: absolute; bottom: 3px; left: 4px;
    font-size: 0.62rem; font-weight: 700; color: var(--lo);
    line-height: 1;
  }}
  .k .ra {{
    position: absolute; top: 3px; right: 4px;
    font-size: 0.62rem; font-weight: 700; color: var(--ra);
    line-height: 1;
  }}
  .k.mod {{ background: var(--mod); border-color: var(--modBorder); }}
  .k.thb {{ background: var(--thb); border-color: var(--thbBorder); }}

  .thumbs {{ display: flex; gap: var(--gap); margin-top: 0.45rem; }}
  .thumbs.l {{ padding-left: calc(var(--keysize) * 2.4); }}
  .thumbs.r {{ padding-right: calc(var(--keysize) * 2.4); justify-content: flex-end; }}

  @media print {{
    @page {{ size: letter landscape; margin: 0.4in; }}
    body {{ background: #fff; padding: 0; }}
    .layer {{ box-shadow: none; border: 1px solid #e2e8f0; padding: 0.6rem; }}
    :root {{ --keysize: 3rem; }}
    .k .base {{ font-size: 0.9rem; }}
    .k .lo, .k .ra {{ font-size: 0.58rem; }}
  }}
</style>
</head>
<body>
  <h1>Silakka54 keymap reference</h1>
  <div class="meta">Auto-generated from <code>config/lily58.keymap</code> &middot; print to PDF or paper (Ctrl+P) &middot; landscape orientation</div>
  <div class="legend">
    Each key: <b>{base_name}</b> in the center &middot;
    <b class="lo">{lower_name}</b> in the bottom-left (hold <kbd>{lower_name}</kbd> left thumb) &middot;
    <b class="ra">{raise_name}</b> in the top-right (hold <kbd>{raise_name}</kbd> right thumb)
  </div>

{body}
</body>
</html>
"""


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: render_keymap_reference.py <keymap-file> [<output-html>]",
            file=sys.stderr,
        )
        return 1

    keymap_path = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = (
            keymap_path.resolve().parent.parent / "reference" / "keymap-reference.html"
        )

    text = keymap_path.read_text(encoding="utf-8")
    layers = parse_layers(text)
    if len(layers) != 3:
        print(
            f"ERROR: expected exactly 3 layers, found {len(layers)}",
            file=sys.stderr,
        )
        return 1

    for i, (_, name, _) in enumerate(layers):
        LAYER_DISPLAY_NAMES[i] = name

    for layer_id, name, bindings in layers:
        if len(bindings) != TOTAL:
            print(
                f"ERROR: layer {layer_id} ({name}) has {len(bindings)} bindings, "
                f"expected {TOTAL}",
                file=sys.stderr,
            )
            return 1

    base = slice_layer(layers[0][2])
    lower = slice_layer(layers[1][2])
    raise_ = slice_layer(layers[2][2])
    body_html = render_body(base, lower, raise_)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Force LF newlines so output is byte-identical regardless of host OS.
    # Otherwise a Windows-local generation followed by a Linux CI regeneration
    # produces a spurious "chore: sync" commit on every push.
    output_path.write_text(
        HTML_TEMPLATE.format(
            body=body_html,
            base_name=html.escape(layers[0][1]),
            lower_name=html.escape(layers[1][1]),
            raise_name=html.escape(layers[2][1]),
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
