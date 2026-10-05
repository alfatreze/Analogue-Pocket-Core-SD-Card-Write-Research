# Card-writing lab status

## 2026-10-04 — first implementation

- Official example and template cloned into this project's vendor folder and pinned by commit plus file hashes. No sibling Tau repository was changed.
- Official reference package assembled from unchanged JSON/assets/upstream prebuilt RBF. The upstream prebuilt image is a control, not a newly timing-qualified custom build.
- Official control installed on the user-designated CARDWRITE volume. All 13 package files hash-verified; pre-existing non-OS files hash-identical after install. Evidence: `work/evidence/install-official-control/{volume,plan,before,after,journal}.json`.
- Card baseline: removable exFAT, 128 KiB allocation blocks, volume UUID recorded in FIRST_HARDWARE_RUN.md. Installed Pocket firmware still pending.
- Independent host verifier supports the 64-byte NCW1 record and the reference's first image. It rejects wrong bytes/length/generation/word byte order and cannot generate fixtures outside this project's work folder.
- Minimal CPU-free core implemented: dedicated slot ID 0x22, fixed 64-byte write, separate BRAM payload/readback, poisoning/received mask, genuine completion handling, and a frozen fault state after timeout.
- `make test` passes: real-template command integration under simulation models, generation 1/2 compared with the independent host byte oracle, stale DONE, corrupted/missing readback, result errors, and outstanding-command ownership across timeout/reset. Five host checks pass. Top-level compiles under Icarus. Template's pre-existing 10-bit-to-8-bit table-port truncation warnings remain.
- Eight diagnostic states captured from actual `lab_video` RTL at native 320x240 and visually inspected. Telemetry inputs are deterministic fixtures; this verifies the renderer, not Pocket display characteristics. Files: `work/sim/frame-0.png` through `frame-7.png`.
- Isolated Quartus 25.1std seed-1 full compile completed with 0 errors and 162 warnings. Uses 2,544/18,480 ALMs (14%), 2,214 registers, 6 RAM blocks and 1 PLL. Worst setup slack +3.714 ns; worst hold +0.126 ns. All reported timing corners pass. Reports and bitstream collected and hashed. External bridge/scaler I/O delays remain unconstrained in the template; no unconstrained clocks. This is internal timing qualification, not end-to-end Pocket interface qualification. See BUILD_AUDIT.md.

Next gate: perform CONTROL-001 / FSM-001 on Pocket, preserve physical output files, and test cold persistence. Follow FIRST_HARDWARE_RUN.md. No new Pocket-originated SD-write success has been claimed.

- Custom CARDWRITE01 installed: all 11 package files hash-verified; every pre-existing protected file unchanged. Installation journal completed. CARDWRITE safely ejected after both installs.


## FSM-001 — first Pocket observation

- Pocket-generated device metadata reports runtime firmware 2.7, byte 39, build date 2026-09-04. Settings > About confirmation pending.
- User supplied screenshots `20261004_234302.png` and `20261004_234310.png`: WRITE CMD OK then READ DIFF; completion counts 1 then 2, error 0. Both show expected generation 0 rather than the source's initial 1. Read generation is 0x00010001 (the record test ID, shifted into the generation position).
- Remounted physical `write64.bin` is 64 bytes and changed from its installed zero fixture. SHA-256: `40e733d070f38a15467d752210fa4a84ca83d31e1d85e465362c68630276879c`. Independent generation-1 verifier FAILS.
- Exact diagnostic match: generation-zero record with its first 4 bytes removed and a zero word appended. This is a diagnostic classification, not an accepted format or revised oracle.
- All pre-existing protected files hash-identical. New Pocket settings/catalog files and the two screenshots listed for review.
- Evidence preserved locally under `work/evidence/runs/FSM-001/`; raw inventories and screenshots remain excluded from Git.
- Verdict: intended-record write/read test FAILED. Changed bytes reached the remounted card; no repeatability, cold reload, crash safety or Tau suitability demonstrated. Exact Quit/shutdown sequence awaits user confirmation.

Next experiment: correct and qualify the probe's APF read-response timing, investigate deterministic generation initialization, then repeat with a fresh build ID. Preserve minimal01 and its failure evidence unchanged. Existing direct-bus simulation did not exercise the real SPI peripheral or hardware power-up behavior.


## CARDWRITE02 preparation

- Old one-word shift reproduced with actual pinned APF serial state machines (Icarus syntax adaptation). Corrected response and 16-word serial RX/readback pass; direct command/error/timeout tests and six host tests pass.
- Clocked startup establishes generation 1; underlying minimal01 power-up discrepancy remains unproven.
- Eight new native 320x240 RTL status captures inspected under `work/sim/minimal02/`.
- Separate minimal02 seed-1 Quartus full compile PASSED: 0 errors, 162 warnings; worst setup +4.169 ns, hold +0.150 ns, 15% ALMs. Artifacts collected and package qualified for Pocket trial; external interface margins remain unqualified. See BUILD_AUDIT.md.
- Next physical run: NEXT_HARDWARE_RUN.md, core CARDWRITE02 and new output file.

- CARDWRITE02 installed on designated CARDWRITE: all 11 package files hash-verified; protected pre-existing contents unchanged, including CARDWRITE01's failed output and the supplied screenshots. Five known catalogue caches backed up then cleared. Installation journal completed.
- Terasic JTAG chain verified after user enabled passthrough: USB-Blaster [5-3], 02B050DD. No programming performed; Tau Alpha consulted read-only.
- Automatic multi-case batch and stable JTAG result access planned in BATCH_TEST_PLAN.md/JTAG_WORKFLOW.md; not implemented in CARDWRITE02.
- CARDWRITE safely ejected after CARDWRITE02 installation. Ready for FSM-002.


## FSM-002 attempt — original core resumed/selected

New screenshots `20261005_002904.png` and `20261005_002910.png` show CARD WRITING LAB 01, WRITE CMD OK then READ DIFF, generation 0. Pocket's System/lastcore.bin names CARDWRITE01. CARDWRITE02's output remains the installed 64-byte zero fixture, and all its installed package hashes match the qualified package. No protected baseline file changed. This attempt supplies no CARDWRITE02 hardware verdict; preserve it as wrong-build evidence rather than interpreting it as failure of the corrected transport. Screenshots and collector output preserved locally under `work/evidence/runs/FSM-002/`. Next run is FSM-002-R1, explicitly selecting CARDWRITE02 through Tools > Developer > Builds and checking the LAB 02 banner before pressing buttons.


## FSM-002-R1 — first correct physical record PASS

- Screenshots `20261005_003514.png` and `20261005_003518.png` show LAB 02, WRITE CMD OK then READ MATCH, expected/read generation 1, completion counts 1/2, error 0. Startup-only screenshot was not supplied.
- Remounted physical `write64.bin` is exactly the expected 64-byte generation-1 record. SHA-256 `b7b05ccadcfa2eb7ed53aee6b5b12db57a06217da1351728a82810ad757f393c`. Independent full-byte verifier PASS.
- The conservative collector returned overall inconclusive because System/lastcore.bin and System/recent.bin changed. Both now identify CARDWRITE02, consistent with the deliberate core selection. Their raw changes remain retained and explicitly reviewed in local review.json; no other protected baseline files changed. Do not silently discard metadata differences.
- Local immutable evidence: `work/evidence/runs/FSM-002-R1/`, including raw output, screenshots, snapshots, original collector result and review.
- Verdict: one correct physical existing-file update and immediate readback on firmware 2.7/designated card. Cold reload, repeatability and interrupted-write safety remain pending; exact Quit/shutdown actions not separately confirmed.
- Next gate: cold-launch CARDWRITE02 and press B only; expect READ MATCH generation 1. Batch implementation can now use the repaired transport, while cold persistence still needs its separate observation.

## FSM-002-COLD — reload readback PASS

- Screenshot `20261005_003824.png` shows LAB 02, READ MATCH, expected/read generation 1, completion 1, error 0, cycles 0x00073399. This is consistent with the requested fresh-launch B-only read.
- Remounted physical output still matches all 64 expected bytes; SHA-256 `b7b05ccadcfa2eb7ed53aee6b5b12db57a06217da1351728a82810ad757f393c`.
- Compared with the prior FSM-002-R1 snapshot, no existing protected file changed or disappeared. The sole added file is the new screenshot. The conservative original collector still reports the previously reviewed core-selection metadata changes against its older installation baseline; its output is retained unchanged.
- Immutable local evidence is under `work/evidence/runs/FSM-002-COLD/`, with screenshot, physical output, inventory, original collector result and separate review.
- Verdict: reload readback and physical bytes PASS. Exact cold power-off sequence is not separately confirmed; one observation does not establish repeatability or interrupted-write safety.
- Next implementation: uniquely numbered B003 automatic multi-case batch, updating the stable active core entry with verified backups. Preserve the successful minimal02 artifacts and output.

## B003 implementation and compile attempts

- Automatic 32-case CPU-free batch implemented, with 38 write/read pairs, disjoint guarded regions, shrinking overwrites, cold read mode and retained per-operation ISSP results. Exact catalogue: experiments/b003.json. No physical batch result yet.
- Initial batch03 synthesis failed when bundled Java JIT crashed during JTAG fabric generation. Failed stage/log retained; Java interpreter mode scoped to the research build fixes that generator.
- B003R1 synthesis resource review found TX/result memories mapped to registers: 30,203 estimated ALMs against 18,480 available, 43,065 registers. Stopped only that isolated compile after retaining partial reports. This was not a full fit/timing verdict.
- B003R2 introduces dedicated synchronous RAM read registers ahead of the validity/response-hold muxes. Real pinned APF serial simulation still matches every requested payload byte and the whole guarded file; command-interface and cold/fault tests pass. Existing minimal02 regression also passes. New frozen B003R2 stage is compiling; timing and physical JTAG/batch qualification remain pending.
- The audited updater and Tcl helper are tested against temporary fake card trees and a mocked ISSP service. Neither supplies physical JTAG/SD evidence. CARDWRITE remains on the working minimal02 build until qualification succeeds.

## B003R2 qualified and installed — physical batch pending

- Full compile completed with 0 errors / 169 warnings. Uses 2,829 ALMs (15%), 2,859 registers, 83,181 block-memory bits, 15 RAM blocks, 9 DSP blocks and 1 PLL. All five intended arrays infer RAM. Worst setup +2.545 ns, hold +0.075 ns; every reported corner TNS 0. No unconstrained clocks. External I/O delays remain incomplete (6 inputs / 23 outputs, including JTAG). See BUILD_AUDIT.md for scope and hashes.
- Qualified SD bitstream SHA-256 `4944d570b7f97caf3b2d72b4c5c7f63532c5f819e1d675f567d1cbb14c7a552e`. Version 0.3.2, banner B003R2, same `alfatreze.CARDWRITE02` entry.
- Audited update completed on the designated CARDWRITE volume. All 11 package files independently hash-verified after installation. Only planned core files/new scratch/cache refresh changed; all unrelated protected contents unchanged. Earlier successful write64.bin remains SHA-256 `b7b05ccadcfa2eb7ed53aee6b5b12db57a06217da1351728a82810ad757f393c`.
- Prior qualified sources, metadata, SOF/RBF and package archived under local `work/archives/minimal02-before-b003/`, with a verified manifest. Old active-core files, five catalogue caches and physical write64.bin backed up under local `work/evidence/update-batch03/backup/`. Plan, before/after snapshots, journal and final review retained privately.
- CARDWRITE update is verified; normal ejection was refused twice and normal volume unmount also failed by macOS loginwindow (PID 171), with no matching ordinary open-file handle found by the scoped inspection. No force or process termination used. Safe removal remains pending. No JTAG programming performed; physical SDW3/batch/cold-read results remain pending.
- Next owner action: successfully eject CARDWRITE in Finder, then insert it into Pocket, cold-launch/resume the same core, confirm B003R2 and leave it at READY with the Blaster connected. The host can then confirm the live endpoint, start the batch and collect its retained results before Quit/shutdown/remount. B003_HARDWARE_RUN.md also gives the A-button route.

## BATCH-003-WRITE — physical immediate batch PASS

- Owner reports B003R2 loaded. Host-mounted CARDWRITE absent. Live SDW3 signature/revision confirmed READY with no previous commands; JTAG start requested the batch without FPGA programming.
- Physical retained terminal summary: status 4, warm mode, 32 completed, 32 passed, 0 failed, 76 commands. All 38 indexed write/read records independently decoded with expected case, ordinal, offset, lengths and exact clean flags 0x80000007. Includes repeated and shrinking overwrites. Public structured evidence: work/evidence/b003r2-physical-jtag-write.json; full original console captures retained privately in work/evidence/jtag/.
- System Console invocation required an actual hardware correction: --script with closed stdin returned banner/exit 0 without executing the script. Holding interactive stdin and explicitly sourcing the absolute script executes it; the console has no Tcl exit command. The host now waits for completion markers, captures stderr, and requires an actual validated summary/request. Four Tcl mock tests still pass. Frozen FPGA sources and installed package are unchanged.
- Verdict: physical immediate payload comparisons PASS for one batch, with live JTAG endpoint/retained records now demonstrated. Whole-card final bytes, guard integrity, protected files, persistence after normal Quit/shutdown and cold read remain pending; no repeatability or interruption guarantee inferred.
- Next owner action: capture final screenshot, Quit normally, shut down, then remount CARDWRITE so the host can verify the physical file before the separate cold-read session.

## BATCH-003-WRITE — remounted physical whole-file PASS

- Designated CARDWRITE UUID matched after owner reported mounted. Collected output is exactly 262,144 bytes, matching the independent entire-file oracle SHA-256 f29a1a67f46db9181f251199cb9bab73c65df2ccd0d70621303d56f70ee9ca26. Every region, guard and preserved shrinking-overwrite tail matches. No changed/missing existing protected files against the post-update baseline.
- Sole new user file is screenshot 20261005_113406.png; five known cleared menu caches were recreated. Screenshot visually inspected: SD WRITE RESEARCH B003R2, BATCH PASS, CASE/PASSED/FINISHED 0x20, ERROR 0, cycles 0x00079FD7, consistent with retained JTAG records.
- Immutable output/screenshot/snapshots/collector result under private work/evidence/runs/BATCH-003-WRITE/. Public summary: work/evidence/b003r2-physical-file-write.json. Normal Quit/shutdown/remount requested, owner confirmed mounted; exact physical action sequence not separately confirmed.
- Verdict: one complete warm batch, immediate comparisons and remounted whole-file persistence PASS. Cold B-only read, repeated sessions, other media/firmware and interruption safety remain pending. Next: safely eject, fresh launch same B003R2 core, leave READY for JTAG cold request; do not press A.

## BATCH-003-COLD — physical fresh-launch read-only PASS

- CARDWRITE was safely ejected after warm whole-file verification. Owner reported done after instruction to insert, fresh-launch B003R2 and leave READY without A. JTAG confirmed revision 2, READY, zero counters and accepted cold control. Host-mounted CARDWRITE absent. Exact power sequence not separately confirmed.
- Terminal retained summary: status 4, cold 1, 32 completed, 32 passed, 0 failed, 32 commands. All 32 indexed records matched expected case/final ordinal/offset/max read length/final write length and exact clean read-only flags 0x80000006; every retained write-cycle value is zero. No FPGA programming.
- Public structured evidence: work/evidence/b003r2-physical-jtag-cold.json. Original console evidence retained privately under work/evidence/jtag/.
- Verdict: one complete fresh-launch read-only recovery of all final payloads and preserved tails PASS. Final remount must confirm the whole guarded file and protected contents stayed unchanged during cold reads. Repeatability/stress, interruptions, other media/firmware and Tau CPU integration remain pending.
- Next owner action: final screenshot, normal Quit/shutdown and remount CARDWRITE for BATCH-003-COLD host collection; do not press A or reset until capture is complete (now collected).

## BATCH-003-COLD — remounted unchanged-file PASS; initial baseline complete

- CARDWRITE identity matched. Full 262,144-byte output still matches SHA-256 f29a1a67f46db9181f251199cb9bab73c65df2ccd0d70621303d56f70ee9ca26, including all guards and retained tails. Comparing directly against BATCH-003-WRITE's post-run snapshot shows no changed/missing existing files, including the batch output and original write64.bin. Only added file: screenshot 20261005_114024.png.
- Screenshot copied with verified hash and visually inspected: B003R2 BATCH PASS, CASE/PASSED/FINISHED 0x20, ERROR 0, cycles 0x0001A8FC, matching cold JTAG final-case timing. Original output/screenshot/inventories/result/review retained privately under work/evidence/runs/BATCH-003-COLD/. Public result: work/evidence/b003r2-physical-file-cold.json.
- Initial CPU-free existing-file write/remount/fresh-launch-read/remount baseline is complete: 38 successful write/read pairs, independently correct whole file, 32 subsequent read-only comparisons, and unchanged remounted contents. Owner followed prompted sequence and reported done; exact power actions not separately confirmed. One sequence does not establish exhaustive reliability, secure interrupted recovery or repeated durability.
- Next research gate: bounded serial repeatability/stress with independent generations and retained failure history, then explicit interruption/recovery experiments and exact Tau VexRiscv integration. Current verified core/output remain the preserved baseline; no new write or fixture reset performed in this collection.

## B004 implementation — simulation PASS; compilation pending

- New CPU-free stress profile: 10,000 changing-data round-robin pairs / 20,000 commands, new bounded slot 0x24/file stress-b004.bin, same stable core ID, banner B004/version 0.4.0. All operations retain independent failure/timing records in RAM; first failure and global extrema are sticky. Read-only mode recovers each of the 32 final generations.
- Full 10,000-pair direct RTL run and all retained success records pass; cold RTL 32 reads pass. Actual pinned APF serial bridge passes a representative 64-pair/two-visit run, with every payload word checked; the real core_bridge_cmd passes the same 64-pair workload. Independent full-file oracle agrees with both simulated outputs. Injected corruption/missing word/read error/write error and timeout/late completion/reset/button ownership pass. Later overwrites do not erase earlier retained failures.
- Six host oracle checks, eight fake-card updater guard checks and four mocked Tcl/JTAG tests pass. The latter validates all 10,000 records and 32 cold final indices, rejects corrupted/duplicate records and refuses wrong revision/busy start. These are simulations/tool tests, not physical SD/JTAG evidence.
- Native 320x240 RTL display captures for eight states inspected at work/sim/stress/video/. Prior minimal02 regression passes. New stress04 stage frozen and isolated Quartus compile launched; install requires complete successful compile, RAM/resource fit, corner timing and package hash qualification.
- Intended successful final physical SHA-256: 0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56. B003R2 and both successful outputs remain installed and unchanged until qualification. Method still has no interrupted-write atomicity/recovery claim.

## B004 first compile failure; immutable B004R1 correction

- Actual synthesis error: altsource_probe_body asserts PROBE_WIDTH <= 511; the first 512-bit probe violates it. Failed stress04 stage preserved unchanged, complete log retained as work/evidence/b004-first-compile-failure.log. No custom bitstream qualified or installed.
- B004R1 transports the same 16 logical words through a 511-bit probe by omitting the signature's constant-zero most significant bit. Host integer decoding naturally restores that leading zero. Live probe filter is 511 bits, header revision is 1, banner B004R1/version 0.4.1. New immutable stress04r1 compile stage launched with Java interpreter mode; no global VM or Tau changes.
- Prior simulation demonstrated complete 10,000-pair history and final byte oracle. Repeat tests also validate RAM-derived timing extrema; corrected revision/filter mock tests pass. The physically demonstrated B003R2 remains untouched pending successful R1 compile/timing/resource qualification.

## B004R1 timing-history assertion; B004R2 correction

- Expanded full-history assertions found global read extrema captured the DONE-edge counter, while retained records used the subsequent held counter (one clock greater). Payload comparisons still passed, but mismatched accounting would make independently checked hardware history inconclusive.
- Stopped only verified PID/process-group 435846, with exact /proc cwd in card-writing-lab/stress04r1-s1/src/fpga and quartus_sh command confirmed. Stop evidence and partial log retained; no claim of R1 fit/timing failure or qualified bitstream. Frozen R1 sources unchanged.
- B004R2 captures read_cycles at DONE once and uses it for completed retained records; global extrema use that same edge. Timeout timing still captures its outstanding elapsed value. Probe signature stays 0x53445704; revision 2, banner B004R2/version 0.4.2. Focused 64-pair timing/history regression and host updater/JTAG mocks pass; full expanded suite rerunning.
- New immutable stress04r2 stage launched. Installed card remains the complete physical B003R2 baseline until R2 fully qualifies. All payload/guard semantics remain unchanged.

## B004R2 expanded regression complete

- Full make test-stress PASS: 10,000 pairs / 20,000 commands, every indexed history record and global timing extrema validated; 32 cold reads; 64-pair actual command bridge and actual serial bridge runs; corruption/missing-word/command-error/timeout ownership and unwritten cold-file cases; JTAG control, held snapshots and invalid-index rejection. Independent complete-file oracle agrees with both direct and serial outputs.
- Six oracle and eight fake-card updater tests pass. Five latest host/Tcl tests validate all 10,000 mocked records, cold indices, bad/duplicate data, fresh-READY/wrong-revision guards, and a failed session whose later successful overwrite stays individually successful while the overall session remains failed. Raw per-operation flags are retained independently of summary failure.
- Native B004R2 display captures reviewed for all eight states. Prior B003 host regressions and macro top-level compilation pass; the prior minimal02 regression also passes. Frozen R1's timing failure is reproducible with the current parameterized testbench at revision 1. See work/evidence/b004r2-simulation-summary.json and test logs for scope. Real FPGA full compile/resource/timing still pending; no physical B004 result yet.

## B004R2 full qualification and verified installation

- Full compile successful: 0 errors / 168 warnings, elapsed 31:05. Uses 3,248 ALMs (18%), 3,617 registers, 1,034,037 block-memory bits (33%), 129 RAM blocks (42%), zero DSPs and one PLL. All intended history/payload memories infer RAM. Worst setup +3.767 ns / hold +0.152 ns; every reported corner TNS zero; no illegal/unconstrained clocks. External I/O delay limits remain (6 inputs/23 outputs).
- Collected real RBF/SOF/full reports; exact raw/once-reversed hashes and qualified source/simulation/configuration hashes recorded in custom-build-audit-stress04r2.json and BUILD_AUDIT.md. Qualified Pocket RBF_R SHA-256 4f8ee21d60090aab672b7539541d75bf5e44b474428e08a64651e10e00f3ad91. No JTAG FPGA programming.
- Before update, CARDWRITE matched the entire verified B003 cold snapshot (no changed or added files), with new scratch absent. Audited B004R2 plan applied to the same UUID/stable core. Independently rechecked all 11 installed package files, all 16 prior card-file backups and all 68 archived qualified B003 files. No unexpected protected changes; previous write64.bin and batch-b003.bin retain their exact successful hashes.
- Local private update journal/plan/snapshots/backups/final review: work/evidence/update-stress04r2/. Qualified B003 archive: work/archives/batch03r2-before-b004/. Public summary: work/evidence/b004r2-qualified-install-summary.json. New stress-b004.bin is the initial all-0xA5 fixture; no simulated success output was copied to the card.
- Safe ejection pending normal disk ejection. Next owner action after successful ejection: insert, fresh-launch same CARDWRITE02 entry, confirm B004R2/version 0.4.2 and READY 10000 PAIRS, leave Blaster connected, report loaded without A. Host validates live SDW4 revision 2 and starts the bounded 10,000-pair session. Physical endpoint/stress results still pending.

- Normal disk ejection succeeded after the independently verified update. CARDWRITE is safely ejected; owner may insert and fresh-launch B004R2 for the physical stress session.

## B004R2 first physical stress session — retained history PASS

- First JTAG start attempt found the FPGA device but no ISSP endpoint: owner had not loaded the core yet. No start/programming was issued. After owner loaded it, the exact SDW4 32/511 endpoint, magic/revision 2 and fresh READY/zero counters validated; one start request succeeded. No JTAG FPGA programming or result reset.
- Progress snapshots: 1,938 / 3,893 / 5,636 / 7,353 / 9,137 successful pairs, no failures; final warm terminal PASS: completed 10,000, passed 10,000, failed 0, commands 20,000, first-failure sentinel 16,383.
- Collected all 10,000 records before Quit. Decoder and independent assertions verify each index exactly once/in order, clean flags 0x80000007, revision 2, expected bounds and coherent counters; extrema reconstructed from every record match the globals. Write cycles 838,890–9,396,051 (11.298–126.546 ms); read cycles 451,106–1,625,245 (6.076–21.889 ms) at 74.25 MHz.
- Public summary: work/evidence/b004r2-physical-jtag-write.json. Full decoded history: work/evidence/b004r2-physical-jtag-write-records.json.gz (164,216 bytes), decompression independently matches the original decoded evidence SHA-256 d4230191a7eb79352f671192bea2ab589d40415f3378676093b9ab1189908d4f. Original raw/decoded captures retained privately in work/evidence/jtag.
- Owner may now screenshot, normal Quit, shutdown and remount CARDWRITE. Complete 256 KiB final-file verification (expected SHA-256 0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56), guard/protected-content checks and cold reads pending. Immediate comparisons do not prove 10,000 individually durable commits, interruption recovery, other cards/firmware or Tau CPU integration.

## B004R2 first physical stress file after remount — PASS

- CARDWRITE identity revalidated. Read-only collector STRESS-004-WRITE verifies the entire 262,144-byte file against the independent final-generation oracle: exact SHA-256 0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56, no failed regions/mismatch, all guard bytes preserved.
- No prior protected file changed or disappeared. Both successful minimal02 and B003 output hashes remain unchanged. Only additions: five expected regenerated menu caches and one result screenshot; no unexpected additions.
- Inspected native screenshot 20261005_131401.png: B004R2 STRESS PASS, OPERATION/PASSED/FINISHED 0x2710 (10,000), ERROR 0, CYCLES 0x0007BC86. The LCD timing is exactly one greater than the last retained completed read timing, as specified. Screenshot copied/hash-verified into immutable private run evidence.
- Public summary work/evidence/b004r2-physical-file-write.json. Original full snapshots/output/screenshot retained under work/evidence/runs/STRESS-004-WRITE. Normal Quit/shutdown/remount requested; owner reported card mounted, exact power sequence not separately confirmed. This establishes final-file persistence after remount; cold launch, repeated power cycles and interrupted-write recovery still pending.

## B004R2 first fresh-launch cold read — JTAG PASS

- Owner reported done after requested insertion/fresh launch. Live SDW4 revision 2 READY validated with zero completed/command counters; requested cold mode once. No FPGA programming or writes.
- Terminal cold PASS: all 32 final-generation regions pass, 32 reads, zero writes/failures, first-failure sentinel 16,383. All 32 distinct expected final-operation indices, clean flags 0x80000006, zero write timing, byte ranges and consistent global timing extrema independently verified.
- Read cycles 58,405–597,148 (0.787–8.042 ms at 74.25 MHz). Full public record history and original capture hashes: work/evidence/b004r2-physical-jtag-cold.json. Original raw/decoded captures retained privately.
- Result collection finished before Quit. Next: screenshot, normal Quit/shutdown/remount, then whole-file and protected-content comparison against immutable STRESS-004-WRITE snapshot. Exact power sequence not separately confirmed; repeated power-cycle/interruption qualification still pending.

## B004R2 first cold read after remount — full baseline PASS

- STRESS-004-COLD collector revalidated card identity and all 262,144 bytes/guards: unchanged exact expected SHA-256 0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56.
- Independent comparison against STRESS-004-WRITE snapshot: every existing file unchanged, none missing; only new file is result screenshot 20261005_133008.png. Both prior successful output files remain preserved.
- Native screenshot inspected and copied/hash-verified into immutable private run evidence: B004R2 STRESS PASS, OPERATION 0x2700 (9984, expected final case's index + 1), PASSED/FINISHED 0x20 (32), ERROR 0, CYCLES 0x00091C9D (exactly last retained read timing + 1).
- Public summary work/evidence/b004r2-physical-file-cold.json. Complete first B004R2 baseline passes: 10,000 immediate pairs/full history, exact final file after remount, 32 fresh-launch reads/zero writes, unchanged complete file/protected contents after second remount. Exact power sequence not separately confirmed; repeated owner-confirmed shutdown cycles remain the next discovery step. No broader repeatability/interruption/Tau CPU qualification claim.

## B004R2 second fresh-launch read-only session — PASS

- Cold repeat01 begins from independently verified READY/zero counters after card ejection and owner reporting ready. Owner was asked to power fully off before insertion/launch; full power-off is not separately confirmed and this session is not yet counted as an owner-confirmed power cycle.
- All 32 final-generation regions pass again, 32 reads/zero writes/failures. Every indexed record, clean flag/bounds and timing extrema validated independently. Read cycles 55,013–507,271 (0.741–6.832 ms).
- Separate complete history: work/evidence/b004r2-physical-jtag-cold-repeat01.json; original raw/decoded captures retained privately. Prior results remain unchanged. Post-read screenshot/remount and whole-file/protected-content comparison against STRESS-004-COLD remain pending.

## B004R2 cold repeat01 after remount — PASS

- Designated card identity revalidated; whole 262,144-byte file/guards match the expected 0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56 SHA-256.
- Independent comparison against STRESS-004-COLD: every prior file unchanged, none missing; only new result screenshot 20261005_134021.png. Native screenshot inspected, copied and hash-verified: B004R2 STRESS PASS, OPERATION 0x2700, PASSED/FINISHED 0x20, ERROR 0, CYCLES 0x00019FDD (last retained read timing + 1).
- Separate public summary work/evidence/b004r2-physical-file-cold-repeat01.json; full private snapshot/output/screenshot retained immutably. Two separate fresh-launch read-only sessions now pass with subsequent whole-file/protected-content verification. Owner reported mounted without separately confirming full power-off; do not count these as confirmed power-cycle qualification.

## B004R2 third fresh-launch read-only session — PASS

- Cold repeat02: owner reported loaded after requested full power-off/insertion/fresh launch. Live READY/zero counters independently verified before one cold start. Exact power-off action remains unconfirmed; no FPGA programming or writes.
- All 32 final-generation regions pass, 32 reads/zero failures. Every indexed record, clean flag, byte range and timing extrema verified. Read cycles 57,509–513,000 (0.775–6.909 ms at 74.25 MHz).
- Separate complete public history work/evidence/b004r2-physical-jtag-cold-repeat02.json; original raw/decoded captures preserved privately. Post-read screenshot/remount and whole-file/protected-content comparison against STRESS-004-COLD-REPEAT01 remain pending. Three fresh-launch read sessions pass; broader power-cycle/interruption qualification remains pending.

## B004R2 cold repeat02 after remount — PASS

- Card identity revalidated. Entire 262,144-byte file/guards match expected SHA-256 0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56. Independent comparison against STRESS-004-COLD-REPEAT01: every prior file unchanged, none missing; only new result screenshot 20261005_141038.png.
- Native screenshot inspected, copied/hash-verified: B004R2 STRESS PASS, OPERATION 0x2700, PASSED/FINISHED 0x20, ERROR 0, CYCLES 0x00050E44 (final retained read timing + 1). Full snapshots/output/screenshot remain immutable private evidence.
- Public summary work/evidence/b004r2-physical-file-cold-repeat02.json. Three separate fresh-launch read-only sessions and subsequent complete-file/protected-content checks pass. Exact power actions not separately confirmed; repeated confirmed power cycles, interruption recovery and Tau CPU integration remain pending.

## B004R2 fourth fresh-launch read-only session — PASS

- Cold repeat03 starts from independently verified READY/zero counters after owner reports ready; exact requested power-off sequence is not separately confirmed. No FPGA programming or writes.
- All 32 final-generation regions pass, 32 reads/zero failures; each indexed record, flag/bounds and timing extrema validated. Read cycles 55,023–593,825 (0.741–7.998 ms).
- Complete separate public history work/evidence/b004r2-physical-jtag-cold-repeat03.json; original captures retained privately. Fourth fresh-launch read session passes; post-read remount and comparison against STRESS-004-COLD-REPEAT02 still pending.

## B004R2 cold repeat03 after remount — PASS

- Card identity revalidated; complete 262,144-byte file/guards match expected SHA-256 0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56. Independent comparison against STRESS-004-COLD-REPEAT02: every existing file unchanged, none missing; only new result screenshot 20261005_141827.png.
- Native screenshot inspected and copied/hash-verified into immutable private evidence: B004R2 STRESS PASS, OPERATION 0x2700, PASSED/FINISHED 0x20, ERROR 0, CYCLES 0x00019FB3 (last retained read timing + 1).
- Public summary work/evidence/b004r2-physical-file-cold-repeat03.json. Four fresh-launch read-only sessions now pass with subsequent complete-file/protected-content verification. Exact power actions not separately confirmed; broader confirmed power-cycle, interruption recovery and Tau CPU qualification remain pending.

## B004R2 fifth fresh-launch read-only session — PASS

- Cold repeat04 begins from independently verified READY/zero counters after owner reports ready. Full power-off requested but not separately confirmed; no FPGA programming or writes.
- All 32 final-generation regions pass, 32 reads/zero failures; all indexed records, clean flags, bounds and timing extrema verified. Read cycles 55,003–509,792 (0.741–6.866 ms).
- Complete separate public history work/evidence/b004r2-physical-jtag-cold-repeat04.json; original raw/decoded captures retained privately. Post-read screenshot/remount and whole-file/protected comparison against STRESS-004-COLD-REPEAT03 remain pending.

## B004R2 cold repeat04 after remount — PASS

- Card identity revalidated; whole 262,144-byte file/guards match expected SHA-256 0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56. Independent comparison against STRESS-004-COLD-REPEAT03: every existing file unchanged, none missing; only new result screenshot 20261005_143049.png.
- Native screenshot inspected and copied/hash-verified into immutable private evidence: B004R2 STRESS PASS, OPERATION 0x2700, PASSED/FINISHED 0x20, ERROR 0, CYCLES 0x0001A0A2 (final retained read timing + 1).
- Separate public summary work/evidence/b004r2-physical-file-cold-repeat04.json. Five fresh-launch read-only sessions now pass with subsequent whole-file/protected-content checks. Exact power actions not separately confirmed; broader confirmed power-cycle/interruption/Tau CPU qualification remains pending.

## B004R2 sixth fresh-launch read-only session — PASS

- Cold repeat05 begins from independently verified READY/zero counters after owner reports ready. Exact requested full power-off not separately confirmed; no FPGA programming or writes.
- All 32 final-generation regions pass, 32 reads/zero failures; indexed records, clean flags, byte ranges and timing extrema verified. Read cycles 57,554–504,289 (0.775–6.792 ms).
- Complete separate public history work/evidence/b004r2-physical-jtag-cold-repeat05.json; original raw/decoded captures retained privately. Post-read screenshot/remount and comparison against STRESS-004-COLD-REPEAT04 remain pending.

## B004R2 cold repeat05 after remount — PASS

- Card identity revalidated; complete 262,144-byte file/guards match expected SHA-256 0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56. Independent comparison against STRESS-004-COLD-REPEAT04: every existing file unchanged, none missing; only new result screenshot 20261005_144257.png.
- Native screenshot inspected, copied/hash-verified into immutable private evidence: B004R2 STRESS PASS, OPERATION 0x2700, PASSED/FINISHED 0x20, ERROR 0, CYCLES 0x0004F6F5 (final retained read timing + 1).
- Separate public summary work/evidence/b004r2-physical-file-cold-repeat05.json. Six fresh-launch read-only sessions now pass with subsequent whole-file/protected-content verification. Exact power actions not separately confirmed; broader confirmed power-cycle/interruption/Tau CPU qualification remains pending.

## B004R2 seventh fresh-launch read-only session — PASS

- Cold repeat06 begins from independently verified READY/zero counters after owner reports ready. Exact requested full power-off not separately confirmed; no FPGA programming or writes.
- All 32 final-generation regions pass, 32 reads/zero failures; indexed records, clean flags, byte ranges and timing extrema independently validated. Read cycles 57,880–814,021 (0.780–10.963 ms).
- Complete separate public history work/evidence/b004r2-physical-jtag-cold-repeat06.json; original raw/decoded captures retained privately. Post-read screenshot/remount and comparison against STRESS-004-COLD-REPEAT05 remain pending.

## B004R2 cold repeat06 after remount — PASS

- Card identity revalidated; complete 262,144-byte file/guards match expected SHA-256 0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56. Independent comparison against STRESS-004-COLD-REPEAT05: every existing file unchanged, none missing; only new result screenshot 20261005_145524.png.
- Native screenshot inspected and copied/hash-verified into immutable private evidence: B004R2 STRESS PASS, OPERATION 0x2700, PASSED/FINISHED 0x20, ERROR 0, CYCLES 0x00050CCA (final retained read timing + 1).
- Separate public summary work/evidence/b004r2-physical-file-cold-repeat06.json. Seven fresh-launch read-only sessions now pass with subsequent whole-file/protected-content checks. Exact power actions not separately confirmed; broader confirmed power-cycle/interruption/Tau CPU qualification remains pending.

## B004R2 eighth fresh-launch read-only session — PASS

- Cold repeat07 begins from independently verified READY/zero counters after owner reports ready. Exact requested full power-off not separately confirmed; no FPGA programming or writes.
- All 32 final-generation regions pass, 32 reads/zero failures; indexed records, clean flags, byte ranges and timing extrema independently validated. Read cycles 55,443–541,119 (0.747–7.288 ms).
- Complete separate public history work/evidence/b004r2-physical-jtag-cold-repeat07.json; original raw/decoded captures retained privately. Post-read screenshot/remount and comparison against STRESS-004-COLD-REPEAT06 remain pending.

## B004R2 cold repeat07 after remount — PASS

- Card identity revalidated; complete 262,144-byte file/guards match expected SHA-256 0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56. Independent comparison against STRESS-004-COLD-REPEAT06: every existing file unchanged, none missing; only new result screenshot 20261005_151325.png.
- Native screenshot inspected, copied/hash-verified into immutable private evidence: B004R2 STRESS PASS, OPERATION 0x2700, PASSED/FINISHED 0x20, ERROR 0, CYCLES 0x0001A23D (final retained read timing + 1).
- Separate public summary work/evidence/b004r2-physical-file-cold-repeat07.json. Eight fresh-launch read-only sessions now pass with subsequent whole-file/protected-content checks. Exact power actions not separately confirmed; broader confirmed power-cycle/interruption/Tau CPU qualification remains pending.

## B004R2 ninth fresh-launch read-only session — PASS

- Cold repeat08 begins from independently verified READY/zero counters after owner reports ready. Exact requested full power-off not separately confirmed; no FPGA programming or writes.
- All 32 final-generation regions pass, 32 reads/zero failures; indexed records, clean flags, byte ranges and timing extrema independently validated. Read cycles 55,963–688,330 (0.754–9.270 ms).
- Complete separate public history work/evidence/b004r2-physical-jtag-cold-repeat08.json; original raw/decoded captures retained privately. Post-read screenshot/remount and comparison against STRESS-004-COLD-REPEAT07 remain pending.

## B004R2 cold repeat08 after remount — PASS

- Card identity revalidated; complete 262,144-byte file/guards match expected SHA-256 0ef80e007254ccc6d63874e2aac6e0082e360de00843b82b36836807ff433e56. Independent comparison against STRESS-004-COLD-REPEAT07: every existing file unchanged, none missing; only new result screenshot 20261005_152117.png.
- Native screenshot inspected and copied/hash-verified into immutable private evidence: B004R2 STRESS PASS, OPERATION 0x2700, PASSED/FINISHED 0x20, ERROR 0, CYCLES 0x0001A18A (final retained read timing + 1).
- Separate public summary work/evidence/b004r2-physical-file-cold-repeat08.json. Nine fresh-launch read-only sessions now pass with subsequent whole-file/protected-content checks. Exact power actions not separately confirmed; broader confirmed power-cycle/interruption/Tau CPU qualification remains pending.

## B004R2 tenth fresh-launch read-only session — PASS

- Cold repeat09 begins from independently verified READY/zero counters after owner reports ready. Exact requested full power-off not separately confirmed; no FPGA programming or writes.
- All 32 final-generation regions pass, 32 reads/zero failures; indexed records, clean flags, byte ranges and timing extrema independently validated. Read cycles 55,949–508,032 (0.754–6.842 ms).
- Complete separate public history work/evidence/b004r2-physical-jtag-cold-repeat09.json; original raw/decoded captures retained privately. All ten fresh-launch read sessions pass (320 reads, zero writes/failures); final post-read screenshot/remount and comparison against STRESS-004-COLD-REPEAT08 remain pending.

## B004R2 tenth remount and initial campaign summary — PASS

- STRESS-004-COLD-REPEAT09 identity/whole-file/guards pass with exact expected SHA-256. Independent comparison against repeat08: all prior files unchanged; only new screenshot 20261005_152605.png. Inspected and copied/hash-verified screenshot: STRESS PASS, PASSED/FINISHED 0x20, ERROR 0, CYCLES 0x0001A207 (last retained read + 1).
- All ten sessions and host snapshots independently rechecked as a chain: 320 reads, zero writes/failures; every prior file unchanged at each remount. Public final summary b004r2-physical-file-cold-repeat09.json and aggregate b004r2-physical-campaign-summary.json under work/evidence.
- B004_RESULTS.md records the completed initial single-card persistence baseline and its exact limits. Power actions not separately confirmed; no confirmed-cycle or interrupted-write safety claim. Next proposed experiment B005: two preallocated alternate files, independently validated generation/checksum/length format and controlled recovery tests before Tau CPU integration.

## B005 prepared — compilation and physical trials pending

- B004 baseline committed and pushed as ad3f039. Its complete 10,000-pair history, ten read-only sessions and final snapshots remain preserved.
- B005 implements alternating preallocated files, fixed record/header/CRC validation, 64-bit generation, exact readback and controlled single-update pause/resume points. Full planned procedure: B005_HARDWARE_RUN.md.
- 36 RTL trials and 39 host/mock tests pass (7 oracle, 6 JTAG, 12 updater, 9 collector, 5 cleanup). Actual pinned command and serial modules are exercised under simulation. Nine native display states reviewed.
- Unique version 0.5.0/banner B005 uses the stable CARDWRITE02 entry. Frozen recovery05 stage launched on the isolated VM; full fit/timing qualification pending. No B005 card mutation or physical success yet.
- Mounted card matches the exact final B004 repeat09 snapshot. Owner requested removal of unneeded cores; reviewed cleanup targets only the original example and CARDWRITE01, with backups and all assets preserved, after B005 installation.

- B005 implementation and simulation evidence pushed as b10514a. Full read-only backup of 98 non-OS card files (103,448,123 bytes) independently hash-verified; card unchanged during backup. Synthesis passes; final fit/timing remain pending. Synthesis infers RX, retained A record and all five history arrays as RAM; TX maps to registers with its two independent read ports. Final resource/timing reports determine whether this bounded implementation qualifies.

## B005 qualified and installed — Pocket trials pending

- Full compile passed at 16:33:47 WEST, zero errors / 167 warnings. All four timing corners pass, worst setup +2.924 ns / hold +0.116 ns. Resources and external-interface limits recorded in BUILD_AUDIT.md.
- B004 qualified artifacts and complete physical evidence archived before mutation; all 196 archive files independently re-hashed afterward. Update backups and all 12 installed package file hashes independently verified. Three prior outputs and every unrelated existing file remain unchanged.
- B005 version 0.5.0/banner B005 installed in the stable CARDWRITE02 entry. Both new 8 KiB files are intact all-0xA5 fixtures; no B005 physical write test has run.
- Owner-authorized cleanup completed: original Keyboard Mouse Target Data example and CARDWRITE01 removed after verified 19-file backups. CARDWRITE02 is the only remaining core. Every asset, screenshot and prior output is preserved. Full protected-content comparison passes; separate immutable local update/cleanup journals and public b005-installation-summary.json retained.
- Next: fresh-load B005 READY and collect the first 64-commit JTAG-controlled session, then full-byte/remount and read-only recovery gates in B005_HARDWARE_RUN.md. Neither installation nor simulation proves recovery under physical interruption.

- CARDWRITE safely ejected after qualification, update, cleanup and all independent hash/protected-content gates. Ready for fresh B005 loading; leave A/B untouched for the first JTAG-controlled batch.

## B005 first physical clean batch — immediate PASS

Owner reported ready; physical SDW5 revision/width signature and fresh READY/zero counters verified before JTAG start. All 64 retained records pass: 322 commands, zero failures, generation A=63/B=64, sequence 1–64 with alternating destinations and independently reconstructed CRCs. Full public history: work/evidence/b005-physical-jtag-clean01.json; original raw/decoded evidence preserved privately. Final physical file/guard/remount checks remain pending. Owner cannot swap the card for several hours and requested all feasible connected tests/development; proceed with bounded qualified matching-SOF reload campaigns while preserving each prior history. FPGA reload is not a power cycle or SD remount.

## Connected B005 tests and B006 development in progress

- Qualified matching-SOF JTAG reload demonstrated: exact local/VM SOF SHA and cable/device verified, zero-error programming preserved. First read-only reload check passes generation 64, two reads, zero writes. New reload safety tests (6) and independent connected-model tests (5) pass.
- Owner requested all feasible connected tests/development while unable to swap the card for several hours. Bounded connected B005 campaign started: nine additional clean batches/reloads, two rounds of four pause/resume controls and FPGA-only between-command interruptions, then inactive-record repair. Every history is preserved before reload; stop on any mismatch. Actual checkpoints in b005-connected-campaign.json. No power-cycle, SD-power-cut or host-remount claim.
- B006 separate frozen guarded06 stage implements full 8 KiB guard/received-word checking, refusal to initialize damaged nonblank pairs, and unified synchronous TX RAM access. Full simulation rerun and isolated compile are in progress; initial harness-only fault-injection error retained in b006-harness-correction.json and its original log. No frozen RTL was changed after launch. No B006 programming or installation yet.

- Corrected B006 campaign passes all 50 RTL trials, seven independent host-oracle tests and six mock JTAG tests. Whole-file corruption at ten locations across both files, missing guard word, post-write guard corruption, both-damaged refusal, high-generation carry, 64-save command/serial paths and all inherited timeout/error/recovery cases pass. Tested RTL/top/video match frozen guarded06 source hashes exactly. Nine native screens reviewed with NO VALID fixture generation/mask corrected to zero. Full compile/internal timing and physical B006 remain pending.

- B006 synthesis passes: 4,671 estimated registers and 90,747 block-memory bits. Full 2,048-word RX and 128-word TX/retained-A plus five history arrays infer RAM. TX inference improvement is established in the real map report; final fit/resource/timing qualification remains pending. B005 connected campaign continues independently.

## Additional connected-period development

- B006's frozen RTL passes 657 additional adversarial trials: all 513 byte-prefix boundaries replacing an inactive record, 128 seeded record-bit corruptions across both files and 16 extra guard corruptions. Combined RTL count is 707, separate from host/mock tests. Exact sources/reports are added to the qualification hash gate; physical power cuts remain untested.
- B006 loader/campaign safety and independent-model tests pass (6 + 5). B006_HARDWARE_RUN.md defines qualification, compatible JTAG-only loading, bounded saves/reloads/pauses and later remount checks. No B006 loading yet; B005 campaign retains exclusive JTAG ownership.
- Read-only clean Tau revision 7b98a2e is pinned with exact copied CPU/crossing/license. Crossing-only simulation passes 1,200 modeled commands. Actual generated VexRiscv executes firmware and passes 1,500 modeled commands across four clock rates plus a stalled-bus case. No Tau modifications, physical CPU writes, full SoC/playback or independent-reset qualification. TAU_CPU_INTEGRATION.md records the next stages and remaining boundaries.
- B006 fit completed at 17:34:17 WEST: 4,893 ALMs (26%), 5,078 registers, 90,747 block-memory bits and 18 RAM blocks, no DSPs, one PLL. Final flow/timing qualification remains pending; the fitter has a real TX RAM implementation.

- Isolated exact-Tau-crossing reset diagnostic confirms CPU-side busy may clear before an outstanding APF command finishes, followed by a delayed completion incrementing the post-reset sequence. This is a documented integration limitation, not a failed Pocket session or reset-safety pass. No Tau changes/hardware reset were made; coordinated owner/reset handling remains required.

## B006 qualified — connected physical trial pending

Full compile passed 17:40:22 WEST, zero errors / 167 warnings, 39:10. Four internal timing corners pass; worst setup +3.402 ns / hold +0.108 ns, all TNS zero. Reviewed fit/RAM/warnings/external-delay limits and exact source/test/display/config hashes qualify the genuine collected SOF/RBF and once-bit-reversed package. Details in BUILD_AUDIT.md. No B006 programming yet: await B005's completed preserved campaign, then a guarded ABI-compatible JTAG load and first full-region read-only recovery. Existing card metadata remains B005/0.5.0.
