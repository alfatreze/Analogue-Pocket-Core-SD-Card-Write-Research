# B005 connected results — stopped by JTAG connection failure

2026-10-05, designated single CARDWRITE card, B005/0.5.0. The connected campaign stopped at 18:08 WEST when System Console could not open SDW5. The Blaster remained visible to the VM, but repeated chain reads reported “JTAG chain broken”. No automatic retry/reconfiguration or B006 loading followed this failure.

## Completed storage evidence

The independent replay rechecked all 40 completed events against retained raw/decoded packets, record order/destinations/CRCs, counter/mask/generation fields and 39 programming journals. The first separately preserved 64-save batch is included in the save total.

| Observed quantity | Result |
| --- | --- |
| Clean batches | Ten batches of 64: 640 verified commits |
| Single-save resume controls | Seven verified commits |
| Total committed saves | **647** |
| Read-only recovery sessions | 17, each two reads and zero writes |
| Between-command FPGA interruptions | Seven recoveries pass: all four points once, then points 0/1/2 again |
| Counted SD commands, including partial-prefix sessions | 3,326 |
| Newest selected generation | 647 |
| Planned point 3 second repetition and final repair | Not run |
| Entire planned campaign | **Incomplete; transport failure preserved** |

Every completed storage session passes its declared immediate readback/recovery oracle. This is not zero-failure completion of the planned campaign: the JTAG transport failure is retained separately. No SD power cuts or full Pocket power cycles were confirmed in this connected campaign.

Retained per-save cycle totals (four writes plus verification read; excludes boot/reloads/tooling): minimum 2,318,935, median 3,785,550, maximum 18,699,600 cycles. At nominal 74.25 MHz these are approximately 31.23 / 50.98 / 251.85 ms. These correlated single-card observations are not a universal timing bound or failure-rate estimate.

## Current model and preservation rule

The last completed read-only session selects A generation 647 with valid mask 1. The independent model predicts B's header generation 648 but an invalid CRC, because its first 256 bytes were replaced at the deliberate interruption point while the remaining record bytes stayed old. Both fixed-region guards are predicted intact; actual host-read sizes/bytes/guards and all protected content remain pending.

Expected full-file SHA-256 values:

- A: 41b5b767f85a832b63f0888914382dfa824dc313c762ab9c6ebe58458fd7b51b
- B: ff5c586c43076beb0d7893088147d1a15a3f73b5afac102564b9d50e096ba495

These are software-model hashes, not a host-remount result. Preserve both raw physical files before any repair when the card becomes available. `tools/read_connected_results.py --build B005 --allow-stopped --test-id STOPPED-005-FINAL --firmware 2.7` captures and compares the stopped prefix without qualifying the incomplete campaign. Firmware is explicitly owner-reported. Eleven temporary-card collector tests pass; a stopped forensic capture cannot satisfy the B006 installation gate.

If connection returns first, capture status with `tools/jtag_session.py --build B005 status`. Require the restored exact single cable/device and either a live terminal snapshot matching the preserved generation-647 result or a separately explained fresh load followed only by read-only recovery. Preserve the failed checkpoint/continuation; create new resume evidence instead of rewriting them. Do not start a new blanket campaign or initialize/reset the files.

## Tooling findings

The old client closed SSH while leaving remote console processes alive. The VM held 165 orphan consoles and had about 108 MiB available RAM with all 2 GiB swap occupied. Exact PID/start/command identities and uniquely paired B005 captures identified 131 research clients (capture lag 27.7–36.8 seconds). Scoped cleanup closed those 131 clients; a separate observation verified none remained. About 9 GiB RAM became available, but the FPGA chain still could not be read. Memory exhaustion and the unreadable chain are both observed; cleanup did not establish the chain failure's cause.

A first shutdown trial established that this SDK rejects Tcl `exit`. The separate new console client records its remote PID/start ticks, waits for script completion markers and then closes only that verified process. Both harmless VM success/error trials pass; nine host signature/lifetime/error tests and twelve reload/load safety fixtures pass. These client tests issue no SD commands or FPGA programming. ISSP access through the new client remains pending connection restoration. Original qualified Tcl/decoder/tool sources and frozen FPGA stages remain unchanged.

The independent replay initially omitted saved transport metadata when comparing public events. Its schema fixture was corrected to retain exit/script fields, and a missing-metadata refusal test was added; five verifier tests and the complete stopped-prefix replay now pass. The initial harness failure log is preserved. This was an audit-tool mismatch, not a newly observed storage mismatch.

## Evidence

work/evidence/b005-connected-campaign.json/.log retain the actual stopped campaign. b005-connected-stopped-summary.json and b005-stopped-verification.log record the independent replay and explicitly keep campaign completion false. Original raw console/programming/predicted-file evidence stays private under work/evidence/jtag. b006-continuation.json records failure before loading B006. research-console-cleanup.json and console-session/loader qualification records preserve the tooling recovery.

- Publication privacy: automatic approval review rejected publishing the broad raw diagnostic set because it exposed local/VM paths. Originals and their hashes remain unchanged in private local archives. Public b005-connected-public-summary.json and console-transport-public-tests.json retain outcomes/hashes with tracebacks and process identifiers omitted. Qualification and replay tools continue to use the exact private originals; a public clone alone does not contain the physical raw history.
