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

[B004 procedure](B004_HARDWARE_RUN.md) describes the 10,000-pair changing-data stress profile, complete retained failure history and repeated cold-read checks. Simulation and full compilation/internal timing pass. B004R2 (version 0.4.2) is installed in the same CARDWRITE02 entry with verified B003 backups and preserved prior results. The first physical 10,000-pair session passes: all 10,000 retained records validated, 20,000 commands, zero failures. After remount, the complete final file and guards match exactly and no protected files changed. Seven separate fresh-launch read-only sessions each pass all 32 saved regions with zero writes/failures; all subsequent remount checks confirm the entire file and all prior contents remain unchanged. Repeated power cycles, interruption recovery and Tau CPU integration remain pending. Full compressed history and its summary are preserved under work/evidence; earlier failed/stopped stages are retained.
