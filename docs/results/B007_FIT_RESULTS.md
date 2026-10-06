# B007R3/R4/R5 — fit and coverage implementation

[All suites](README.md) · [Overall feasibility](../research/FEASIBILITY_STATUS.md)

## Goal

Fit complete 65,536-word receive coverage on the actual FPGA while still detecting missing words hidden by duplicate arrivals.

## Method

Freeze each revision, run simulations, then complete sequential isolated Quartus builds and inspect resources, RAM inference, timing corners, and warnings.

## Corrections

R4 fixed a stop press lost during ISSUE_WRITE arming. R3/R4 both retained the oversized variable-indexed bitmap; R5 replaced it with a synchronous 65,536×1 M10K bitmap, direct set writes, sequential clear/scan, and exact received-word count.

## Result details

**R3 FAILED; R4 FAILED; R5 PASS for fit/internal timing.** Earlier failed images were not installed.

### B007R3-FIT

**Goal:** Fit the first full-size coverage implementation.

**Method:** Complete Quartus fitter/resource review for the frozen R3 stage.

**Corrections:** Preserve the failed stage; do not substitute a shipped bitstream.

**Result details:** 46,914 / 18,480 ALMs (254%); 92,968 combinational nodes. Fitter failed.

### B007R4-FIT

**Goal:** Check the stop-edge correction and whether capacity improved.

**Method:** Compile the separate frozen R4 stage after R3 exited.

**Corrections:** Latch B through command arming; coverage architecture remained unchanged.

**Result details:** 46,936 / 18,480 ALMs (254%); 93,013 combinational nodes. Fitter failed.

### B007R5-FIT

**Goal:** Retain coverage correctness with RAM-sized resource use.

**Method:** Full compile, M10K inference inspection, all timing corners and warning review.

**Corrections:** Replace the register bitmap with the synchronous RAM/scan design; rerun full-size simulation and independent oracle.

**Result details:** PASS: 1,991 ALMs (11%), 2,287 registers, 13/308 RAM blocks, 74,043 memory bits. All 64 timing checks positive; minimum slack +0.123 ns. 161 warnings reviewed with no latch or RAM-inference warning.

### Evidence and scope

[R3 report](../../work/evidence/build-failure-powercut07r3.json), [R4 report](../../work/evidence/build-failure-powercut07r4.json), [R5 report](../../work/evidence/build-success-powercut07r5.json), [design/procedure](../procedures/B007_ACTIVE_WRITE.md). Internal timing qualification does not measure the complete Pocket board interface or prove card persistence.
