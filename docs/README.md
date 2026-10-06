# Documentation

Project documentation is grouped by its role. The repository-root [README](../README.md) is the GitHub landing page; this page is the full documentation index.

## Research and architecture

- [Research plan](research/RESEARCH_PLAN.md) — stages, methods, gates, and stop rules.
- [Future tests](research/FUTURE_TESTS.md) — parked directory, library, cover-optimization, and playlist investigations.
- [Experiment notes](research/EXPERIMENTS.md) — early test outline and run record template.
- [Tau test catalogue](research/TAU_TEST_MATRIX.md) — protocol, security, recovery, CPU, workload, and endurance cases.
- [Tau CPU integration](research/TAU_CPU_INTEGRATION.md) — B008 plan and modeled CPU results.
- [B008 mailbox architecture](research/B008_MAILBOX.md) — ownership, register map, reset/timeout policy and simulation reproduction.
- [Core knowledge](research/CORE_KNOWLEDGE.md) — selected Analogue Pocket development knowledge.
- [Tau repository research](research/REPO_RESEARCH.md) — read-only findings from Tau Alpha.
- [Decision log](research/DECISIONS.md) — architecture choices, corrections, and rationale.

## Results and feasibility

- [Overall feasibility and progress rubric](research/FEASIBILITY_STATUS.md) — current capability status and 60/100 discovery score.
- [Results index](results/README.md) — every suite and its individual report.
- [Official control](results/CONTROL_RESULTS.md), [FSM-001](results/FSM001_RESULTS.md), and [FSM-002](results/FSM002_RESULTS.md) — preparation, first failure, corrected minimal baseline.
- [B003 batch](results/B003_RESULTS.md) and [B004 stress](results/B004_RESULTS.md) — bounded-write and sustained-repeatability evidence.
- [B005 recovery](results/B005_CONNECTED_RESULTS.md) and [B006 guards](results/B006_RESULTS.md) — alternating records and interruption boundaries.
- [B007 fit](results/B007_FIT_RESULTS.md) and [B007 active cuts](results/B007_RESULTS.md) — redesign, tearing, and selected cold-read refusal.
- [B008 CPU/engine gate](results/B008_RESULTS.md) — actual-CPU simulation, fault/reset trials, observed bus correction and next hardware prerequisites.
- [CPU simulations](results/CPU_SIM_RESULTS.md) — exact generated CPU prototype findings.
- [Result template](results/TEMPLATE.md) — required suite/case reporting order.
- [Chronological status](status/CURRENT_STATUS.md) — dated engineering timeline; original B004/B005 reports are retained in `status/archive/`.

## Procedures and test plans

- [First hardware run](procedures/FIRST_HARDWARE_RUN.md) — official reference and initial probe procedure.
- [Next hardware run](procedures/NEXT_HARDWARE_RUN.md) — historical minimal-core procedure.
- [B003 hardware run](procedures/B003_HARDWARE_RUN.md) — batch and cold-read protocol/results.
- [B004 hardware run](procedures/B004_HARDWARE_RUN.md) — stress and repeated cold-read protocol/results.
- [B005 hardware run](procedures/B005_HARDWARE_RUN.md) — alternating-record recovery campaign.
- [B006 development](procedures/B006_DEVELOPMENT.md) and [hardware run](procedures/B006_HARDWARE_RUN.md) — guards, initialization, and connected tests.
- [B006 partial-prefix power cycle](procedures/B006_POWER_CYCLE_PREFIX.md) — controlled recovery boundary.
- [B007 active-write study](procedures/B007_ACTIVE_WRITE.md) — active-write cut methodology, controls, and evidence.
- [Batch test plan](procedures/BATCH_TEST_PLAN.md) — automated case families.
- [JTAG workflow](procedures/JTAG_WORKFLOW.md) — console, capture, reload, and safety workflow.

## Build and legal references

- [Build audit](build/BUILD_AUDIT.md) — build identities, resources, timing scope, and limitations.
- [Third-party notices](legal/NOTICE.md) — provenance and applicable third-party terms.
- [MIT License](../LICENSE) — original project work.

## Repository-only guidance

`AGENTS.md` remains at the repository root so coding agents load the project working agreements before editing. `README.md` and `LICENSE` also remain at the root for GitHub discovery and license detection. Vendored upstream documentation stays with its source and is not duplicated here.
