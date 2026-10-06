# B005 — alternating-file recovery

[All suites](README.md) · [Overall feasibility](../research/FEASIBILITY_STATUS.md)

## Goal

Keep a valid previous record while updating the alternate preallocated file, and recover deterministically after interruptions between SD commands.

## Method

Alternate generation/CRC-validated records; run bounded clean batches, pause/control/reload scenarios, independent replay, and later read-only recovery/remount. Preserve the stopped campaign separately from the resumed trial.

## Corrections

Console clients leaked processes on SSH close; a scoped client now records its process identity and waits for completion markers before closing it. Replay fixtures were corrected to retain transport metadata. A faulty charging cable/low battery was resolved before restoring read-only Pocket access; the chain failure is retained without claiming a proven sole cause.

## Result details

**Recovery checks passed; original connected campaign stopped incomplete.** Its 647 saves/seven recoveries remain a stopped prefix. A separately completed trial added two commits and the eighth FPGA interruption recovery, reaching generation 649; these are separately identified evidence.

### RECOVERY-005-CLEAN01 — first 64 saves

**Goal:** Verify alternating records and genuine command completion.

**Method:** Collect all 64 operation histories and matching-SOF reload recovery.

**Corrections:** None recorded in this batch.

**Result details:** 64 saves, 322 commands, zero failures; A63/B64 valid. Read-only reload selected generation 64 with two reads and zero writes.

### RECOVERY-005-CONNECTED — stopped campaign

**Goal:** Repeat clean saves and recover at the four pause boundaries.

**Method:** Independent replay of 40 completed events and 39 programming journals.

**Corrections:** Console transport/replay fixes described above; original stopped checkpoint remains unchanged.

**Result details:** 647 saves total (including CLEAN01), 17 read-only sessions, seven FPGA interruptions, 3,326 commands. Immediate oracles passed; planned second point-3 trial/final repair did not run before chain failure. Campaign verdict INCOMPLETE. Per-save retained cycle totals correspond to minimum/median/maximum 31.23 / 50.98 / 251.85 ms at nominal 74.25 MHz; these exclude boot/reload/tool overhead and are not universal timing bounds.

### BOOT-INCIDENT — read-only recovery/remount

**Goal:** Check preservation after the boot/charging incident.

**Method:** Restore Pocket power, cold-read without saving, compare both full files and guards on host.

**Corrections:** Switch faulty charging cable and charge; use the scoped console client.

**Result details:** PASS: selected A647, rejected partial B648, two reads/zero commits; host bytes and protected files matched the preserved prediction. Active-write power-loss timing was not captured.

### RECOVERY-005-RESUMED — final point and repair

**Goal:** Complete the omitted recovery boundary without rewriting stopped evidence.

**Method:** Separate resumed proof, point-3 control/cut and inactive-record repair; B006 initially reads the resulting records.

**Corrections:** Create separate resume evidence and verify the stopped-file backup rather than restarting the old blanket runner.

**Result details:** Two more commits; generation 649; eight B005 FPGA interruption recoveries cumulatively; final A649/B648 both valid in the retained replay. This resumed B005 endpoint was not separately host-remounted before B006 advanced the files.

### Evidence and scope

[Procedure](../procedures/B005_HARDWARE_RUN.md), [stopped summary](../../work/evidence/b005-connected-public-summary.json), [power-return summary](../../work/evidence/b005-power-return-summary.json), [resumed proof](../../work/evidence/b005-resumed-summary.json), [retained original history](../status/archive/B005_CAMPAIGN_RECORD.md). FPGA reload between commands does not test loss of SD power during a live write. Raw local card/process captures remain private; published summaries retain outcomes/hashes.
