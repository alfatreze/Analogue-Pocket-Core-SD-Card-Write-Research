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
