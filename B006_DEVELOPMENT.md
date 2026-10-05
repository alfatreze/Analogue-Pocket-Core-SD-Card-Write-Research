# B006 — whole-file guards and explicit blank initialization

## Changes under qualification

B005 validates each 512-byte record and compares each newly written record exactly. B006 reads the fixed 8,192-byte region of each existing preallocated file before choosing a destination, and again after each save. It requires all 2,048 received words, checks every guard word outside offsets 512–1,023 against 0xA5, and validates the unchanged B005 record/header/CRC/generation. A guard failure stops without further writes (reason 0x25); an incomplete read stops with reason 0x23.

Initialization is permitted only when both records are exactly blank 0xA5 and both whole-file guards pass. If neither record validates and either is nonblank, a save refuses with reason 0x13, preserving forensic bytes. Read-only mode still reports NO VALID without writing. When one valid record remains, an invalid inactive record may be replaced after full guard checks. Equal-generation conflict and uint64 exhaustion remain permanent stop conditions.

TX uses one synchronous RAM read path selected between APF payload service and record verification, plus a unified write port. This aims to remove B005's register-mapped TX buffer. Real Quartus RAM/resource/timing reports must establish the outcome.

## Compatibility and identity

Separate frozen build guarded06, version 0.6.0/banner B006, debug endpoint SDW6 (source 32/probe 511, revision zero). The two filenames/slots and SDR5 record format remain unchanged. The package contains no save fixtures; never reset B005 output files. A later JTAG-only trial can use the existing B005 slot metadata only after explicit compatibility and qualification checks, retaining the deliberate difference between SD metadata 0.5.0 and the loaded B006 SOF. No B006 hardware programming or card update has occurred yet.

## Evidence gates

- Separate RTL suite covers prior clean/recovery/prefix/fault/generation cases plus both-damaged initialization refusal, ten guard corruptions across both files, missing guard word and post-write guard corruption.
- Initial test-harness failure is preserved: a text replacement unintentionally changed j==127 to j==1407, and the new injection omitted no guard word. RTL passed the uninjected trial correctly; the harness expected a failure. The correction changes only the testbench, not frozen compile sources. Full rerun is required.
- Nine native RTL display states are rendered/inspected independently with realistic fixture masks and NO VALID telemetry. These are renderer checks, not physical screenshots.
- Compile sources are frozen once launched. No package qualification or physical success claim until full source/test/display/hash gates and all timing corners pass.
- FPGA checks cover the fixed 8,192-byte region; exact host file size, any bytes beyond that region and all unrelated files still require independent host verification. These checks complement later physical host comparison; they do not supply an SD flush, authenticated storage or guaranteed power-loss atomicity.
