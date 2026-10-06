# B006 — guarded records and recovery

[All suites](README.md) · [Overall feasibility](../research/FEASIBILITY_STATUS.md)

## Goal

Enforce complete received-word coverage and whole-file guards; reject damaged nonblank initialization; recover the prior valid record at tested update boundaries.

## Method

Run 707 RTL trials, then a 25-event connected campaign, host remount, a separate SD-loaded 64-save batch, and a full Pocket power cycle after one completed inactive-record prefix.

## Corrections

An initial harness replacement changed the wrong index and omitted the intended corruption; fix and rerun the harness while preserving frozen RTL. The first coordinator audit imported a tuple instead of the model module; independent R2 audit tools replayed the retained hardware sequence. Separate updater fixtures corrected old summary filenames.

## Result details

**PASS for tested guard/recovery boundaries.** 325 connected saves, 64 post-install saves, four FPGA interruption recoveries, and one confirmed between-command Pocket power-cycle recovery passed their stated checks.

### GUARDED-006-RTL — complete-read and corruption matrix

**Goal:** Reject corrupt, incomplete, conflicting, or improperly initialized records.

**Method:** 50 corrected base trials plus 657 adversarial cases: all 513 inactive-record byte-prefix boundaries, 128 seeded record-bit corruptions, and 16 additional guard corruptions.

**Corrections:** Correct the initial injection harness; retain the original failure record.

**Result details:** 707 RTL trials passed. These modeled boundaries are not physical power-cut trials.

### GUARDED-006-CONNECTED — campaign/remount

**Goal:** Validate repeated saves, guards, and recoveries against the independent host model.

**Method:** 25 events, retained histories, independent replay, and complete host remount comparison.

**Corrections:** Repair only the derived audit tooling after hardware completion; no hardware rerun to fix the audit.

**Result details:** 325 saves, four FPGA interruptions, 11 read-only sessions, 1,681 commands. Final A973/B974 valid; both 8 KiB files and all protected content passed remount.

### GUARDED-006-POSTINSTALL64 — SD-loaded persistence

**Goal:** Verify the installed B006 image saves correctly after fresh loading.

**Method:** 64 saves, followed by full Pocket shutdown and host remount.

**Corrections:** None recorded in this run.

**Result details:** 64 retained records passed; 322 commands; final A1037/B1038 matched complete host hashes with intact guards and unchanged unrelated files.

### GUARDED-006-POWERPREFIX — full power cycle

**Goal:** Select valid B while rejecting an incomplete inactive A record after power cycling.

**Method:** Write one 128-byte generation-1039 prefix into A, pause with no outstanding APF command, fully power off, restart/cold-read, then remount.

**Corrections:** None recorded in this physical trial.

**Result details:** PASS: A invalid, B valid, selected generation 1038. Exact 8 KiB A/B file hashes and guards matched; protected files unchanged. This cuts between commands after a persisted prefix, not during an active write.

### Evidence and scope

[Development](../procedures/B006_DEVELOPMENT.md), [procedure](../procedures/B006_HARDWARE_RUN.md), [connected summary](../../work/evidence/b006-connected-resumed-summary.json), [final remount](../../work/evidence/b006-final-card-verification.json), [post-install remount](../../work/evidence/b006-post-install-64-remount-summary.json), [prefix host result](../../work/evidence/b006-power-cycle-prefix-host-summary.json). The A/B format is not yet physically qualified under active-command SD power loss.
