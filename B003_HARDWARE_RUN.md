# B003R2 — first automatic 32-case batch

Status: full compilation/internal timing qualified; installed package hashes verified, prior results preserved, safe card ejection is pending because macOS refused normal ejection. Eject successfully before removing the card. Physical batch and new JTAG endpoint pending. The active core identity remains `alfatreze.CARDWRITE02`; its build banner must read **SD WRITE RESEARCH B003R2**, version 0.3.2. Earlier minimal02 sources, SOF/RBF and package are archived, and its successful `write64.bin` is preserved.

## Write session: BATCH-003-WRITE

1. Insert CARDWRITE into Pocket and launch/resume the same research-core entry. Confirm the **B003R2** banner and **READY 32 CASES**. There is no new core entry to select.
2. Press **A once**. It runs 38 write/read pairs across 32 independent file regions. Wait for **BATCH PASS**, **BATCH FAIL** or **TIMEOUT STOPPED**. Success shows **PASSED 00000020**, **FINISHED 00000020** (hexadecimal 0x20 = 32).
3. Take one final screenshot, even on failure. Leave Pocket powered on at that result screen with the Terasic Blaster connected, and report readiness. The host reads the retained per-operation results over JTAG before Quit/reconfiguration discards them. Do not press A again, change core or reset while collecting.
4. After JTAG collection, Quit normally, shut down, remove and remount CARDWRITE on the computer. Record the physical actions used. The host verifies all 256 KiB against the independent oracle, including every guard byte and untouched tail, and compares protected files.

The screen establishes immediate comparison only. The final physical file establishes persistence of each final region. Earlier overwritten versions have retained immediate results but cannot all be verified from the final file.

For cable-controlled operation, leave the freshly launched core at READY and report readiness. `tools/jtag_batch.py status` confirms the endpoint/build, then `start` requests the same A-button batch. This needs no SOF programming and preserves the live results. `cold` requests the B-button batch on a fresh boot. A screenshot remains useful, but the retained per-operation records supply the detailed outcomes.

Output: `Assets/cardwrite/alfatreze.CARDWRITE02/batch-b003.bin`, exactly 262,144 bytes.
Expected successful final SHA-256: `f29a1a67f46db9181f251199cb9bab73c65df2ccd0d70621303d56f70ee9ca26`.

```sh
python3 tools/jtag_batch.py results
python3 tools/read_results.py batch03r2 --test-id BATCH-003-WRITE --firmware 2.7
```

## Cold read session: BATCH-003-COLD

After the physical file passes, eject and cold-launch the same B003R2 core. Press **B once**, without A. This reads and compares the 32 final payloads, including the preserved tails of shrinking overwrites. Expect PASSED/FINISHED 00000020 and BATCH PASS. Take a screenshot and retain the live JTAG results before Quit/shutdown/remount. Collect the physical file under `BATCH-003-COLD`.

## Cases and boundaries

The exact case catalogue is `experiments/b003.json`. Cases 0–27 are single writes; 28–29 perform three distinct overwrites; 30–31 perform a large write then a smaller overwrite. Five patterns cover zero, ones, alternating bits, ascending bytes and deterministic mixed bytes. Lengths range from 1 to 4,096 bytes; selected file offsets cross word/512-byte sector boundaries. Each case owns an 8,192-byte region in a preallocated file filled initially with 0xA5.

Configuration/JTAG case IDs are zero-based (0–31); the screen shows the human case number (1–32).

This first batch supplies representative coverage of W07/W08/W09 and part of W10, with S01 protected-file checks and S07 bounded initialized buffers from TAU_TEST_MATRIX.md. It does not complete those qualification rows: missing corpus sizes, allocation/cluster boundaries, stress, interruption, other cards/firmware, CPU and Tau workloads remain separate experiments. There is no file creation/resizing, NV shutdown writeback, explicit flush or arbitrary pathname operation in this batch.

Timeout latches ownership and stops the session. Command errors stop the affected case's further overwrite passes and retain its error; other cases continue. A comparison failure remains recorded even if a later overwrite reads correctly. A finished session cannot start another batch without reconfiguration. A fresh A run overwrites this scratch file intentionally; preserve its previous run first.
