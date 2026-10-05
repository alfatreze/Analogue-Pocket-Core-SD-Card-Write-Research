# B004R2 — changing-data repeatability stress

Status: **B004R2's first physical 10,000-pair session passes**, with all 10,000 retained records independently validated: 20,000 commands, zero failures, correct indexed byte ranges/flags and matching timing extrema. The live SDW4 511-bit interface/revision 2 is verified. Full history is preserved in `work/evidence/b004r2-physical-jtag-write-records.json.gz`; summary/hashes are in `work/evidence/b004r2-physical-jtag-write.json`. Writes range 11.298–126.546 ms; reads 6.076–21.889 ms at 74.25 MHz. After owner remount, the complete 256 KiB file matches the expected SHA-256 and all guard bytes; no protected files changed. Screenshot agrees with the retained history. See `work/evidence/b004r2-physical-file-write.json`. Exact Quit/power sequence was not separately confirmed. The first fresh-launch cold session also passes all 32 final regions: 32 reads, zero writes/failures, full retained history validated in `work/evidence/b004r2-physical-jtag-cold.json`. Post-cold remount also passes: entire file/guards unchanged, every prior file unchanged, only the new PASS screenshot added. See `work/evidence/b004r2-physical-file-cold.json`. A separate second fresh-launch read-only session also passes all 32 regions (cold-repeat01); its post-read remount confirms the entire file/guards and every prior file remain unchanged. See `work/evidence/b004r2-physical-file-cold-repeat01.json`. Full power-off actions are not separately confirmed, so repeated owner-confirmed power-cycle qualification remains pending.

B004R2 is compiled/internal-timing qualified and installed in the stable CARDWRITE02 entry, version 0.4.2. All 11 package hashes verified; qualified B003R2 artifacts and prior physical outputs preserved. Earlier failed/stopped stages remain archived.

## Scope

One fresh A/JTAG-start session performs **10,000 write/read pairs (20,000 commands)** against a new preallocated 256 KiB `stress-b004.bin` in slot 0x24. The stable menu entry remains `alfatreze.CARDWRITE02`; B004 displays **SD WRITE RESEARCH B004R2**, metadata version 0.4.2.

Operations visit 32 independent 8 KiB regions in round-robin order. Sizes range from 1 to 4,096 bytes, with aligned and misaligned/cross-sector offsets inherited from the verified B003 catalogue. Each visit changes the data within its region. The five base pattern families are mixed with the visit number; the single-byte case necessarily repeats eventually, but adjacent visits always differ. Configuration is `experiments/b004.json`; `tools/stress.py` is the independent complete-file oracle. No shrinking overwrite is added here: B003 already covers that separately.

All 10,000 operations retain flags, write cycles and read cycles in dedicated FPGA RAM. First failure and total failures stay latched despite subsequent successes. Global minimum/maximum command cycles provide the timing summary. Timeout stops the owner permanently until reconfiguration; late completion, buttons and host reset cannot retry a live request. Ordinary command/comparison failures are recorded and the next independent operation proceeds. JTAG can read progress snapshots while busy; indexed logs are exposed only after completion/timeout.

The final file proves only the last durable payload in each region. Earlier generations have immediate comparison records; **10,000 immediate pairs are not 10,000 independently proven durable commits**. Interrupted-write atomicity and recovery are later experiments. No file creation/resizing, flush, NV writeback, arbitrary path, CPU or external RAM is introduced.

## Host preparation

Before the stable entry is changed, qualify full Quartus compile, RAM inference and all timing corners. Archive verified B003R2 sources/package/SOF/RBF/reports; back up current core files, caches and both physical output files. `tools/update_stress.py` requires exact installed B003R2 hashes, qualified B004 package hashes, matching designated-card UUID, and unchanged prior physical outputs against BATCH-003-COLD. It refuses existing B004 scratch files. Review its generated plan; existing chat authorization covers this bounded update.

Expected final file SHA-256 after success:
`0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56`.

## STRESS-004-WRITE

1. Safely eject CARDWRITE, insert it into Pocket, fresh-launch the same menu entry, confirm **B004R2 / READY 10000 PAIRS**, leave Blaster connected and report loaded. Do not press A while a JTAG start is planned.
2. Host validates live SDW4 signature/revision and READY with zero counters, then requests start. Alternatively press A once. Do not reset/reconfigure/quit during the run.
3. Wait for STRESS PASS / FAIL or TIMEOUT STOPPED. Successful screen PASSED/FINISHED is hex **00002710 = 10,000**. Capture a screenshot.
4. **Collect retained JTAG records before Quit**. Reading all 10,000 snapshots can take several minutes. Keep Pocket powered on. `python3 tools/jtag_stress.py results` preserves raw and decoded records; success requires all 10,000 distinct indexed records, exact expected flags/bounds, 20,000 commands, no failures and consistent timing summaries.
5. Normal Quit, shutdown, remount. `python3 tools/read_results.py stress04r2 --test-id STRESS-004-WRITE --firmware 2.7` verifies every byte/guard and protected files. Preserve the physical actions, screenshot and full result history.

## STRESS-004-COLD and repeated launch cycles

After the physical file passes, safely eject and fresh-launch B004 without A. Host `cold` (or B once) reads the **32 final region generations**. It issues exactly 32 reads and zero writes; final PASSED/FINISHED is **00000020 = 32**. JTAG selects each region's final operation index, which is not simply the last 32 indices in ascending case order.

Collect JTAG, screenshot, normal Quit/shutdown/remount and full file/protected-content verification under STRESS-004-COLD. Repeat fresh-launch read-only sessions under separate IDs (initial target 10 owner-confirmed shutdown cycles). Preserve every cycle's results; never silently replace earlier evidence. This supplies initial repeated read/reload coverage, not the research plan's later 1,000-cycle qualification.

## SDW4 snapshot

Source width 32, probe width 511, no FPGA programming. The 16-word logical packet is padded to 512 bits on the host; its omitted most significant signature bit is constant zero. Source bits 31 snapshot toggle, 30 stress start, 29 cold start, 13:0 selected zero-based operation. Hold index before snapshot toggle. All other source bits unused.

16 MSB-first words: signature 0x53445704; header; selected operation; completed; passed; failed; command count; region file offset; length; flags; write cycles; read cycles; min write cycles; max write cycles; min read cycles; max read cycles. Header: ack31, cold30, terminal29, reserved28:26, revision25:18 (=2), status17:14, first failure13:0 (16383 means none). Clean flags: warm 0x80000007 / cold 0x80000006; timeout bit15 with bit12 write or bit13 read. Cold write timing is zero and min-write sentinel 0xffffffff.

Fresh launch alone does not prove a particular power-off sequence: record owner actions separately. Runtime firmware 2.7 is known from prior runtime metadata; verify About if changing firmware.

The LCD CYCLES field is the held inclusive FSM counter. Completed JTAG command timings are captured at DONE before the final counter increment; the LCD final value is one clock greater than the final retained read timing. Compare extrema against retained records, as the regression does.

## Repeat02 current result

Third fresh-launch read-only session passes all 32 regions, zero writes/failures; full history is `work/evidence/b004r2-physical-jtag-cold-repeat02.json`. Post-read remount also passes: complete file/guards and all prior files unchanged; only the new PASS screenshot added. See `work/evidence/b004r2-physical-file-cold-repeat02.json`. Exact full power-off actions have not been separately confirmed.

## Repeat03 current result

Fourth fresh-launch read-only session passes all 32 final regions, zero writes/failures; full history is `work/evidence/b004r2-physical-jtag-cold-repeat03.json`. Post-read remount/whole-file comparison pending; exact power-off action not separately confirmed.
