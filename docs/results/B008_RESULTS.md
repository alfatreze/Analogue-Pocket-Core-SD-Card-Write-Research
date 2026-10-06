# B008 — exact CPU supervising the B007 engine

[All results](README.md) · [Mailbox architecture and reproduction](../research/B008_MAILBOX.md)

## Goal

Execute the pinned Tau VexRiscv with the unchanged B007R5 storage engine, while
preserving single transfer ownership, cold-read gating, coherent clock crossing,
and safe CPU reset/timeout behavior before preparing a Pocket build.

## Method

An isolated dual-clock CPU/16 KiB memory/MMIO harness supervises B007 through
`rtl/b008_mailbox.sv`. A modeled APF target supplies genuine delayed completion,
stale DONE, error, incomplete receipt and timeout scenarios. Four nominal CPU
clock rates and shifted engine phases exercise command flow. Fourteen trials
use 1 KiB fixtures; one uses the full 256 KiB B007 image. Independent host code
compares every final file word; the full-size case also uses the unchanged B007
oracle. A separate Icarus test checks the mailbox directly. No card writes,
Quartus build, JTAG operation or Tau source edit occurred.

## Corrections

Two initial CPU runs passed eight trials each, then timed out on the idle-reset
profile. The mailbox incorrectly required the Wishbone bus to drop between
all beats. Consecutive distinct register accesses from the actual CPU required
recognizing the next address/control beat; unchanged held beats still act once.
A directed-test assertion was also moved after the consuming engine edge.
Failed logs/source hashes remain separately archived and listed in public
evidence. Later complete regression passed. B007R5 RTL and pinned CPU hashes
are unchanged.

## Result details

**PASS — first isolated simulation gate:** 15 CPU trials plus one directed
mailbox campaign. CPU trials contain 24 modeled reads, ten attempted writes,
seven completed writes and four CPU-only resets. Thirty-two directed coherent
snapshot trials also passed. Expected fault cases remain successful refusal
tests; they are not successful writes. Two earlier CPU runs remain failed,
and the early directed assertion was a test-harness correction.

Progress stays **60/100**: physical CPU persistence has not yet earned its
milestone. Metastability, bundled-data timing/constraints, actual Pocket SoC,
FPGA fit, cache publication for CPU-owned payloads, full Tau MMIO mapping,
playback and physical power-loss behavior remain unqualified. Reset coverage
uses the stated phases and durations, not an exhaustive timing sweep. Errors
occur before modeled payload copying; partial-error write recovery is deferred.

### B008-00 — normal command flow and clock ratios

**Goal:** Cold-read gating, serial start/stop, wrong-state rejection and coherent final read must work with the exact CPU.

**Method:** Run profile 0 at nominal 50, 60, 74.25 and 90 MHz CPU rates with differing engine phases; begin with stale high DONE. CPU checks cold-required and invalid-command responses, validates a read, starts one write, rejects READ while writing, stops, then reads. Compare every modeled file byte independently.

**Corrections:** None recorded in these four trials.

**Result details:** PASS: four 1 KiB trials; each performed two reads, one write, one completed write and exact tag-1 output.

### B008-01 — target read error

**Goal:** A target read error must prevent write enable.

**Method:** Return target error 3 on the first read before copying payload; CPU requests START after observing fault.

**Corrections:** None recorded.

**Result details:** PASS: one read, zero writes; engine fault and START rejection. Every initial file byte preserved.

### B008-02 — target write error

**Goal:** A failed write must not be counted as a completed save or unlocked by recovery.

**Method:** Validate a cold read, start a write, return target error 3 before copying payload, then request recovery.

**Corrections:** None recorded.

**Result details:** PASS: one read, one attempted write, zero completed writes; recovery rejected and baseline bytes unchanged. This models an early error, not partial physical write failure.

### B008-03 — timeout and delayed DONE

**Goal:** Timeout must retain outstanding ownership and prevent retry even when completion arrives later.

**Method:** Stall the first write past 200,000 engine cycles, attempt recovery/start after status 7, then supply late DONE. Independently check active owner, source range and final file.

**Corrections:** None recorded.

**Result details:** PASS: one attempted write, zero completed writes; status 7 and active owner remain after late DONE; no retry; initial bytes preserved.

### B008-04 — mixed cold image

**Goal:** A mixture of valid operation tags must be rejected before writing.

**Method:** Replace one word of the tag-0 fixture with tag-1 data; deliver a complete read and attempt START after fault.

**Corrections:** None recorded.

**Result details:** PASS: one read, zero writes; mismatch rejected and mixed fixture preserved exactly.

### B008-05 — CPU reset while idle

**Goal:** Reset must lock new submissions and permit explicit recovery only from safe idle.

**Method:** Complete a valid read, trigger CPU-only reset, reboot firmware with retained RAM cookie, attempt START while locked, recover, and read again.

**Corrections:** Initial two runs timed out because the mailbox required CYC/STB to fall between all beats. Actual VexRiscv kept the bus active while moving to another register. The adapter now identifies a new address/control beat and still handles an unchanged held beat once. Both failed logs and hashes remain archived; directed bus regression and all CPU trials passed after correction.

**Result details:** PASS after correction: one CPU reset, two reads, zero writes, exact original file; lock rejection and safe recovery checked. Original attempts remain failed.

### B008-06 — CPU reset during live write

**Goal:** Reset must request a clean stop without releasing or changing the live transfer.

**Method:** Reset CPU after write acknowledgement with DONE low. Restarted firmware verifies reset lock, waits for idle, recovers and reads. Engine clock and B007 state continue.

**Corrections:** Uses the bus correction from B008-05; no separate case correction.

**Result details:** PASS: one reset, two reads, exactly one completed write and exact tag-1 file. Source remained fixed until modeled genuine completion.

### B008-07 — CPU reset during live read

**Goal:** A read owner must survive CPU reset and finish before recovery.

**Method:** Reset CPU while the first cold-read target is active; reboot, observe lock, wait for safe idle, recover and repeat the read.

**Corrections:** Uses the bus correction from B008-05; no separate case correction.

**Result details:** PASS: one reset, two complete reads, zero writes and unchanged baseline file.

### B008-08 — delayed acknowledgements/completion

**Goal:** Command delivery must remain distinct from target completion.

**Method:** Repeat normal flow with 1,000 engine-cycle target delays and stale DONE before each acknowledgement.

**Corrections:** None recorded.

**Result details:** PASS: two reads, one completed write, exact tag-1 file; no second target owner while busy.

### B008-09 — missing word plus duplicate

**Goal:** An exact received count must not hide incomplete address coverage.

**Method:** Omit the final receive address and duplicate the preceding one, retaining the total word count; attempt START after refusal.

**Corrections:** None recorded.

**Result details:** PASS: one read, zero writes; B007 coverage scan rejected the image despite the matching count. Baseline file preserved.

### B008-10 — CPU reset plus timeout

**Goal:** CPU reset must not provide an escape from a timed-out live transfer.

**Method:** Reset during a stalled write, run rebooted firmware until timeout, request recovery and later supply DONE.

**Corrections:** Uses the bus correction from B008-05; no separate case correction.

**Result details:** PASS: one reset, one attempted write, zero completions, recovery refused; active ownership retained after late DONE and file preserved.

### B008-11 — full B007 image

**Goal:** Reduced fixtures must be backed by an exact full-size engine/CPU transfer.

**Method:** Repeat profile 0 with 262,144 bytes / 65,536 words. Compare all resulting bytes to the unchanged tools/b007_oracle.py image(1).

**Corrections:** None recorded.

**Result details:** PASS: two full reads and one completed write; exact tag-1 SHA-256 00aec285fa738e1225c201774629ea5af4bd630f89f64976fbb5ad632a8f7a6a.

### B008-12 — directed mailbox/bus checks

**Goal:** A held beat and competing submission must not cause extra engine actions; responses must remain coherent through reset.

**Method:** Icarus directed test: hold a beat for 16 CPU cycles, submit a second command while pending, run 32 correlated snapshots, use consecutive changed-register beats without dropping CYC/STB, reject a byte-strobe command, reset a pending snapshot, and reset a pending START.

**Corrections:** An early testbench assertion sampled the consumer pulse before its next engine edge and incorrectly reported zero actions. Delay that assertion until the consumer edge. The held-bus correction above is explicitly regression-tested. No B007 engine change.

**Result details:** PASS: one held-read action, competing submission rejected without changing command/toggle, 32 coherent snapshots, byte-write rejected, pending snapshot preserved across reset, pending START refused by reset guard, and explicit safe recovery.

### Evidence and next gate

[Structured hashes, trial logs and retained failures](../../work/evidence/b008-cpu-engine-simulation.json).
The evidence identifies private generated logs, firmware, source snapshots and
whole-file outputs under `work/sim/b008/`. Compilation warnings were reviewed:
existing pinned CPU/B007 width truncation/extension, bounded testbench index
widths, missing source timescales and runtime clock-delay warnings. The new
mailbox has no width, latch or multiple-driver diagnostic in these runs; this
review does not substitute for synthesis or STA.

Next: prepare a distinct synthesizable B008 top-level with CPU clock/BRAM and
reviewed reset/CDC wiring, capture its native screen, freeze sources, then fit
and inspect complete timing/resources before any Pocket installation. Retain
B007/B006 outputs and packages. Hardware cold-read/write/stop/restart/host
verification remains pending.
