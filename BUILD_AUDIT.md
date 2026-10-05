# Minimal01 build audit — 2026-10-04

## Reproducible identity

- Quartus Prime Lite 25.1std.0 Build 1129, device 5CEBA4F23C8, seed 1.
- Full compilation: 0 errors, 162 warnings; 16 minutes 16 seconds.
- Source manifest SHA-256: `a171d77028594d4e5498f0f30300fc01e3fe5b0c803c90d4469b464d903614ae`.
- Raw RBF SHA-256: `c057d353e490b76d6ac167af6e687e489a9c1d23b75b91c8b95f5f1f1b83fe6b`.
- Installed RBF_R SHA-256: `1d1ab747086c0c057af4c05f4c0763243c9a5e6f8e0eb4731afd047f5a292860`.
- Raw RBF was bit-reversed once; the package gate rejects the upstream template bitstream.
- Resources: 2,544/18,480 ALMs; 2,214 registers; 6/308 RAM blocks; 8,597 block-memory bits; 0 DSPs; 1 PLL.

## Timing scope and warnings

All reported setup/hold/pulse-width timing corners pass with zero total negative slack. Worst setup slack is +3.714 ns; worst hold is +0.126 ns. No illegal or unconstrained clocks are reported.

There are 4 unconstrained external input ports (bridge 1-wire and SPI) and 22 unconstrained external output ports (bridge and scaler video/audio). The inherited template does not supply their min/max I/O delays. Internal timing success does not establish their physical margins. These interfaces require Pocket hardware observation; the official unchanged control provides a separate comparison.

Reviewed warnings include inherited unused/undriven command fields, initialized build-ID padding, safe constant unused memory/cartridge pins, absent PLL reset, non-dedicated bridge SPI clock routing, unused PLL outputs, incomplete inherited I/O assignments and disabled SignalTap metadata. The PLL has no runtime loss-of-lock recovery; video loss requires relaunch and must be recorded. Lab truncations narrow the word index and display coordinates intentionally. The display case has a preceding blank default assignment; the synchronizer's unused single-bit rise/fall outputs produce width warnings for its 135-bit diagnostic bus. Diagnostic bus synchronization can tear during changes and is not used to authorize file operations.

Qualification is limited to this source/seed/tool/device build, simulation checks and reported internal constraints. Pocket boot, command completion, physical SD durability, cold recovery and protected-file integrity remain pending.

## Evidence

- `work/fpga/minimal01-s1/`: complete compile log, synthesis/fitter/assembler and timing reports plus raw bitstream.
- `work/build/minimal01-manifest.json`: frozen stage file hashes. The first frozen stage contains upstream shipped outputs; packaging accepts only the newly collected full-build artifact. Future preparation strips old outputs.
- `work/evidence/custom-build-audit.json`: machine-readable identity and report hashes.
- `work/packages/minimal01-manifest.json`: installed package hashes and identical build provenance.

The local simulation copy moves datatable declarations ahead of first use for Icarus. The frozen Quartus stage retains the original declaration ordering, with identical behavior intended. No vendor source was changed.


# Minimal02 build audit — 2026-10-05

- Quartus 25.1std.0 Build 1129 Lite; device 5CEBA4F23C8; seed 1. Full compile: 0 errors, 162 warnings; 17 minutes 25 seconds.
- 2,757/18,480 ALMs (15%), 2,123 registers, 6/308 RAM blocks, 8,597 memory bits, no DSPs, one PLL.
- All reported timing corners pass with zero total negative slack. Worst setup +4.169 ns; worst hold +0.150 ns. No unconstrained clocks. Four bridge input and 22 bridge/scaler output ports still lack external I/O delay constraints; physical interface margins are not established by this timing pass.
- Report confirms Power-Up Don't Care **Off**. Reviewed warning categories match the template/interface and deliberate display/word-index narrowing described above. No new unconstrained clocks.
- Frozen source manifest SHA-256: `cc96e104f584718021a7abd73d07ebfe79b8cf4e27fd099add7eab8169132662`. Its lab RTL equals current lab RTL; vendor is untouched; stage contains no shipped old outputs.
- Raw RBF SHA-256: `7fa74e63a0dd2dee4f7a002d7da8626beecc77350b3a1aacc60acb24bc091fda`.
- RBF_R SHA-256: `d0d17448b5347e7916f8171fe20aa75c411b43fa6166eadcc501fa14a115bff5`.
- SOF SHA-256: `c09d8e97784e5126950c770f8c88069a249513fa56206369e42af0093dbaa234`; retained for optional JTAG loading. SignalTap/ISSP are absent in this build.
- Complete reports: `work/fpga/minimal02-s1/`; machine-readable audit: `work/evidence/custom-build-audit-minimal02.json`.
- Simulations pass, including the actual serial state machines with documented syntax adaptation. Physical bytes, startup generation and cold persistence remain pending on Pocket.

## B003R2 — automatic batch and retained ISSP history

Exclusive stage `work/build/batch03r2`, remote `card-writing-lab/batch03r2-s1`, seed 1. Full Quartus 25.1std.0 Build 1129 Lite compile completed 2026-10-05 01:47:51 VM time, elapsed 25:38, **0 errors / 169 warnings**. Device 5CEBA4F23C8. Prior B003 generator crash and B003R1 agent-stopped resource attempt are retained separately and are not qualified images.

- ALMs 2,829 / 18,480 (15%); registers 2,859; block memory 83,181 / 3,153,920 bits (3%); RAM blocks 15 / 308; DSP blocks 9 / 66; PLLs 1 / 4.
- Report confirms TX, RX and all three log arrays infer RAM. Power-up don't-care is Off.
- Worst reported setup **+2.545 ns**; hold **+0.075 ns** (JTAG clock); all corners have TNS 0. Recovery/removal and pulse-width checks also pass.
- No illegal/unconstrained clocks. Generated JTAG SDC constrains altera_reserved_tck at 30 MHz and groups it asynchronously.
- **External margins remain unqualified:** 6 input and 23 output ports lack I/O delays, including inherited bridge/scaler ports plus JTAG TDI/TMS/TDO. This qualifies reported internal timing; it does not prove cable/board/APF physical margins, JTAG service operation or SD persistence.
- Frozen source-manifest SHA-256 `9ed9f7965ffe60ce357826151cded5e132d5cbb8736ab37483c9d5a2261595d8`.
- Raw RBF SHA-256 `dcb7ed7585a1676e34869270cf371528abf4620466e8f0aa765640c0cdf6ae35`; SD RBF_R (byte bit reversal exactly once) `4944d570b7f97caf3b2d72b4c5c7f63532c5f819e1d675f567d1cbb14c7a552e`.
- SOF SHA-256 `7b9d1e98f5d1e65e075c3199b9b9bdfb619c3c1c169c09b331ff893141c71303`.

Complete reports/SOF/RBF: `work/fpga/batch03r2-s1`; audit and report hashes: `work/evidence/custom-build-audit-batch03r2.json`. Matching package: `work/packages/batch03r2`, fixed core identity CARDWRITE02, visible B003R2/version 0.3.2, new batch-b003.bin slot 0x23. Physical batch and new ISSP endpoint remain pending.

## B004R2 — qualified and installed; physical stress pending

Quartus 25.1std.0 Build 1129 Lite, 5CEBA4F23C8, seed 1; full compilation successful (0 errors / 168 warnings), elapsed 31:05. Uses 3,248/18,480 ALMs (18%), 3,617 registers, 1,034,037/3,153,920 block-memory bits (33%), 129/308 RAM blocks (42%), zero DSPs and one PLL. All three 10,000x32 history arrays and both 1,024x32 payload arrays infer RAM. Worst setup +3.767 ns, hold +0.152 ns; all reported setup/hold/recovery/removal/pulse checks pass and TNS is zero. Illegal/unconstrained clocks: zero. Six input and 23 output ports retain incomplete external delay constraints (including JTAG), so board-level external margins are not fully qualified.

- Frozen source manifest SHA-256: 20b40c60f9a11e3df62c73b4c70d41e9d735bb03d9f2a3b22c598cb51bbd2fce.
- Raw RBF: 4d9e0385cf656405a09a8df98750dd8650a94ef102a1aa4b522f32c1ae66c9f3.
- Once-bit-reversed Pocket RBF_R: 4f8ee21d60090aab672b7539541d75bf5e44b474428e08a64651e10e00f3ad91.
- SOF (not programmed through JTAG): 0eaeed5497705763bf6512b8a23ca93f50fc68a8ad7c8aebcb9169b576e1c983.

Full reports/binaries under work/fpga/stress04r2-s1/, hashed custom-build-audit-stress04r2.json and qualified package manifest. Packaging also requires the passing simulation source/configuration hashes to match the frozen stage. The designated-card update independently verified 11 installed files, 16 prior card-file backups, 68 archived qualified B003 files and no unrelated protected changes. Physical B004 stress/cold evidence remains separate.
