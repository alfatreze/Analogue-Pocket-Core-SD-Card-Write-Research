# Results

Each suite uses the same reporting order: **Goal**, **Method**, **Corrections**, then **Result details**. “Corrections” records changes made during the work, including test-harness or tooling fixes; use “None recorded” when there were none. Procedure docs and the chronological [CURRENT_STATUS.md](../status/CURRENT_STATUS.md) retain deeper details. Simulation, Quartus fit, immediate readback, cold reload, and host-remount verification are different evidence levels.

## Official control and initial probe

**Goal:** Establish a documented reference behavior and verify that intended bytes are actually stored.

**Method:** Run the official target-data control and a minimal custom CPU-free probe; compare the complete remounted file against an independent byte oracle, then cold-read it.

**Corrections:** The custom probe's observed output did not match the intended record. The record oracle was kept unchanged; the observation was classified as a failure rather than redefining success.

**Result details:** FSM-001 changed physical bytes but failed intended-record verification. A generation-zero/shifted-data pattern explained the mismatch diagnostically, not as a valid format. No repeatability, cold-persistence, or interruption-safety claim follows. See [FSM-001 status](../status/CURRENT_STATUS.md#fsm-001--first-pocket-observation) and [first hardware run](../procedures/FIRST_HARDWARE_RUN.md).

## B003R2 batch baseline

**Goal:** Exercise repeated bounded writes/reads, shrinking overwrites, and a fresh-launch read-only pass using the minimal CPU-free BRAM/FSM core.

**Method:** Run the 32-case batch, retain JTAG operation records, remount and compare the complete guarded file, then start a fresh read-only pass and remount again.

**Corrections:** The initial System Console invocation returned success without executing its script because stdin was closed. The runner was changed to hold interactive stdin, source the absolute script path, and require validated completion/request evidence. Frozen FPGA sources and the installed package were unchanged.

**Result details:** 38 write/read pairs passed and the complete 256 KiB file matched the independent oracle; all guards and protected files remained unchanged. A fresh-launch cold pass read and verified all 32 final regions without writes, and the second remount found the file unchanged. Exact full power-off actions were not separately confirmed. See [B003 procedure and results](../procedures/B003_HARDWARE_RUN.md) and [status log](../status/CURRENT_STATUS.md).

## B004R2 stress and cold reads

**Goal:** Test sustained changing-data updates, operation timing, and repeatable read-only recovery across fresh launches.

**Method:** Execute 10,000 write/read pairs (20,000 commands), retain every indexed record, perform ten separate fresh-launch sessions of 32 reads each, then compare the full 256 KiB file and protected contents after each host remount.

**Corrections:** The first B004 implementation's fit/timing issue was addressed in the qualified R2 build; the testbench and timing extrema checks were corrected and rerun. No physical result is inferred from those simulation/build fixes.

**Result details:** All 10,000 pairs and 320 cold reads passed; all eleven host whole-file checks passed. Final file SHA-256: `0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56`. One exFAT card was used. Full power-off was requested but not separately confirmed; interrupted writes, multi-card scope, and Tau CPU/playback remain unqualified. See [full B004R2 physical report](B004_RESULTS.md) and [B004 procedure](../procedures/B004_HARDWARE_RUN.md).

## B005 two-file recovery

**Goal:** Preserve an older valid record while alternating bounded updates to two preallocated files and test recovery at controlled between-command interruption points.

**Method:** Run bounded save batches and read-only recovery sessions, retain JTAG histories, independently replay event records, and verify physical file bytes and protected content after remount.

**Corrections:** The old console client leaked remote processes on SSH close. A scoped client was added to wait for explicit completion markers and close only its verified process. The independent replay verifier was also corrected to retain transport metadata; original evidence and failed campaign history were preserved.

**Result details:** 647 saves, 17 read-only recoveries, and seven between-command FPGA interruption recoveries passed their immediate oracles. The campaign stopped incomplete after a JTAG chain failure; it was not counted as a full campaign pass. Later read-only recovery and remount verified both preserved files and unrelated contents. Active SD power-loss timing was not tested. See [full B005 connected report](B005_CONNECTED_RESULTS.md), [B005 procedure](../procedures/B005_HARDWARE_RUN.md), and [JTAG workflow](../procedures/JTAG_WORKFLOW.md).

## B006 guard and initialization recovery

**Goal:** Validate complete fixed-region guards/received-word coverage and ensure damaged nonblank records are not mistaken for blank initialization candidates.

**Method:** Run RTL and host checks, then connected batches and controlled between-command recovery/power-cycle scenarios; remount and compare complete files, guards, and protected content.

**Corrections:** A test-harness text replacement accidentally altered an index and failed to inject the intended guard corruption. The frozen implementation was not changed for that harness issue; the testbench was corrected and rerun. A separate audit-replay harness issue was fixed without rerunning completed hardware trials.

**Result details:** 707 RTL trials passed. Connected campaigns included 325 saves/four between-command recovery checks, a follow-up 64-save remount check, and a full Pocket power cycle after a completed partial-record prefix. The previous valid generation was recovered and exact file hashes, guards, and protected contents passed remount checks. Active-command SD power-loss durability remains unqualified. See [B006 development](../procedures/B006_DEVELOPMENT.md), [hardware run](../procedures/B006_HARDWARE_RUN.md), and [partial-prefix power-cycle report](../procedures/B006_POWER_CYCLE_PREFIX.md).

## B007R3 and R4 fit attempts

**Goal:** Qualify full-file received-word coverage while rejecting missing words masked by duplicates.

**Method:** Fit two frozen Cyclone V builds using the 65,536-bit variable-indexed register-vector bitmap and inspect Quartus resource/fitter reports.

**Corrections:** R3's 46,914 ALM estimate showed the design exceeded device capacity. R4 fixed the stop-edge behavior but retained the same bitmap structure, intentionally preserving the coverage invariant while fit was checked independently.

**Result details:** Both builds failed fitter placement at about 254% of 18,480 available ALMs (R3: 46,914; R4: 46,936). Neither was installed. R5 then changed the bitmap implementation to infer M10K RAM; see the [B007 design record](../procedures/B007_ACTIVE_WRITE.md#read-completeness-implementation-update-b007r5) and preserved [R3](../../work/evidence/build-failure-powercut07r3.json)/[R4](../../work/evidence/build-failure-powercut07r4.json) reports.

## B007R5 CPU-free active-write study

**Goal:** Determine whether interrupted live writes leave detectable mixed data and whether cold recovery refuses to trust or overwrite that data.

**Method:** Qualify and install the isolated 256 KiB scratch-file writer; pass no-cut and between-command controls; perform three JTAG-observed active-write power cuts; host-remount and classify each whole file; cold-read torn images; verify unrelated files and post-cut controls.

**Corrections:** The first active-cut attempt's JTAG monitor sampled stale payload data, making its timing telemetry inconclusive. Later trials captured changing active-write samples before link loss at shutdown. The R3/R4 ALM fit failures were corrected in the R5 implementation using a synchronous M10K-backed coverage bitmap with sequential scan.

**Result details:** R5 passed full fit/timing review at 1,991 / 18,480 ALMs (11%), with 2,287 registers, 13 / 308 RAM blocks, and minimum reported slack +0.123 ns. No-cut, between-command power-cycle, clean-stop, and post-cut between-command controls passed exact host checks. All three monitored active cuts left stable, mountable mixed old/new scratch files; cold reads rejected the candidates and disabled writes. One accidental unmonitored shutdown also produced mixed data and was separately preserved, not counted as a controlled cut. Unrelated files remained unchanged. This supports fail-closed handling on one Pocket/card/firmware combination; it does not prove atomic writes, precise power-rail timing, or compatibility across cards. See [B007 procedure and run evidence pointers](../procedures/B007_ACTIVE_WRITE.md), [status log](../status/CURRENT_STATUS.md), and the [B007 experiment definition](../../experiments/b007.json).

## Tau CPU integration simulations (pre-B008 prototypes)

**Goal:** Reduce CPU/transport risks before joining the real CPU to the proven storage engine.

**Method:** Simulate the exact hash-pinned VexRiscv and Tau crossing with modeled APF responses; exercise command ownership, sequence wrap, record formats, recovery states, and fault cases against independent byte/file models.

**Corrections:** An Icarus run hit its global simulation budget at 302/322 commands without a terminal pass. A separate testbench increased only that budget; Verilator then completed the profile. A modeled missing-guard-word case also showed stale matching data could be accepted by one prototype; the gap was recorded and a received-word lease was added to the prototype, while preserving B006's hardware received-word mask requirement.

**Result details:** Five command profiles passed 300 commands each (1,500 total). Eight 64-save profiles passed (512 saves, 2,576 modeled APF commands) with exact modeled files/guards/CRC/generations. These are simulation results, not physical CPU-driven persistence, production CDC, Tau MMIO-map, playback, or card-durability qualification. B008's first gate is specified in [TAU_CPU_INTEGRATION.md](../research/TAU_CPU_INTEGRATION.md).

## Qualification interpretation

- A completed APF command, same-session readback, or simulation alone does not prove durable card bytes.
- Host remount plus exact whole-file comparison is required for physical persistence claims.
- Clean stop, Pocket power cycle between commands, and power loss during a live SD command are separate tests.
- A checksum detects accidental corruption; it does not authenticate hostile modification.
- Full gates and environment targets are in [RESEARCH_PLAN.md](../research/RESEARCH_PLAN.md) and [TAU_TEST_MATRIX.md](../research/TAU_TEST_MATRIX.md).
