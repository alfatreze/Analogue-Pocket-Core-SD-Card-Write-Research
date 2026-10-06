# B004R2 physical results — initial persistence baseline

## Standard test summary

**Goal:** Test sustained changing-data writes and repeatable fresh-launch readback against an independent whole-file oracle.

**Method:** Run 10,000 changing-data pairs, retain all JTAG records, run ten fresh-launch read-only sessions, and verify the complete file and protected contents after host remounts.

**Corrections:** Earlier R1/R2 development corrected a 511-bit probe-width limit and aligned read timing-history accounting to the DONE edge. The qualified R2 build and expanded simulation were used for the physical run; see [B004 hardware procedure](../procedures/B004_HARDWARE_RUN.md) and [chronological status](../status/CURRENT_STATUS.md).

**Result details:** All 10,000 write/read pairs, 320 fresh-launch reads, and eleven host whole-file checks passed. See the detailed per-session data below. This was one card/setup; exact owner-confirmed full power-off actions were not established, so no power-cycle or interruption-safety claim is made.

## Result

PASS for the tested scope: one 10,000-pair changing-data runtime session (20,000 commands), ten separate fresh-launch read-only sessions (320 reads), and all eleven subsequent host whole-file checks. No observed comparison failures or unexpected existing-file changes. Full 256 KiB final-file SHA-256: `0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56`. Guard bytes and both prior qualified output files remain unchanged.

All 10,000 warm records are preserved losslessly in `work/evidence/b004r2-physical-jtag-write-records.json.gz`. Each cold session has its own full public retained history and post-remount summary. The aggregate with evidence hashes is `work/evidence/b004r2-physical-campaign-summary.json`; original card snapshots, output files, screenshots and raw JTAG captures remain private immutable evidence.

## Fresh-launch checks

| Check | Reads | Writes | Failures | Read range (ms) | Post-remount whole file and prior contents |
|---|---:|---:|---:|---|---|
| 1 | 32 | 0 | 0 | 0.787–8.042 | PASS |
| 2 | 32 | 0 | 0 | 0.741–6.832 | PASS |
| 3 | 32 | 0 | 0 | 0.775–6.909 | PASS |
| 4 | 32 | 0 | 0 | 0.741–7.998 | PASS |
| 5 | 32 | 0 | 0 | 0.741–6.866 | PASS |
| 6 | 32 | 0 | 0 | 0.775–6.792 | PASS |
| 7 | 32 | 0 | 0 | 0.780–10.963 | PASS |
| 8 | 32 | 0 | 0 | 0.747–7.288 | PASS |
| 9 | 32 | 0 | 0 | 0.754–9.270 | PASS |
| 10 | 32 | 0 | 0 | 0.754–6.842 | PASS |

Warm write timings: 11.298–126.546 ms; warm read timings: 6.076–21.889 ms, measured at the 74.25 MHz core clock. Each cold launch starts from verified READY/zero counters. Screenshots agree with indexed retained history and the documented one-clock LCD timing convention.

## Supported conclusion and limits

The minimal serialized BRAM/FSM APF writer can persist bounded updates to the existing preallocated file on this card, and the data remains readable across the tested fresh launches/remounts. This supplies a working reference for further experiments.

Ten fresh launches do not establish the research plan's 100/1,000 confirmed power-cycle goals. Full power-off was requested, but exact actions were not separately confirmed. The ten sessions are recorded as fresh launches. One exFAT card and firmware reported 2.7 were used. Earlier overwritten generations have immediate comparison history; only the final generation in each region has host durability evidence. No statistical reliability bound is claimed for correlated operations.

Interrupted writes, atomicity, filesystem recovery, malicious/corrupt record rejection, allocation/create/resize, NV/flush alternatives, additional cards/firmware and Tau's VexRiscv/playback path remain unqualified.

## Next experiment

Develop B005 using two separate preallocated files with generations, explicit length/version and checksum validation. On launch validate both independently and choose the newest valid generation; reject malformed or out-of-bounds records. Preserve B004's exact source/package/results as the differential reference.

First simulate corrupt/truncated records, generation selection and all interrupted-transfer phases, then compile/qualify a separate numbered build. Establish clean physical alternating writes and cold recovery before controlled power interruption on the designated disposable card. Retain external/JTAG evidence, full-card sentinels and the untouched previous generation at every boundary; a write to the alternate file is not assumed atomic. Only after this recovery experiment should the same transport be introduced into the exact pinned Tau VexRiscv configuration, followed by idle/playback workload tests.
