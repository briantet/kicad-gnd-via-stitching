# GND Via Stitching Plugin — README

Oct 10, 2026 · @Brian

## GND Via Stitching — KiCad Action Plugin

License: MIT | Compatible with KiCad 10.0

A KiCad PCB Editor action plugin that automatically places GND via stitches in a clean left-to-right, top-to-bottom grid across your board — while intelligently avoiding all footprints, tracks, pads, and existing vias.

Built and tested on KiCad 10.0 (Windows). Developed by Teters Technology LLC for the N8MP Power Management Board.

## What it looks like

After running the plugin on a populated PCB, via stitches appear in a clean uniform grid across all open copper areas, avoiding every component, trace, and pad automatically. A preview mode shows dot markers before any vias are committed so you can verify placement first.

## Features

- Places GND vias in a configurable grid, left-to-right and top-to-bottom
- Avoids all footprint bounding boxes, track segments, pads, and existing vias with adjustable clearance
- Preview mode — shows via positions as temporary markers on a scratch layer before committing, so you can adjust settings without placing anything
- Configurable grid spacing, via drill size, via pad size, clearance distance, and target net
- Layer selection: through vias (F.Cu to B.Cu), F.Cu stub, or B.Cu stub
- Board outline clipping — stays inside the edge cuts boundary
- Net dropdown populated directly from your board's actual net list
- Works on the full board outline or a selected copper zone

## Installation

**Manual install (all platforms)**

1. Download or clone this repository
2. Find your KiCad 3rdparty plugins folder. Open KiCad, go to **Preferences → Configure Paths** and look for `KICAD10_3RD_PARTY` (or the equivalent for your version). Common locations:

| OS | Default path |
| --- | --- |
| Windows | `C:\Users\<you>\Documents\KiCad\10.0\3rdparty\plugins\` |
| macOS | `~/Documents/KiCad/10.0/3rdparty/plugins/` |
| Linux | `~/.local/share/kicad/10.0/3rdparty/plugins/` |

3. Create a folder named `com_gnd_via_stitching` inside the `plugins` folder
4. Copy these three files into it:
   - `via_stitching_plugin.py`
   - `__init__.py`
   - `metadata.json`
5. Open the KiCad PCB Editor
6. Go to **Tools → External Plugins → Refresh Plugins**
7. The plugin appears as **GND Via Stitching** in the External Plugins menu

> **KiCad 10 note:** The plugin folder name must start with `com_` and the `identifier` field in `metadata.json` must match the folder name exactly. KiCad 10 only scans folders that follow this naming convention.

**Via KiCad Plugin and Content Manager (PCM)**

Search for `GND Via Stitching` in the PCM once the plugin has been accepted into the official repository.

## Usage

1. Open your `.kicad_pcb` file in the PCB Editor
2. Go to **Tools → External Plugins → GND Via Stitching**
3. The settings dialog opens — configure your grid and via parameters (see Settings below)
4. Click **Preview** to see where vias will be placed as cyan dot markers — no vias are committed yet
5. Adjust settings if needed and preview again
6. Click **Place Vias** to commit all vias to the board
7. Click **Cancel** at any time to discard the preview and make no changes
8. After placement, run **Inspect → Design Rules Checker** to verify no clearance violations

**Tip:** If you have existing GND vias that were placed manually and want to start fresh, you can remove them all from the KiCad Scripting Console (Tools → Scripting Console) with:

```python
import pcbnew
board = pcbnew.GetBoard()
net = board.FindNet('GND')
vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetCode() == net.GetNetCode()]
for v in vias: board.Delete(v)
pcbnew.Refresh()
board.Save(board.GetFileName())
```

## Settings

| Setting | Default | Description |
| --- | --- | --- |
| Grid spacing (mm) | 2.5 | Distance between via centers in X and Y |
| Via drill diameter (mm) | 0.4 | Drill hole size |
| Via pad diameter (mm) | 0.8 | Copper annular ring outer diameter |
| Clearance from objects (mm) | 0.35 | Minimum distance from any footprint, track, or pad edge |
| Net | GND | The net to assign placed vias to — dropdown shows all board nets |
| Via layer | Through (F.Cu ↔ B.Cu) | Through, F.Cu stub only, or B.Cu stub only |
| Restrict to zone | Full board outline | Optionally limit placement to a specific copper zone boundary |
| Stay inside board edge outline | On | Clips via placement to the Edge.Cuts boundary |
| Respect courtyard layers | On | Uses footprint courtyard for stricter clearance checking |

**Recommended starting values for most boards:**

- Grid: 2.0–3.0 mm
- Drill: 0.3–0.4 mm
- Pad: 0.6–0.8 mm
- Clearance: 0.3–0.5 mm

## Compatibility

| KiCad version | Status | Notes |
| --- | --- | --- |
| 10.0 | Tested and working | Primary target — all API calls verified |
| 7.0 / 8.0 | Should work with minor changes | `pcbnew.VIATYPE_THROUGH`, `board.GetNets()`, and `pcbnew.COMMIT()` exist in these versions but were removed in 10 |
| 6.0 | Not tested |  |

**KiCad 10 specific changes from earlier versions:**

- `board.GetNets()` → `board.GetNetInfo().NetsByName()`
- `pcbnew.VIATYPE_THROUGH` was removed — through via is now the default, so `SetViaType()` is not needed
- `pcbnew.COMMIT()` undo transaction API was removed — vias are placed directly with `board.Add()`
- `pcbnew.Eco1_User` → `pcbnew.User_1`
- Plugin folder must be named with a `com_` prefix inside the `plugins` directory
- `wxString` objects from `NetsByName().keys()` must be cast to `str()` before sorting

## Contributing

Bug reports and pull requests are welcome. If you run into a KiCad API issue on a version not listed above, please open an issue with:

- Your KiCad version
- Your OS
- The full error traceback from the PCB Editor exception dialog

This plugin was originally developed for the N8MP Power Management Board by Teters Technology LLC and open-sourced to help others dealing with the same KiCad 10 API changes.

## License

MIT License — see LICENSE file for details.

Copyright 2026 Teters Technology LLC — [teters.ai](https://teters.ai)
