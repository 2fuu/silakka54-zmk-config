# Silakka54 Wireless ZMK Config

ZMK firmware configuration for the Silakka54 wireless 54-key split keyboard with SuperMini nRF52840.

The Silakka54 is based on the [Lily58](https://github.com/kata0510/Lily58) layout, but with 54 keys instead of 58 (no encoder keys and reduced thumb cluster). This config uses the official Lily58 shield with the 4 missing key positions mapped to `&none`.

## Building Firmware

### Via GitHub Actions (recommended)

1. Fork this repository to your own GitHub account
2. Optionally modify `config/lily58.keymap` to your preferences
3. Push your changes to GitHub
4. Go to the **Actions** tab in your repository
5. Download the `firmware.zip` artifact from the latest build

### Building Locally

See the [ZMK documentation](https://zmk.dev/docs/development/setup) for local setup instructions.

## Flashing Firmware

### Requirements

- USB-C cable
- The firmware `.uf2` files (left and right)
- `settings_reset-nice_nano_v2-zmk.uf2` for resetting pairing (included in build)

### Steps per half

1. **Connect** the keyboard half (left or right) via USB-C to your computer

2. **Enter bootloader mode** by double-tapping the small reset button on the underside of the board (near the nice!nano/SuperMini)

3. The board will appear as a USB storage device named `NICENANO`

4. **Copy the correct `.uf2` file** to the `NICENANO` drive:
   - `lily58_left nice_view_adapter nice_view_gem-nice_nano_v2-zmk.uf2` for the **left** half
   - `lily58_right nice_view_adapter nice_view_gem-nice_nano_v2-zmk.uf2` for the **right** half

5. The board will automatically restart after copying

6. **Repeat** for the other half

## Resetting Pairing

If you have connection issues between the left and right halves:

1. **Turn off both halves**

2. **For each half** (start with right):
   - Connect via USB-C
   - Double-tap reset button (bootloader mode)
   - Copy `settings_reset-nice_nano_v2-zmk.uf2` to `NICENANO`
   - Wait for restart
   - Double-tap reset button again
   - Copy the correct firmware `.uf2`
   - Repeat for the other half

3. **Turn on both halves** and simultaneously press the reset button on both halves to pair them

4. Connect via Bluetooth to the **left** half (master)

## ZMK Studio

This firmware has ZMK Studio enabled. This allows you to modify your keymap without reflashing:

1. Open [ZMK Studio](https://zmk.studio) in Chrome/Edge
2. Connect your keyboard via USB
3. Modify your keymap - changes are saved immediately

Note: The 4 keys not present on the Silakka54 will appear in ZMK Studio but are non-functional.

## Modifying the Keymap

The keymap is located in `config/lily58.keymap`. After making changes:

1. Commit and push to GitHub
2. Wait for the GitHub Action to complete
3. Download and flash the new firmware

## Bluetooth Controls

All Bluetooth controls are on the **Lower layer** (hold the middle left thumb key).

### Profile Selection (top row, left side)
| Key | Function |
|-----|----------|
| ESC | `BT_CLR` - Clear current profile pairing |
| 1 | Select Bluetooth profile 1 |
| 2 | Select Bluetooth profile 2 |
| 3 | Select Bluetooth profile 3 |
| 4 | Select Bluetooth profile 4 |
| 5 | Select Bluetooth profile 5 |

### Output Selection (top row, right side)
| Key | Function |
|-----|----------|
| 6 | `OUT_USB` - Force USB output |
| 7 | `OUT_BLE` - Force Bluetooth output |
| ` (backtick) | `BT_CLR_ALL` - Clear ALL profile pairings |

### Pairing a New Device
1. Hold **Lower** + press **1-5** to select a profile
2. The keyboard enters pairing mode if the profile is empty
3. On your device, search for "Lily58" and connect

### Switching Between Devices
1. Hold **Lower** + press the profile number (1-5) for that device

### Troubleshooting Connection Issues
1. Hold **Lower** + **ESC** to clear the current profile
2. Remove the keyboard from your device's Bluetooth settings
3. Re-pair by selecting the profile again

## Printable Keymap Reference

A printable cheat sheet visualizing all three layers in keycap style (Base
centered, Lower in the bottom-left, Raise in the top-right) lives at
[reference/keymap-reference.html](reference/keymap-reference.html).

Open it in a browser and press **Ctrl+P → Save as PDF** to get a printable
PDF. The page is laid out for **Letter landscape**.

The HTML is auto-generated from `config/lily58.keymap` by
`.github/scripts/render_keymap_reference.py`. The `Sync keymap-derived files`
GitHub Actions workflow regenerates it on every push to `main`, so it stays
in sync even when the keymap is edited via the keymap-editor web tool.

To regenerate locally after editing the keymap:

```
python .github/scripts/render_keymap_reference.py config/lily58.keymap
```

## Files

```
silakka54-zmk-config/
├── config/
│   ├── lily58.keymap                 # Keymap configuration (54 keys, 4 as &none)
│   ├── lily58.conf                   # Firmware settings
│   └── west.yml                      # ZMK dependencies
├── reference/
│   └── keymap-reference.html         # Printable cheat sheet (auto-generated)
├── build.yaml                        # Build matrix
└── .github/
    ├── scripts/
    │   ├── sync_layer_diagrams.py    # Regenerates ASCII diagrams in keymap
    │   └── render_keymap_reference.py # Regenerates the cheat sheet HTML
    └── workflows/
        ├── build.yml                 # Firmware build
        └── sync-layer-diagrams.yml   # Auto-regenerate derived files on push
```

## Links

- [ZMK Firmware](https://zmk.dev/)
- [ZMK Studio](https://zmk.studio)
- [Lily58 Keyboard](https://github.com/kata0510/Lily58) (base layout)
