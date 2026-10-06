# Overall feasibility and progress

Updated 2026-10-06. [Main README](../../README.md) · [Individual results](../results/README.md)

## Current feasibility decision

**Feasible for bounded CPU-free updates to preallocated files on the tested setup. Full Tau qualification is pending.**

Exact physical bytes survived the verified write/remount and fresh-launch checks. Alternating records retained valid previous state at tested between-command interruption points. Active overwrites produced mixed bytes in three monitored trials; selected cold-read checks refused those torn images. Host comparisons found no unexpected protected-file changes within the audited runs.

Evidence covers one Pocket, the designated exFAT CARDWRITE card, and the recorded firmware setup (reported 2.7). Full qualification of active-power-loss recovery for the A/B save format, physical CPU persistence, playback budgets, and wider environments remains pending.

## Progress: 60/100

This is a **weighted discovery-milestone tally introduced for reporting**, not an empirical reliability measure, percentage of elapsed effort, or count of all planned test cases. The weights allocate 60 points to establishing the CPU-free foundation and 40 to proving suitability in Tau and broader conditions. A milestone earns its weight when its declared initial discovery scope is evidenced; extended qualification can remain pending. Existing simulation prototypes do not earn physical CPU-integration points.

| Discovery milestone | Available points | Earned | Evidence / remaining gate |
|---|---:|---:|---|
| Reproducible fixtures, observability, audit and protected-file checks | 10 | 10 | Pinned builds, deterministic host oracle, JTAG and remount records. |
| Exact minimal write and fresh-launch readback | 10 | 10 | [FSM-002](../results/FSM002_RESULTS.md), [B003](../results/B003_RESULTS.md). |
| Sustained updates and repeat cold reads | 15 | 15 | [B004](../results/B004_RESULTS.md): 10,000 pairs and ten fresh-launch sessions. |
| Guarded records and between-command recovery | 15 | 15 | [B005](../results/B005_CONNECTED_RESULTS.md), [B006](../results/B006_RESULTS.md); limited interruption scope. |
| Active-write interruption characterization and torn-data refusal | 10 | 10 | [B007](../results/B007_RESULTS.md); tearing observed, selected refusal checks pass. |
| Exact CPU-to-engine integration and physical persistence | 15 | 0 | B008 simulation gate, fit/timing, and Pocket/remount evidence pending. |
| Tau functional/memory/workload suitability | 15 | 0 | Settings, migration, playback and actual buffer/latency budgets pending. |
| Environment and endurance qualification | 10 | 0 | Declared card/firmware/filesystem and repeated lifecycle/interruption matrix pending. |
| **Total** | **100** | **60** | **Five initial discovery milestones evidenced; three remaining.** |

## Capability status

| Capability | Evidence status | Practical limit |
|---|---|---|
| Bounded existing-file writes | Demonstrated on hardware | CPU-free, serialized, preallocated outputs on this setup. |
| Fresh-launch/power-cycle persistence | Demonstrated at recorded boundaries | Many early fresh launches lack separately confirmed full power-off; later controls explicitly include it. |
| Previous-valid-record recovery | Demonstrated at tested between-command boundaries | Active-power-loss A/B recovery remains unqualified. |
| Atomic overwrite | Not supported by observed trials | Three live cuts left mixed old/new bytes. |
| Torn-data detection/refusal | Demonstrated on selected B007 cold reads | CUT1, CUT3, and separate unmonitored shutdown; not a per-cut claim for CUT2/CUT4. |
| Protection of unrelated files | Passed retained host comparisons | Full destination/invalid-input security catalogue not completed. |
| Exact Tau CPU writes | Modeled prototypes only | Physical persistence and production ownership/reset/CDC pending. |
| Saving during playback | Pending | No measured Tau FIFO/latency qualification yet. |
| Create/resize, NV shutdown, explicit flush | Not qualified by these campaigns | Preallocated target writes are the established baseline. |
| Authentication/encryption | Not implemented/qualified | CRC and guard checks detect accidental damage; they do not authenticate data. |
| General card/firmware reliability | Pending | Single-card evidence cannot establish the broader matrix. |

## Next gate

B008 first joins the pinned generated CPU to the proven B007 engine in an isolated dual-clock simulation. Only after ownership/reset/CDC cases pass should a new frozen FPGA build be fitted and tested for exact Pocket/host persistence. See [B008 plan](TAU_CPU_INTEGRATION.md#b008-first-implementation-gate). Further active-cut qualification of the intended A/B format must remain explicit before any stronger power-loss-safety claim.
