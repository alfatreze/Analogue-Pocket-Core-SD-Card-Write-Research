# B004R2 — stress and repeated cold reads

[All suites](README.md) · [Overall feasibility](../research/FEASIBILITY_STATUS.md)

## Goal

Test sustained bounded updates and repeatable fresh-launch recovery of the final region data.

## Method

Run 10,000 changing-data pairs; collect complete operation history; perform ten separate 32-read fresh launches with host whole-file checks after each session.

## Corrections

The initial 512-bit probe violated the 511-bit IP limit. R1 retained read timing one clock later than the global extrema; R2 captured the DONE-edge counter consistently. Failed/stopped builds and expanded simulation histories remain preserved.

## Result details

**PASS within the initial single-card scope:** 10,000 pairs, 320 subsequent read-only comparisons, and eleven host checks. Final SHA-256 `0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56`.

### STRESS-004-WRITE — 10,000 pairs

**Goal:** Detect missing, repeated, stale, or wrong-range operations during sustained changing-data updates.

**Method:** Retain every indexed write/read record, reconstruct timing extrema, then independently compare the entire file.

**Corrections:** Before hardware, reduce the unsupported 512-bit probe to 511 bits and align retained/read-extrema timing to the same DONE edge. No in-flight RTL correction.

**Result details:** 10,000 pairs / 20,000 commands; zero comparison failures. Writes 11.298–126.546 ms; reads 6.076–21.889 ms. Final 256 KiB file and protected content passed.

### STRESS-004-COLD-01 — fresh-launch read/remount

**Goal:** Recover all 32 final regions read-only and confirm that the read causes no stored-data changes.

**Method:** Fresh READY/zero counters; 32 retained reads; host whole-file/guard/protected comparison.

**Corrections:** None recorded; any expected new screenshot was reviewed separately.

**Result details:** PASS: 32 reads, zero writes/failures, read range 0.787–8.042 ms. Full file and all prior contents unchanged.

### STRESS-004-COLD-02 — fresh-launch read/remount

**Goal:** Recover all 32 final regions read-only and confirm that the read causes no stored-data changes.

**Method:** Fresh READY/zero counters; 32 retained reads; host whole-file/guard/protected comparison.

**Corrections:** None recorded; any expected new screenshot was reviewed separately.

**Result details:** PASS: 32 reads, zero writes/failures, read range 0.741–6.832 ms. Full file and all prior contents unchanged.

### STRESS-004-COLD-03 — fresh-launch read/remount

**Goal:** Recover all 32 final regions read-only and confirm that the read causes no stored-data changes.

**Method:** Fresh READY/zero counters; 32 retained reads; host whole-file/guard/protected comparison.

**Corrections:** None recorded; any expected new screenshot was reviewed separately.

**Result details:** PASS: 32 reads, zero writes/failures, read range 0.775–6.909 ms. Full file and all prior contents unchanged.

### STRESS-004-COLD-04 — fresh-launch read/remount

**Goal:** Recover all 32 final regions read-only and confirm that the read causes no stored-data changes.

**Method:** Fresh READY/zero counters; 32 retained reads; host whole-file/guard/protected comparison.

**Corrections:** None recorded; any expected new screenshot was reviewed separately.

**Result details:** PASS: 32 reads, zero writes/failures, read range 0.741–7.998 ms. Full file and all prior contents unchanged.

### STRESS-004-COLD-05 — fresh-launch read/remount

**Goal:** Recover all 32 final regions read-only and confirm that the read causes no stored-data changes.

**Method:** Fresh READY/zero counters; 32 retained reads; host whole-file/guard/protected comparison.

**Corrections:** None recorded; any expected new screenshot was reviewed separately.

**Result details:** PASS: 32 reads, zero writes/failures, read range 0.741–6.866 ms. Full file and all prior contents unchanged.

### STRESS-004-COLD-06 — fresh-launch read/remount

**Goal:** Recover all 32 final regions read-only and confirm that the read causes no stored-data changes.

**Method:** Fresh READY/zero counters; 32 retained reads; host whole-file/guard/protected comparison.

**Corrections:** None recorded; any expected new screenshot was reviewed separately.

**Result details:** PASS: 32 reads, zero writes/failures, read range 0.775–6.792 ms. Full file and all prior contents unchanged.

### STRESS-004-COLD-07 — fresh-launch read/remount

**Goal:** Recover all 32 final regions read-only and confirm that the read causes no stored-data changes.

**Method:** Fresh READY/zero counters; 32 retained reads; host whole-file/guard/protected comparison.

**Corrections:** None recorded; any expected new screenshot was reviewed separately.

**Result details:** PASS: 32 reads, zero writes/failures, read range 0.780–10.963 ms. Full file and all prior contents unchanged.

### STRESS-004-COLD-08 — fresh-launch read/remount

**Goal:** Recover all 32 final regions read-only and confirm that the read causes no stored-data changes.

**Method:** Fresh READY/zero counters; 32 retained reads; host whole-file/guard/protected comparison.

**Corrections:** None recorded; any expected new screenshot was reviewed separately.

**Result details:** PASS: 32 reads, zero writes/failures, read range 0.747–7.288 ms. Full file and all prior contents unchanged.

### STRESS-004-COLD-09 — fresh-launch read/remount

**Goal:** Recover all 32 final regions read-only and confirm that the read causes no stored-data changes.

**Method:** Fresh READY/zero counters; 32 retained reads; host whole-file/guard/protected comparison.

**Corrections:** None recorded; any expected new screenshot was reviewed separately.

**Result details:** PASS: 32 reads, zero writes/failures, read range 0.754–9.270 ms. Full file and all prior contents unchanged.

### STRESS-004-COLD-10 — fresh-launch read/remount

**Goal:** Recover all 32 final regions read-only and confirm that the read causes no stored-data changes.

**Method:** Fresh READY/zero counters; 32 retained reads; host whole-file/guard/protected comparison.

**Corrections:** None recorded; any expected new screenshot was reviewed separately.

**Result details:** PASS: 32 reads, zero writes/failures, read range 0.754–6.842 ms. Full file and all prior contents unchanged.

### Evidence and scope

[Procedure](../procedures/B004_HARDWARE_RUN.md), [campaign summary](../../work/evidence/b004r2-physical-campaign-summary.json), [retained original report](../status/archive/B004_CAMPAIGN_RECORD.md). Ten fresh launches are not ten independently confirmed full power cycles; only final stored generations have host durability evidence. Other media, active interruption, and Tau workloads were outside this suite.
