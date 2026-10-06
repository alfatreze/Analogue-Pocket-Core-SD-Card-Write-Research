# Analogue Pocket Core — SD Card Write Research

An independent research project to determine whether an Analogue Pocket core can write its own SD-card data safely, repeatably, and without changing Tau's music or other protected files. All physical writes use a dedicated scratch file on the designated test card. Tau Alpha remains a read-only reference; its repository and build outputs are not modified.

## Current report — B007R5

**Goal:** Determine whether the CPU-free writer detects incomplete data after power is removed during a live SD write.

**Method:** Run the qualified B007R5 core with external JTAG observation; power off during active writes; remount and compare the complete scratch file; cold-read torn images; check unrelated files.

**Corrections:** R3/R4's register-expanded coverage bitmap exceeded the FPGA's ALM capacity. R5 changed coverage tracking to an M10K-backed bitmap and passed full Quartus fit/timing review.

**Result details:** Three monitored active cuts left stable, mountable mixed old/new files. Cold reads rejected each torn image and disabled further writes. Clean-write, stop, restart, and between-command power-cycle controls passed exact host-side checks; unrelated files remained unchanged. Fit used 1,991 / 18,480 ALMs (11%), with minimum reported slack +0.123 ns. Evidence is limited to one Pocket, one exFAT card, and one firmware setup; it does **not** establish atomic writes or general power-loss safety. Optional extra cuts are deferred. Next is B008 CPU integration using the pinned Tau VexRiscv path.

Full results, limits, and evidence links: [Results](docs/results/). The detailed dated log remains in [CURRENT_STATUS.md](docs/status/CURRENT_STATUS.md).

## Roadmap and test suites

The sequence progresses from isolated storage behavior to the real Tau CPU and workloads. Each stage keeps its own build and evidence; later stages reuse the same deterministic payloads and independent host oracle.

| Stage | Test suite | What it tests | Status / gate |
|---|---|---|---|
| 0 | [Protocol, fixtures, and observability](docs/research/RESEARCH_PLAN.md#phase-0--freeze-the-protocol-fixtures-and-observability) | Freeze source/build/card identity, slot map, payload corpus, hashes, command traces, host oracle, and protected-file manifest before a hardware run. | Ongoing discipline for every stage. |
| 1 | [Official reference control](docs/research/RESEARCH_PLAN.md#phase-1--establish-an-independent-reference-control) | Establish what the official target-data example does on the same Pocket/card, including post-Quit and cold-restart file contents. | Earlier control evidence; see [Results](docs/results/). |
| 2 | [Minimal CPU-free writer](docs/research/RESEARCH_PLAN.md#phase-2--minimal-custom-core-no-cpu) | Compare documented APF write and nonvolatile paths with BRAM/FSM only; test create/update, readback, Quit, reopen, and cold persistence. | B003–B007 built this baseline. B007R5 passed the initial active-write study. |
| 3 | [Recovery formats and write strategies](docs/research/RESEARCH_PLAN.md#phase-3--recoverable-formats-and-alternative-approaches) | Compare preallocated files, alternating records, journals, commit markers, chunking, and bounded/coalesced saves. Test torn/corrupt data and whether the last valid state is retained. | Initial A/B-record recovery methods tested; broader format and interruption qualification remains. |
| 4 | [Exact Tau CPU and command path](docs/research/RESEARCH_PLAN.md#phase-4--the-same-cpu-and-command-path-as-tau) | Add the pinned VexRiscv and command crossing, then test MMIO ownership, CDC, BRAM publication, memory sources, busy/error/timeout/reset cases against the CPU-free baseline. | **B008 next.** Existing CPU prototypes pass modeled simulations but do not establish physical CPU-driven persistence. |
| 5 | [Tau workloads and qualification](docs/research/RESEARCH_PLAN.md#phase-5--tau-workloads-and-qualification) | Test settings first, then resume/bookmarks and diagnostics; measure playback audio/FIFO impact, command latency, memory use, and protected-file integrity. | Not yet qualified. |
| 6 | [Environment and endurance matrix](docs/research/TAU_TEST_MATRIX.md#environment-and-long-run-campaign) | Exercise declared firmware, card/filesystem, fragmentation, long-run, and repeatability conditions; state limits per environment. | Not yet qualified. |

### Suite coverage

The [Tau test catalogue](docs/research/TAU_TEST_MATRIX.md) defines detailed cases for protocol and persistence boundaries, destination security, invalid inputs, CPU/BRIDGE/memory correctness, recovery/interruption, functional playback and performance, and environment/endurance. “Exhaustive” means covering the declared invariants, boundaries, and risk combinations; it does not mean testing every possible byte string or card.

## Research documents

- [Results index](docs/results/) — concise outcomes by build/campaign and links to detailed records.
- [Research plan](docs/research/RESEARCH_PLAN.md) — staged method, gates, and stop rules.
- [Tau test catalogue](docs/research/TAU_TEST_MATRIX.md) — detailed functional, safety, recovery, and performance tests.
- [Current status log](docs/status/CURRENT_STATUS.md) — chronological implementation, build, and hardware evidence.
- [B007 active-write procedure](docs/procedures/B007_ACTIVE_WRITE.md) — design, controls, and interruption protocol.
- [B008 CPU integration plan](docs/research/TAU_CPU_INTEGRATION.md) — next integration gate and existing simulation scope.
- [Core and platform knowledge](docs/research/CORE_KNOWLEDGE.md) — selected Analogue Pocket development references.
- [Local Tau repository research](docs/research/REPO_RESEARCH.md) — read-only findings from Tau Alpha.
- [Decision log](docs/research/DECISIONS.md) — rationale, corrections, and scope decisions.
- [Documentation map](docs/README.md) — complete index grouped by purpose.

## Getting started

```sh
git clone --recurse-submodules https://github.com/alfatreze/Analogue-Pocket-Core-SD-Card-Write-Research.git
```

Simulation requires Python 3 and Icarus Verilog; see the [Makefile](Makefile) for targets. The pinned vendor sources are documented in `vendor/PINNED.json`. Hardware update tools are bound to the designated disposable card identity and require an audited plan, backups, and protected-content comparison. Do not use them on a production card.

## License

Original project work is licensed under the [MIT License](LICENSE). Third-party framework code, IP, assets, and generated artifacts retain their applicable terms; see [NOTICE.md](docs/legal/NOTICE.md).
