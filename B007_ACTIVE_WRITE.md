# B007 active SD-write interruption study

## Purpose and evidence boundary

B006 established recovery after a full Pocket shutdown between completed SD
commands. It did not remove card power during a live command. B007 is a separate
CPU-free experiment to observe what the Pocket's APF `[0184]` data-slot write
does when power is interrupted during transfer. It cannot by itself reproduce
an SD card's internal flash-program/erase timing, so it measures the Pocket,
filesystem and card together and records the limits of manual cut timing.

Keep the existing `alfatreze.CARDWRITE02` core entry. Give this image a B007
metadata version and screen banner. B006, both B005 files, `stress-b004.bin`, and
their archives remain immutable. Use a new slot and a new, initially known
scratch file; never target Tau Alpha or a non-disposable card.

## Proposed test data path

- Add one optional, core-specific deferred slot, provisionally ID `0x27`, with
  a unique filename `powercut-b007.bin`. The file starts as a deterministic,
  fixed-size baseline whose size/hash are recorded before installation.
- Start with a bounded single command to a 256 KiB slot. That size matches the
  existing B004 file envelope and the official target-command maximum guidance;
  validate this exact deferred-slot and bridge-buffer behavior before hardware
  use. If the bridge cannot serve this source without gaps, stop and reduce the
  chunk size or build an explicitly windowed writer. Never silently assume the
  host API's file-size limit is the FPGA's payload-buffer capacity.
- Generate byte-distinguishable payload words from the requested byte address
  and an operation counter. Include a header/version and whole-file checksum
  oracle on the host. Avoid a huge on-chip payload RAM. Verify byte order,
  first/last words, unaligned-tail rules (if supported), and address wrap in
  simulation before selecting the transfer length.
- After each acknowledged write, optionally issue the next write immediately
  and alternate two regions within the *new scratch file* only if the APF slot
  semantics and initial file size are proven. Do not touch either B005/B006
  recovery slot. A repeated same-offset overwrite is the simpler first mode.

### Read-completeness implementation update (B007R5)

R3 and R4 used a 65,536-bit variable-indexed register vector for received-word
coverage. Quartus expanded it into 92,968/93,013 combinational nodes and the
Cyclone V fitter failed at 254% ALM utilization. R5 replaces the vector with a
single-bit, synchronous M10K-inferred bitmap. Incoming writes set the bit at
their word address directly; a sequential scan reads one bit per word after
APF DONE. Cold-read acceptance still requires exactly `WORDS` received writes,
every scanned bit set, and a matching whole-image candidate. Thus a duplicate
that masks a missing address remains rejected without a live read-modify-write
path. Quartus confirmed the bitmap as a 65,536x1 M10K and B007R5 passed full
fit and internal timing review. R5 is installed; both the no-cut and
between-command power-cycle physical controls passed cold-read and host-remount
verification. See `CURRENT_STATUS.md`,
`work/evidence/runs/B007R5-NOCUT1-REVIEW1/`, and
`work/evidence/runs/B007R5-POWER1-001/` for exact results. Manual active-write
interruption trials are underway and remain limited to the disposable B007
scratch file on this card.

## Observable interruption protocol

The screen must distinguish `READY`, `ARMING WRITE`, `WRITE ACTIVE`, `ACKNOWLEDGED`, `READBACK`,
`PASS`, command error and timeout. During the active transfer it should expose a
stable “POWER OFF NOW” cue only after target ACK with DONE still low; an arming
state is not counted as active. B latches a request to stop after the current
command, including during arming. A JTAG SDW7 snapshot stream
should be captured to the host continuously and include operation number,
state, target request, ack/done/error, elapsed clocks and bridge byte address.
JTAG is an observer; it must not pause, reset, or change the payload while the
target command is live. Confirm that the capture client does not contend with
the command path or lose the final samples when the Pocket powers off.

If a hard power switch cannot be controlled and timed repeatably with available
equipment, record the trial as a manually timed interruption, not a precisely
timed cut. A run where the command completed before the cut is a between-command
control, not an active-write trial.

## Recovery and host oracle

After every cut, first cold-start into B007's read-only inspection mode. It must
not auto-write, initialize, repair or retry. Read the entire scratch file and
classify it as exact baseline, exact complete operation image, mixed/torn,
short/long, unreadable, or command failure. Persist raw JTAG capture and screen
image before quitting. Then power the Pocket fully off, mount CARDWRITE, and
independently hash/compare the scratch file against the baseline and every
possible deterministic operation image. Confirm B005/B006 saves and all
protected files are byte-identical. Archive the complete before/after file
inventory and hashes before another attempt.

Do not infer filesystem consistency from an RTL model, APF `done`, a successful
core read, or the Pocket rebooting. Host remount is required for each physical
trial. If the filesystem fails to mount, stop writes and preserve the card for
read-only imaging/diagnosis.

## Ordered trials and controls

1. Offline checks: exact slot-ID/size acceptance, zero-length refusal,
   max+1 refusal, pattern/endian and boundary addresses, source-address hold,
   data stability during stalls, target errors, delayed completion, timeout,
   no retry, cold readback and byte-for-byte host oracle.
2. No-cut control: complete one operation, cold read, full shutdown/remount,
   verify exact file and protected content.
3. Between-command power-cycle control: cut only after `done`, then recover and
   verify. This validates the observer and read-only restart path.
4. Manual active-write attempts at early, middle and late transfer progress,
   followed by a larger repeat series around any observed transition windows.
   Keep each cut's screen, JTAG log, precise available timing, remount hashes,
   and classification independent. Do not count a missed timing window as a
   cut during a live write.
5. Repeat no-cut and between-command controls after active-cut series to detect
   cumulative card or filesystem changes.

## Qualification gates before CARDWRITE update

- Separate frozen `powercut07` source stage and package; all previous packages
  and save/output files hash unchanged.
- RTL simulation covers normal completion, target error, stalled/late response,
  exact length and address bounds, interruption at each modeled payload
  boundary, reboot/read-only classification, and preservation of the prior
  valid scratch generation. Review native screen captures.
- Existing vendor pin verification, Quartus full fit, all timing corners,
  resource and warning review, raw and bit-reversed RBF hashes, package hashes.
- Dedicated B007 updater derived from the audited B006 updater: exact card name,
  UUID and removable-media checks; complete inventory and raw backups; B007
  scratch file must be absent or match a separately reviewed pristine baseline;
  refuse all unexpected state; verify unrelated files and all old saves before
  and after; safe eject.
- A no-cut B007 Pocket control and read-only recovery pass before attempting an
  active cut.

## Remaining uncertainty

The B006 card used so far is one card/sample. This study initially samples one
controller/card/firmware combination and manual physical power interruption.
Repeated success cannot be generalized to all cards, temperatures, power rails,
filesystem states, or write workloads. Encryption/authentication, adversarial
tampering, and multi-card qualification are separate questions.

## Hardware progress — 2026-10-06

B007R5's no-cut and completed-command power-cycle controls passed exact host
image checks and protected-file comparisons. The first manual active-write
candidate produced a mixed tag-0/tag-1 image but its JTAG payload stayed stale,
so its active timing is unverified. The following three trials all captured
JTAG samples with an acknowledged live command and DONE low before the link
dropped at power-off. All three left stable, mountable, 262,144-byte mixed
images with four tag transitions and zero unknown words; no unrelated files
changed. The host oracle measured 55,299/10,237 old/new words in CUT2,
27,651/37,885 in CUT3, and 20,483/45,053 in CUT4. On CUT3 the core cold-read
the torn image, rejected both candidates, and disabled writes (`MISMATCH NO
WRITE`); JTAG confirmed all 65,536 words, no target error, `selected_valid=0`,
and `can_write=0`. Each torn file is preserved and each scratch was restored
with the guarded procedure to the known tag-1 image. This supports repeatable
detection and fail-closed behavior on this one card/setup, but does not prove
atomic updates or exact power-rail timing. A subsequent unmonitored shutdown
after A also produced a mixed image and passed the same fail-closed read test;
it is explicitly not counted among the three JTAG-observed cuts or as a no-cut
control. After restoring and cold-reading tag 1, a post-cut clean-stop control
completed three writes, stopped with B, passed cold read as tag 0, and remounted
as the exact expected operation image with protected files unchanged. A second
post-cut between-command power-cycle control stopped with no command active,
then cold-read and remounted as the exact tag-0 image with protected files
unchanged. The first-pass post-cut controls now pass; three additional varied
active-cut trials are the recommended optional extension for stronger
repeatability evidence. See `CURRENT_STATUS.md` and its linked per-run
JTAG/host evidence.
