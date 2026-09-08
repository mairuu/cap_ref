# Capstone robot — recovery workspace

The processing board died and took `ws/` and the `my_bot` package with it. No
git remote, no backup. This workspace is the plan to rebuild it on a new Jetson
Orin in about a week, and the running record of doing so.

**This workspace is documentation only. No code is written here** — code lives
in `capstone-ws` on the Jetson.

## Start here

| If you want to… | Read |
|---|---|
| Know where the work stands right now | **`STATE.md`** |
| Know what to do today | `checklists/day-N-*.md` |
| Understand why the plan is shaped this way | `RECOVERY.md` |
| Understand the semantic-mapping design | `camera-lidar_semantic_mapping.md` |
| Look up a fact that survived the board | `reference/` |
| Find a number we measured | `records/calibration.md` |
| Fix something that is broken right now | `troubleshooting/symptom-index.md` |

## Working with Claude Code on the Jetson

`CLAUDE.md` is loaded automatically at the start of every session. It carries
the hard constraints, the session start/end protocol, and the list of things
not to suggest. If Claude proposes Jazzy, a Docker build for YOLO, or forking
`articubot_one`, point it back at `CLAUDE.md`.

## The rule that matters most

**Push before you extend.** Every repo gets a remote and an initial commit
before a second feature goes into it. That is the whole reason this workspace
exists.

## Repos

| Repo | Contents | Status |
|---|---|---|
| `capstone-ws` | `my_bot`, `my_bot_hardware`, `semantic_objects`, `yolo_node` | to create |
| `esp-motor-firmware` | ESP32 base controller | **exists**, `b0b762b` |
| `semantic-bridge` | `semantic_bridge` + `semantic_map_ui` | to create — currently only on a USB drive |
| `capstone-docs` | this workspace | to create |
