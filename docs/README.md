# Documentation

Project documentation is grouped by its role. The repository-root [README](../README.md) is the GitHub landing page; this page is the full documentation index.

## Research and architecture

- [Research plan](research/RESEARCH_PLAN.md) — stages, methods, gates, and stop rules.
- [Experiment notes](research/EXPERIMENTS.md) — early test outline and run record template.
- [Tau test catalogue](research/TAU_TEST_MATRIX.md) — protocol, security, recovery, CPU, workload, and endurance cases.
- [Tau CPU integration](research/TAU_CPU_INTEGRATION.md) — B008 plan and modeled CPU results.
- [Core knowledge](research/CORE_KNOWLEDGE.md) — selected Analogue Pocket development knowledge.
- [Tau repository research](research/REPO_RESEARCH.md) — read-only findings from Tau Alpha.
- [Decision log](research/DECISIONS.md) — architecture choices, corrections, and rationale.

## Results

- [Results index](results/README.md) — suite summaries in the standard Goal → Method → Corrections → Result details order.
- [B004R2 physical results](results/B004_RESULTS.md) — stress and fresh-launch cold-read campaign.
- [B005 connected results](results/B005_CONNECTED_RESULTS.md) — completed recovery evidence and stopped-campaign limitations.
- [Chronological status](status/CURRENT_STATUS.md) — detailed build and hardware timeline.

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
