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
