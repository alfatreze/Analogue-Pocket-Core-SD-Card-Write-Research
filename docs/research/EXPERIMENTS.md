# Experiment plan

The staged research sequence and qualification rules are now defined in [RESEARCH_PLAN.md](RESEARCH_PLAN.md), with detailed conditional cases in [TAU_TEST_MATRIX.md](TAU_TEST_MATRIX.md). The short A–E outline below is the initial planning record; use the newer plan's official control → minimal FSM → VexRiscv → Tau workload order.

## Setup record required for every run

| Field | Record |
|---|---|
| Test ID/date | |
| Pocket firmware (Settings > About) | |
| Framework requirement / core version | |
| Core name, build ID and `.rbf_r` SHA-256 | |
| Card identity and format | |
| Slot position, ID, flags, declared size | |
| Write mechanism under test | APF shutdown / target `0x0184` / target `0x0188` |
| Payload pattern, expected bytes and checksum | |
| Exact user/core actions and timing | |
| Result code / log evidence | |
| File path, size, readback bytes/hash | |
| Quit and relaunch result | |
| Conclusion and confidence | |

## Staged experiments

### A. Baseline APF nonvolatile writeback

Use one small fixed-size nonvolatile slot and a disposable card. Start with a known existing file if practical. Write a distinctive test pattern into save memory, ensure the data-slot size table entry for the slot's array position is nonzero and correct, then use the Pocket's normal Quit path. Check exact file size and full contents after remount; relaunch and confirm the bytes load back.

This isolates the documented APF shutdown path from target writes.

### B. First-file creation behavior

On a fresh test namespace with no save file, compare separate runs with and without `parameters` bit 5. Record whether the slot was loaded, whether a file is created, its initial bytes, and whether a later change survives Quit/relaunch. This tests community-reported KB-074.

### C. Target `0x0184` write/readback

Use a dedicated deferload test slot and invoke one bounded write with a pattern that includes unique words at offset zero, a middle offset, and the final bytes. Record the command result and inspect the created/updated file after safe eject/remount. Repeat at small sizes before testing truncation boundaries. Do not concurrently rely on APF shutdown writeback.

### D. Repeatability and interruption

After one path succeeds, repeat identical writes across multiple clean boots. Then vary only one interruption boundary at a time (menu entry, normal Quit, sleep if relevant). Do not pull power/card during the initial characterization. Interruption tests belong on a disposable card and must check whether files are old, new, partial, or absent.

### E. Target `0x0188` flush (optional)

Only after `0x0184` or the baseline path is understood, implement/enable a custom flush command path and test it in isolation. Capture request/response/timing and verify bytes from the card. Treat result code zero without readback as inconclusive.

## Result template

### TEST-ID — short title

- **Setup:** firmware, framework, core build/hash, card, slot definition.
- **Hypothesis:** one claim being tested.
- **Procedure:** exact actions and expected stopping points.
- **Expected:** expected path, size, pattern/hash, and reload behavior.
- **Observed:** command/log result plus actual file observations.
- **Evidence:** photo/log/file hashes and where retained.
- **Verdict:** pass / fail / inconclusive, evidence grade, scope.
- **Next run:** one change only.
