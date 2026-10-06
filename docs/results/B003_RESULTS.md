# B003R2 — automated batch baseline

[All suites](README.md) · [Overall feasibility](../research/FEASIBILITY_STATUS.md)

## Goal

Exercise varied bounded writes, repeated/shrinking overwrites, guarded ranges, and read-only recovery using one CPU-free build.

## Method

Run 32 cases with 38 write/read pairs, retain indexed JTAG results, compare the full 256 KiB file after remount, then verify all 32 final regions from a fresh launch and remount again.

## Corrections

The initial Java JIT crash was avoided with build-scoped interpreter mode. R1 memories expanded into registers; R2 added synchronous RAM read registers. System Console’s closed-stdin invocation did not execute the script; the client then held stdin open, explicitly sourced the script, and required validated completion markers.

## Result details

**PASS for the initial batch and cold-read baseline.** The warm batch completed 76 commands; cold recovery completed 32 reads and zero writes.

### BATCH-003-WRITE — immediate comparisons

**Goal:** Check every intended range/payload and preserve shrinking-overwrite tails.

**Method:** Start only from verified READY; decode all 38 indexed write/read records.

**Corrections:** Correct console execution as described above; keep FPGA sources unchanged during the physical run.

**Result details:** 32 cases passed, 38 pairs, 76 commands, zero failures.

### BATCH-003-WRITE — host remount

**Goal:** Confirm that physical bytes and guards match the independent model.

**Method:** Compare the entire 262,144-byte file and protected-file baseline.

**Corrections:** Review expected screenshot/menu-cache additions.

**Result details:** PASS: SHA-256 `f29a1a67f46db9181f251199cb9bab73c65df2ccd0d70621303d56f70ee9ca26`; every guard/tail matched; no protected existing file changed.

### BATCH-003-COLD — read/remount

**Goal:** Verify all final regions without writing after a fresh launch.

**Method:** 32 indexed reads, then a second whole-file and protected-content comparison.

**Corrections:** None recorded in this read-only run.

**Result details:** 32 reads passed with zero writes/failures; remounted file retained the same exact hash.

### Evidence and scope

[Procedure](../procedures/B003_HARDWARE_RUN.md), [warm JTAG](../../work/evidence/b003r2-physical-jtag-write.json), [warm host](../../work/evidence/b003r2-physical-file-write.json), [cold JTAG](../../work/evidence/b003r2-physical-jtag-cold.json), [cold host](../../work/evidence/b003r2-physical-file-cold.json). Full power-off actions were not separately confirmed. One sequence does not qualify broad repeatability or interruption safety.
