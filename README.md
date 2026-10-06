# Analogue Pocket Core — SD Card Write Research

## Overall feasibility: demonstrated for bounded CPU-free writes; Tau qualification pending

**Progress: 60/100 · Discovery milestone score · Updated 2026-10-06**

`██████░░░░ 60%`

An Analogue Pocket core **can persist exact bounded updates to preallocated SD files** on the tested setup. The CPU-free writer passed a 10,000-pair stress campaign, repeated fresh-launch reads, and independent host file checks. Alternating-record saves recovered the last valid generation after the tested interruptions between commands. Recorded host comparisons found no unexpected changes to protected files.

**Power loss during an active overwrite can leave mixed old/new bytes.** Three monitored trials demonstrated this. Selected cold-read tests rejected torn files and disabled writes. Robust recovery of the alternating-record save format during active SD power loss, physical Tau CPU integration, playback performance, and broader card/firmware coverage remain to be established.

The score credits five completed **discovery milestones**, weighted to 60 points. Physical CPU integration, Tau workloads, and broader qualification account for the remaining 40. It is a planning score, not a measured success probability or a declaration that 60% of every test has passed. See the [scoring rubric and capability status](docs/research/FEASIBILITY_STATUS.md).

## Roadmap, test suites, and individual results

Every executed suite links to its own report. Each report and each recorded case follows **Goal → Method → Corrections → Result details**. A failed or inconclusive test remains visible in its report.

| Suite | What it investigates | Current outcome | Individual results |
|---|---|---|---|
| Official reference control | Install the unchanged official example and establish a comparison baseline. | Installation verified; functional save/reload result pending. | [Control report](docs/results/CONTROL_RESULTS.md) |
| FSM-001 — initial minimal writer | Persist one exact 64-byte record with a CPU-free APF writer. | Completed with incorrect stored bytes; retained failure. | [FSM-001 report](docs/results/FSM001_RESULTS.md) |
| FSM-002 — corrected minimal writer | Repair serial timing/startup, then write, remount, and fresh-launch read. | Exact record and readback passed; wrong-build attempt retained. | [FSM-002 report](docs/results/FSM002_RESULTS.md) |
| B003R2 — automatic batch | Check payload sizes/ranges, repeated and shrinking overwrites, guards, and cold reads. | 32 cases / 38 pairs and 32 cold reads passed host checks. | [B003 report](docs/results/B003_RESULTS.md) |
| B004R2 — stress | Measure 10,000 changing-data pairs and ten fresh-launch cold sessions. | 20,000 warm commands, 320 cold reads, eleven host checks passed. | [B004 report](docs/results/B004_RESULTS.md) |
| B005 — alternating records | Recover a valid generation after controlled interruptions between commands. | Stopped prefix preserved; separate resume reached 649 saves/eight FPGA recoveries. | [B005 report](docs/results/B005_CONNECTED_RESULTS.md) |
| B006 — complete guards and recovery | Reject incomplete/damaged records; verify guarded saves and partial-prefix power cycling. | 707 RTL trials; 325 + 64 saves; four FPGA recoveries; one Pocket power-cycle check passed. | [B006 report](docs/results/B006_RESULTS.md) |
| B007R3/R4/R5 — fit qualification | Fit exhaustive received-word coverage while preserving missing/duplicate rejection. | R3/R4 failed at 254% ALMs; RAM-backed R5 passed at 11%. | [B007 fit report](docs/results/B007_FIT_RESULTS.md) |
| B007R5 — active-write power loss | Characterize torn writes, read-only refusal, protected content, and post-cut controls. | Three monitored cuts left mixed data; selected refusal checks and controls passed. | [B007 interruption report](docs/results/B007_RESULTS.md) |
| Exact Tau CPU prototypes | Model command ownership, crossing, recovery formats, faults, and long save sequences. | Modeled profiles passed; reset and original missing-word limitations documented. Hardware pending. | [CPU simulation report](docs/results/CPU_SIM_RESULTS.md) |
| **B008 — CPU/engine integration** | Join pinned 60 MHz VexRiscv to the proven storage engine; qualify ownership, CDC, reset, then hardware persistence. | **Next implementation gate.** | [Plan](docs/research/TAU_CPU_INTEGRATION.md#b008-first-implementation-gate); no result yet. |
| Tau functional/workload qualification | Test settings, resume/diagnostics, memory sources, and idle/paused/playback save budgets. | Planned. | [Tau catalogue](docs/research/TAU_TEST_MATRIX.md); no result yet. |
| Environment/endurance qualification | Repeat declared capabilities across cards, filesystems, firmware, fragmentation, and lifecycle conditions. | Planned. | [Qualification targets](docs/research/RESEARCH_PLAN.md#qualification-and-stop-rules); no result yet. |

The [research plan](docs/research/RESEARCH_PLAN.md) sets the method order and qualification gates. The [Tau test catalogue](docs/research/TAU_TEST_MATRIX.md) defines the detailed protocol, destination protection, invalid-input, CPU/memory, recovery, workload, and environment cases.

## Project and documentation

This isolated research project uses synthetic fixtures on the designated CARDWRITE test card. Tau Alpha supplies pinned read-only references. Full results are indexed under [docs/results](docs/results/README.md); the [documentation map](docs/README.md) covers plans, procedures, build audits, and the [chronological evidence log](docs/status/CURRENT_STATUS.md).

## Clone and use

```sh
git clone --recurse-submodules https://github.com/alfatreze/Analogue-Pocket-Core-SD-Card-Write-Research.git
```

Simulation requires Python 3 and Icarus Verilog; see the [Makefile](Makefile) for targets. Upstream pins are in `vendor/PINNED.json`. Hardware update tools require the designated disposable card identity, reviewed changes, backups, and protected-file comparison.

## License

Original project work is under the [MIT License](LICENSE). Third-party terms and provenance are in [NOTICE.md](docs/legal/NOTICE.md).
