# Analogue Pocket Core - SD Card Write Research

Local project folder: `APC - Card Write Research`.

## Purpose

An isolated Tau Alpha research project for testing how an Analogue Pocket core can create and reliably update files on the Pocket SD card. The emphasis is on repeatable hardware experiments, clear evidence, and recovery from interrupted or failed writes.

This directory is standalone. It does not change or share implementation state with `tau-alpha`, `Tau Omega`, or the other Tau variants. Those repositories are references only.

## Current scope

Investigate, compare, and document:

1. APF-managed nonvolatile data-slot writeback when the core is quit.
2. Core-initiated target data-slot writes (`0x0184`, and `0x0185` if useful).
3. Explicit target flush (`0x0188`) only as a separate, uncertain path.
4. File creation when no save exists yet, repeated updates, size changes, and power/menu/shutdown boundaries.

The first experiments should use a disposable test card and small deterministic payloads. No existing project or production save data is a test target.

## Research files

- [Core and platform knowledge](CORE_KNOWLEDGE.md) — selected knowledge from Tau's `analogue-pocket-dev` skill.
- [Local repository research](REPO_RESEARCH.md) — existing card-write code and hardware results found in Tau Alpha.
- [Experiment plan](EXPERIMENTS.md) — staged questions, measurements, and result template.
- [Research plan](RESEARCH_PLAN.md) — method order, isolation strategy, durability definitions, qualification and decision gates.
- [Tau test catalogue](TAU_TEST_MATRIX.md) — conditional qualification suite based on actual Tau needs.
- [Decisions](DECISIONS.md) — rationale and corrections to the initial evidence summary.
- [Build audit](BUILD_AUDIT.md) — source and bitstream identities, timing scope and remaining interface limitations.
- [Current status](CURRENT_STATUS.md) — actual implementation/build/card evidence and next gate.
- [JTAG workflow](JTAG_WORKFLOW.md) — cable compatibility, debug captures, reload and USB card access.
- [Batch test plan](BATCH_TEST_PLAN.md) — automatic case batches after transport repair, with independent file records and guard checks.
- [B003 hardware run](B003_HARDWARE_RUN.md) — one 32-case session, retained JTAG results and independent whole-file verification.
- [Next hardware run](NEXT_HARDWARE_RUN.md) — corrected CARDWRITE02, physical byte verification and cold reload.
- [First hardware run](FIRST_HARDWARE_RUN.md) — official control and minimal-probe instructions.

## Evidence rules

- Record Pocket firmware version, framework requirement, core build ID/hash, slot definition, card identity, exact actions, and result for every hardware run.
- Label evidence as source-verified, docs-verified, community-reported, simulated, or Pocket hardware-confirmed. A successful command result is not proof that the intended bytes reached the intended file: read back and compare.
- Keep failures and superseded conclusions. Never promote a community report to fact without a reproducing test.
- Make one change per run. Use distinctive patterns and checksums, then quit and relaunch to check persistence.

## Starting position

Start with the official target-data example as a control, then a minimal BRAM/FSM core comparing a dedicated target write and APF nonvolatile shutdown writeback. Bring in Tau's VexRiscv CPU only after one method passes independent persistent-file verification. See RESEARCH_PLAN.md for the current sequence; it supersedes the shorter initial experiment ordering.


## Clone and use

Clone this repository with its pinned upstream submodules:

```sh
git clone --recurse-submodules https://github.com/alfatreze/Analogue-Pocket-Core-SD-Card-Write-Research.git
```

Requirements for simulation: Python 3 and Icarus Verilog. `make test` runs the host and RTL checks. The retained first build, packages and report hashes are under `work/`; simulation executables and local card-content inventories are excluded from Git.

The first build stage is frozen evidence. `make prepare` refuses to replace it; use a new build stage for subsequent experiments. VM connection defaults in `tools/vm_build.py` describe the original local setup and must be adapted before building elsewhere. Card installation is deliberately bound to the original designated CARDWRITE volume UUID; configure a separate disposable card explicitly before using these tools on another setup.

Minimal02 has one verified physical 64-byte write and a successful reload readback observation. Repeatability, interrupted-write safety and Tau integration remain pending. See CURRENT_STATUS.md. `make test-batch` exercises B003's 32 cases, cold read and failure paths; `python3 sim/test_update.py` and `python3 sim/test_jtag.py` check temporary-card updater behavior and mocked Tcl handshake semantics.


## License

Original project work is licensed under the [MIT License](LICENSE). Third-party framework code, IP, assets and generated artifacts retain their applicable terms; see [NOTICE.md](NOTICE.md) for the scope and provenance.

## Current experiment: B004R2 stress

[B004 procedure](B004_HARDWARE_RUN.md) describes the 10,000-pair changing-data stress profile, complete retained failure history and repeated cold-read checks. Simulation and full compilation/internal timing pass. B004R2 (version 0.4.2) is installed in the same CARDWRITE02 entry with verified B003 backups and preserved prior results. The first physical 10,000-pair session passes: all 10,000 retained records validated, 20,000 commands, zero failures. After remount, the complete final file and guards match exactly and no protected files changed. Ten separate fresh-launch read-only sessions each pass all 32 saved regions with zero writes/failures; all subsequent remount checks confirm the entire file and all prior contents remain unchanged. Repeated power cycles, interruption recovery and Tau CPU integration remain pending. Full compressed history and its summary are preserved under work/evidence; earlier failed/stopped stages are retained.

Completed initial campaign: [physical results and next experiment](B004_RESULTS.md).

## Next experiment: B005 recovery

[B005 procedure](B005_HARDWARE_RUN.md) defines alternating preallocated records, a 64-commit clean batch, read-only recovery and controlled interruption discovery before Tau CPU integration. Simulation and host/mock checks pass; full compile and physical results are recorded separately in CURRENT_STATUS.md. `make test-recovery` exercises the implementation. B005 retains the stable CARDWRITE02 entry and distinct version 0.5.0/banner.

B005 now passes full compilation and internal timing qualification and is installed as version 0.5.0. The original example and CARDWRITE01 entries have been backed up and removed from the designated card, preserving all assets and prior results. The first physical 64-save session and read-only matching-SOF reload pass. An extended connected campaign is in progress; complete remount/file/protected-content checks remain pending. See [installation summary](work/evidence/b005-installation-summary.json) and [build audit](BUILD_AUDIT.md).


## B006 and CPU preparation

[B006](B006_DEVELOPMENT.md) adds full fixed-region guard/received-word validation and refusal to initialize damaged nonblank records. All 707 RTL trials pass. Compile/internal timing and physical trial status are recorded in CURRENT_STATUS.md; [hardware procedure](B006_HARDWARE_RUN.md) preserves the existing B005 files.

[Tau integration preparation](TAU_CPU_INTEGRATION.md) uses exact hash-pinned read-only CPU/crossing references. Crossing simulation passes 1,200 modeled commands; actual generated-CPU firmware execution passes another 1,500. These are simulation results, with physical CPU persistence and playback qualification pending.


## Latest connected result

[B005 connected results](B005_CONNECTED_RESULTS.md): 647 saves and seven between-command FPGA interruption recoveries pass their immediate oracles. The planned campaign stopped on a JTAG connection failure; full physical remount/power-loss qualification remains pending. B006 is fully compiled/internal-timing qualified with 707 passing RTL trials, but was not loaded after the connection fault. CPU save-format and received-mask prototypes pass isolated modeled-transport checks; actual CPU-driven Pocket persistence remains pending. New console session tooling prevents the observed remote-process leak.

- Long exact-CPU simulations now pass eight recovery starting states, 512 modeled saves / 2,576 commands with exact full-file checks. Both harness failures remain documented; physical card persistence and full Tau integration remain unqualified. Details: [TAU_CPU_INTEGRATION.md](TAU_CPU_INTEGRATION.md).

## Resumed Pocket trial

B005's separately resumed point-3/control/repair trial passed, reaching generation 649 with both records valid. The original stopped campaign stays immutable. B006 is physically loaded via qualified JTAG and its initial full-file/guard recovery passed; five 64-save batches plus one four-point interruption round are in progress. SD metadata/bitstream still remain B005 until a later verified remount/update. See [B006_HARDWARE_RUN.md](B006_HARDWARE_RUN.md).

### Latest physical result

B006 completed 325 saves and four between-command FPGA interruption recoveries. Final host remount verified both complete guarded files at generations A973/B974, preserved unrelated contents, and the qualified B006 version 0.6.0 is installed in the stable CARDWRITE02 entry. See CURRENT_STATUS.md and work/evidence/b006-final-card-verification.json. Actual SD power-loss durability remains pending.

A follow-up after SD installation ran 64 B006 saves; all records passed and the subsequent host remount matched both full files at generations A1037/B1038. See CURRENT_STATUS.md and work/evidence/b006-post-install-64-remount-summary.json.
