# Issues log

Append as things break. One entry per real problem — the point is that the
second occurrence costs minutes, not hours.

**When an entry resolves, add the symptom to
`troubleshooting/symptom-index.md`** so it is findable at 2am.

---

## Template

```
## YYYY-MM-DD · <short title>

**Day / step:**
**Symptom:** what you actually observed, verbatim where possible
**Suspected:** what you thought it was first
**Actual cause:**
**Fix:**
**Time lost:**
**Prevented by:** what would have caught this earlier
```

---

## Known issues carried in from before the board died

### Firmware runaway output — *not reproduced in the rewrite, watch for it*

**Symptom:** under the **previous, ported** firmware, any single serial command
caused an endless stable flood of output afterward (e.g. `4095` repeating,
`Invalid Command` repeating) — always the value the just-processed command
legitimately printed once.

**Ruled out:** TX→RX hardware loopback; the serial-parsing code path itself
(instrumentation showed the read loop was never re-entered).

**Not ruled out:** silent reboot loop, watchdog panic loop, ISR/task interaction
from the old `attachInterrupt` encoders.

**Status:** the rewrite removed the most likely cause by construction — encoders
use the PCNT peripheral, so there are no GPIO ISRs at all. A 3-second quiet
window after `e`/`r` was clean, and `esp_reset_reason()` reported `1`
(`ESP_RST_POWERON`), so no reboot loop. **But it was never exercised under motor
load or with the PID running.**

**If it recurs:** print `esp_reset_reason()` at the top of `setup()`, and use a
crash-backtrace-capable monitor rather than a bare pyserial read loop — a real
crash prints to UART via ROM/IDF logging, bypassing Arduino's `Serial` buffering
entirely, which would explain why instrumentation never saw it coming.

### `micro_ros_agent` holding the serial port

**Symptom:** `esptool` upload fails with a generic pyserial disconnect error that
looks like a permissions problem but is not.

**Cause:** a `micro_ros_agent` running as root (systemd or docker) holding
`/dev/ttyUSB0` open.

**Fix:** `sudo fuser -v /dev/esp32` before every upload. Stop the service.

### GPIO12 strapping pin — unverified

`RIGHT_MOTOR_BACKWARD` is on GPIO12, the MTDI strapping pin, which selects flash
voltage if pulled high at reset. Never confirmed harmless in practice.

**Test:** five power cycles, not a drive test. If it glitches, move the signal to
a free non-strapping GPIO and reflash.

### Nav2 would not install from `packages.ros.org` — *unresolved, will recur*

*Found 8 Sep 2026 by reading `recoverable/mount/.bash_history`, not by
experiencing it. Recorded here so Day 4 does not rediscover it under pressure.*

**Symptom:** on the old board, `sudo apt install -y ros-humble-navigation2
ros-humble-nav2-bringup ros-humble-twist-mux` failed repeatedly — history lines
1391–1431 show it retried ~12 times over what looks like an hour, with
`apt update`, `apt-get update`, `apt list --upgradable` and dropping packages
from the command line one at a time in between. The exact apt error is **not**
in the history (only the commands survive, not their output).

**Escalation path taken, in order:**
1. Retry with/without `twist_mux`, with/without `nav2-bringup` — no.
2. Install a **ros2-snapshot** apt source (`/etc/apt/sources.list.d/ros2-snapshot.sources`,
   staged from a Claude scratchpad) — no; **removed again** along with
   `ros2-snapshot-keyring.gpg` a few lines later. It did not work; do not retry it first.
3. `sudo apt install /home/jetson/nav2_debs/*.deb` — this is the one that stuck.
   `--fix-missing` appears on its own on the next lines, so it was not clean even then.

**Actual cause:** unknown. Most likely a `packages.ros.org` arm64 dependency
skew at that date (Humble sync mid-flight), not something about this robot.

**Consequence for the rebuild:** `~/nav2_debs/` died with the board — it is not
in the NVMe dump. If apt fails again there is no cached fallback, and rebuilding
one means finding the same debs from a working mirror or a snapshot date.

**Prevented by:** installing Nav2 on **Day 1**, not Day 4. That is why
`scripts/bootstrap-ros-humble.sh` installs it in its own non-fatal step and
shouts if it fails — three days of slack instead of none.

**If it fails now:** capture the verbatim apt error into this file first. Then
try, in this order: `apt-cache policy ros-humble-navigation2`; installing
`ros-humble-nav2-*` component packages individually to find which dependency is
unsatisfiable; only then a dated snapshot mirror. Log whatever works.
