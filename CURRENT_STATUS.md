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
