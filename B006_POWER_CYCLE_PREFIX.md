# B006 full Pocket power-cycle after a saved partial record

## Purpose

Test whether B006 can recover the last complete save after a full Pocket shutdown when the inactive 512-byte record already contains a persisted 128-byte prefix of the next record. The FPGA will be held at a verified pause point with no APF command outstanding before power-off.

This is a deterministic partial-record plus full-device-power-cycle test. It does **not** remove SD power while a target write command is active. Active-command power interruption remains a separate qualification target requiring a safely timed power control method.

## Frozen baseline and expected result

Baseline is the verified post-install B006 host remount at generation 1038. `tools/prepare_power_cycle_prefix.py` derives the exact expected files from the preserved full-file baseline. Pause point 1 means exactly one successful 128-byte chunk is written to inactive A for generation 1039. Expected final hashes:

- A (partial generation 1039 prefix): `53e9757a53df7bfcbb92903008348001e41abc09c98bb34ed68b7547e0a9c6b6`
- B (unchanged valid generation 1038): `a5d03367ba5cabbff739c229030bb28e0ebafe2e9f0c24b335f1334ac375a3dd`

Recovery after reboot must report only B valid and select generation 1038. The untouched baseline copies and modeled final files are retained under ignored `work/evidence/runs/B006-POWER-CYCLE-PREFIX1-001/`.

## Procedure

1. Insert CARDWRITE and load the existing `alfatreze.CARDWRITE02` B006 / 0.6.0 core. Do not mount CARDWRITE on the host during the Pocket run.
2. Read a fresh status with `python3 tools/jtag_session.py --build B006 status`; continue only with zero commands and READY state.
3. Run `python3 tools/jtag_session.py --build B006 pause --point 1` once. Then run status and independently decode the captured packet. Require PAUSED state 14, status 8, selected generation 1038, completed saves 0 and command count 3 (two boot reads plus one 128-byte write). Stop on any mismatch.
4. With the verified PAUSED state, fully power off the Pocket. This leaves the completed prefix on CARDWRITE and confirms no command is outstanding at shutdown.
5. Power on, load the same B006 core from SD, then run `python3 tools/jtag_session.py --build B006 cold` and `python3 tools/jtag_session.py --build B006 results`. Require a read-only PASS, valid mask 2, selected generation 1038 and no command errors.
6. Quit the core, fully power off, and mount CARDWRITE on the host. Compare both complete 8 KiB files against `work/evidence/runs/B006-POWER-CYCLE-PREFIX1-001/expected-{a,b}.bin`, verify all guards and unchanged protected files, and record any new files. Preserve raw physical evidence before any further SD operation.

The preparation report is `work/evidence/b006-power-cycle-prefix-preparation.json`. Actual success requires both post-reboot B006 recovery and exact host-remount bytes. A JTAG reload alone does not count as a Pocket power cycle.
