# FSM-002 — corrected minimal writer

[All suites](README.md) · [Overall feasibility](../research/FEASIBILITY_STATUS.md)

## Goal

Correct the APF serial response timing and prove an exact 64-byte write plus fresh-launch readback.

## Method

Reproduce the serial timing issue, qualify a separate minimal02 build, verify its banner/package, write/read, remount, then run a read-only fresh launch and remount again.

## Corrections

Repair the serial response timing and establish generation 1 with clocked startup. One attempt resumed CARDWRITE01; it was classified as the wrong build. Core-selection metadata differences were reviewed explicitly rather than silently ignored.

## Result details

**PASS for one correct write/remount and one fresh-launch read/remount.** Exact full power-off actions were not independently confirmed.

### FSM-002 — wrong-build attempt

**Goal:** Exercise the corrected minimal02 build.

**Method:** Compare screenshots, active-core metadata, package hashes, and output fixture.

**Corrections:** Select CARDWRITE02 and verify the LAB 02 banner before retrying.

**Result details:** INCONCLUSIVE for minimal02: LAB 01 was running, while the corrected output remained the installed zero fixture.

### FSM-002-R1 — exact write

**Goal:** Persist the intended generation-1 record.

**Method:** Write/read in LAB 02; remount and compare all bytes.

**Corrections:** Review expected lastcore/recent metadata changes caused by selecting the correct core.

**Result details:** PASS: exact 64-byte record, zero core error, SHA-256 `b7b05ccadcfa2eb7ed53aee6b5b12db57a06217da1351728a82810ad757f393c`; no other protected baseline file changed.

### FSM-002-COLD — reload readback

**Goal:** Recover the same record after a fresh launch without writing.

**Method:** Press B only, capture READ MATCH, then compare remounted bytes and protected files.

**Corrections:** Retain the collector’s older-baseline metadata flags with their separate review.

**Result details:** PASS: generation 1, one completed read, same whole-file hash, no changed/missing protected file; only the new screenshot was added.

### Evidence and scope

[Minimal02 procedure](../procedures/NEXT_HARDWARE_RUN.md) and [status](../status/CURRENT_STATUS.md). The hardware power-up cause in minimal01 remains unproven; the corrected startup behavior is verified only within the recorded scope.
