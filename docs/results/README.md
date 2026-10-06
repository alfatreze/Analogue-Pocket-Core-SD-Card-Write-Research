# Results index

[Overall feasibility: 60/100 discovery progress](../research/FEASIBILITY_STATUS.md) · [Main roadmap](../../README.md)

Each suite has an individual report. Every report begins with **Goal → Method → Corrections → Result details**, and each recorded case repeats those four fields. Evidence links and limitations finish the result details. Historical records retain earlier pending states and are identified as archives; current conclusions live in the individual reports.

| Suite | Outcome | Individual report |
|---|---|---|
| Official control | Preparation verified; functional execution pending. | [Control](CONTROL_RESULTS.md) |
| FSM-001 | Failed intended-record verification. | [Initial minimal writer](FSM001_RESULTS.md) |
| FSM-002 | Corrected write/remount and fresh-launch read passed; wrong-build attempt inconclusive. | [Corrected minimal writer](FSM002_RESULTS.md) |
| B003R2 | 32 cases, 38 warm pairs, 32 cold reads; host checks passed. | [Batch baseline](B003_RESULTS.md) |
| B004R2 | 10,000 pairs, 320 cold reads, eleven host checks passed. | [Stress/cold-read campaign](B004_RESULTS.md) |
| B005 | Original stopped prefix preserved; separate resumed trial completed. | [Alternating-record recovery](B005_CONNECTED_RESULTS.md) |
| B006 | Guard/adversarial checks, connected saves, and tested power-cycle boundary passed. | [Guarded recovery](B006_RESULTS.md) |
| B007R3/R4/R5 fit | R3/R4 failed; R5 RAM-backed coverage passed fit/internal timing. | [Fit and corrections](B007_FIT_RESULTS.md) |
| B007R5 interruption | Three active cuts tore data; selected refusal checks and controls passed. | [Active-write study](B007_RESULTS.md) |
| B008 CPU/engine integration | 15 actual-CPU trials and directed mailbox checks passed in simulation; hardware pending. | [B008 first gate](B008_RESULTS.md) |
| Tau CPU prototypes | Simulated profiles passed with retained reset/completeness limitations. | [CPU simulations](CPU_SIM_RESULTS.md) |

[Report template](TEMPLATE.md) · [Chronological evidence](../status/CURRENT_STATUS.md) · [B004 archived report](../status/archive/B004_CAMPAIGN_RECORD.md) · [B005 archived report](../status/archive/B005_CAMPAIGN_RECORD.md)

A command completion, same-session readback, or simulation does not establish physical persistence by itself. Hardware claims require the stated cold/restart evidence and independent host whole-file checks. FPGA reload, between-command Pocket power cycle, and loss of power during a live SD command are separate conditions.
