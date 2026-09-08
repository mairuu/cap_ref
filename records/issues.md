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
