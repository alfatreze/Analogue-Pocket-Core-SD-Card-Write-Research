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
