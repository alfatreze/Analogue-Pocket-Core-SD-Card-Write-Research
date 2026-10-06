# B007R5 — active-write interruption study

[All suites](README.md) · [Overall feasibility](../research/FEASIBILITY_STATUS.md)

## Goal

Determine what happens to a single preallocated file when an active overwrite loses power, and whether torn data can be rejected without writing over it.

## Method

Use a dedicated 256 KiB slot-0x27 scratch file, alternating deterministic tag-0/tag-1 images, external JTAG observation, full host classification, selected read-only cold-recovery checks, and controls before/after the cut series.

## Corrections

R5’s fit redesign is in the separate [fit report](B007_FIT_RESULTS.md). The first cut’s stale monitor made timing inconclusive; subsequent cuts supplied changing active samples and link loss. Expected screenshots/caches were explicitly reviewed. Every torn image was archived before guarded scratch-only restoration.

## Result details

**Active writes can tear:** three monitored trials all left mixed images. **Read-only rejection passed** on CUT1, CUT3, and the separate accidental shutdown. No-cut and post-cut controls passed. CUT2/CUT4 establish host classification and preservation; their own separate cold-rejection tests are not claimed.

### B007R5-NOCUT1 — no-cut control

**Goal:** Establish known complete images and persistent write/read behavior before cuts.

**Method:** Cold-read all words, complete two alternating writes, stop with B, cold-read and fully shut down/remount.

**Corrections:** Review the explicitly expected screenshot and regenerated menu caches in the host audit.

**Result details:** PASS: all 65,536 words read, exact tag-0 host image SHA-256 `a77f3185b8e29297a05a4c9072162c3719019ff547c202d44920875147329658`, unrelated files unchanged.

### B007R5-POWER1 — between-command power cycle

**Goal:** Verify persistence after full Pocket power cycling with no command active.

**Method:** One completed write; B stop; JTAG idle/DONE; full shutdown/reload/cold-read; host remount.

**Corrections:** None recorded.

**Result details:** PASS: exact tag-1 image SHA-256 `00aec285fa738e1225c201774629ea5af4bd630f89f64976fbb5ad632a8f7a6a` and 65,536-word cold read; zero target error; protected files unchanged.

### B007R5-CUT1 — timing-inconclusive attempt

**Goal:** Attempt a cut during a live write and classify both timing evidence and physical data.

**Method:** User screen cue, JTAG monitor, full shutdown, host classification, then read-only cold recovery.

**Corrections:** Monitor retained stale pre-write payload and no link-loss cue. Treat active timing as unverified; require changing active samples on subsequent attempts.

**Result details:** TIMING INCONCLUSIVE; physical file mixed: 55,299 tag-0 / 10,237 tag-1 / zero unknown words. Cold read rejected it, can_write=0; a second host check found it unchanged.

### B007R5-CUT2 — monitored active cut

**Goal:** Observe an acknowledged live command before shutdown and classify the persisted image.

**Method:** Monitor operation 8 with ACK high/DONE low after seven completed commands; power off; remount and scan every word.

**Corrections:** Use independently changing active JTAG samples and retain link loss; no payload/protocol change during the live command.

**Result details:** 87 active samples. Mixed 262,144-byte image: 55,299 tag-0 / 10,237 tag-1 / zero unknown words, four transitions. SHA-256 `18d4262f6a7e3cf275830244a698f9c6580c24d4f40caa6f96d275044632b415`. Card mountable, unrelated files unchanged. No separate post-cut fail-closed readback result is claimed for this trial.

### B007R5-CUT3 — monitored active cut

**Goal:** Observe an acknowledged live command before shutdown and classify the persisted image.

**Method:** Monitor operation 8 with ACK high/DONE low after seven completed commands; power off; remount and scan every word.

**Corrections:** Use independently changing active JTAG samples and retain link loss; no payload/protocol change during the live command.

**Result details:** 91 active samples. Mixed 262,144-byte image: 27,651 tag-0 / 37,885 tag-1 / zero unknown words, four transitions. SHA-256 `25a5a295b26e2ef224c30eeb8690a13074fbedb43d15a2c496446476a2608aa4`. Card mountable, unrelated files unchanged. A separate cold-read test on this image rejected both candidates with selected_valid=0, can_write=0, last_error=4; torn bytes remained unchanged.

### B007R5-CUT4 — monitored active cut

**Goal:** Observe an acknowledged live command before shutdown and classify the persisted image.

**Method:** Monitor operation 8 with ACK high/DONE low after seven completed commands; power off; remount and scan every word.

**Corrections:** Use independently changing active JTAG samples and retain link loss; no payload/protocol change during the live command.

**Result details:** 86 active samples. Mixed 262,144-byte image: 20,483 tag-0 / 45,053 tag-1 / zero unknown words, four transitions. SHA-256 `45f08b8b84ca7f1e7045b7bbf75d7b6600e27ff86826889733ee356bbdb25fbb`. Card mountable, unrelated files unchanged. No separate post-cut fail-closed readback result is claimed for this trial.

### B007R5-UNMONITORED — accidental shutdown

**Goal:** Preserve and inspect an unexpected shutdown rather than counting it as a clean control.

**Method:** A was pressed and Pocket powered off without the planned B stop/JTAG monitor; host classify, cold-read, then host recheck.

**Corrections:** Record it separately; preserve the torn file before guarded scratch-only restoration.

**Result details:** Mixed 40,963 tag-0 / 24,573 tag-1 / zero unknown words. Read-only recovery rejected it and disabled writes; host hash unchanged after read. Not counted among the three monitored cuts.

### B007R5-POSTCUT-CLEANSTOP3 — post-cut control

**Goal:** Check ordinary write/stop/read/remount behavior after the cut series.

**Method:** Restore/cold-read tag 1, A write loop, B stop, JTAG idle, cold read and host remount.

**Corrections:** B stops after the current command; three writes completed instead of the planned two. Verify the actual final image.

**Result details:** PASS: three writes, exact tag-0 image, 65,536-word cold read, zero error, no unrelated changes.

### B007R5-POSTCUT-POWER — post-cut power cycle

**Goal:** Check whether repeated cuts affected later between-command persistence.

**Method:** B stops with no live command; full Pocket shutdown/reload; cold read and host remount.

**Corrections:** None recorded.

**Result details:** PASS: exact tag-0 image, 65,536-word read, no target error or unrelated-file change.

### Evidence and scope

[Procedure](../procedures/B007_ACTIVE_WRITE.md), [dated per-run records and hashes](../status/CURRENT_STATUS.md), [experiment](../../experiments/b007.json), [simulation summary](../../work/evidence/b007-simulation-summary.json). All cuts were manually timed on one Pocket/exFAT card/firmware setup. This is detection/refusal evidence, not atomic overwrite or active-cut qualification of the B006 A/B save format. Optional extra cut repetitions are deferred.
