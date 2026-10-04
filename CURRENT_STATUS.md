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
