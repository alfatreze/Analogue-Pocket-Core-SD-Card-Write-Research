# Next CPU integration stage

## Read-only reference

Tau revision 7b98a2ee33dc01dda2b3a19c22e924c52d08bff9 was clean when inspected. `work/evidence/tau-cpu-reference.json` pins hashes of the actual generated VexRiscv, SoC, target crossing, linker script and original crossing test. Exact crossing/test/license copies live in references/tau-7b98a2e; Tau remains unchanged.

The generated CPU exposes cached instruction/data Wishbone buses. Tau's source places MMIO at 0x80000000 because address bit 31 marks uncached accesses. CPU Wishbone addresses are word addresses; APF source/destination and file offsets are byte addresses. The default firmware clock contract is 60 MHz. Do not infer write visibility from a CPU store to cached RAM.

Tau's crossing selects read/open/get/write/flush through cmd_sel 0–4. It waits for held APF DONE to clear before accepting the new completion. Firmware must sample the 8-bit sequence before GO and wait for a genuine change. Parameters/payload must remain stable until that completion. A local timeout cannot cancel an APF command.

## Existing isolated simulation

`python3 sim/test_tau_card_cdc.py` uses the pinned exact crossing, modeled APF completion and four CPU clock ratios (nominal 50, 60, 74.25 and 90 MHz). Each performs 300 commands, including all five one-hot selections, all eight error codes, stale DONE, an ignored extra GO while busy and sequence wrap. Full logs/source hashes remain under work/sim/tau-cdc and work/evidence/tau-cdc-simulation.json.

This is crossing-level simulation, without executing VexRiscv or talking to the Pocket. Modeled flush selection does not prove physical flush support. Independent clock-domain reset is not qualified: the 74 MHz FSM/toggles are initialized at FPGA configuration, while rst_sys directly resets only the CPU-side state. A production owner must block reset/parameter changes while outstanding, and reset semantics need a separate fault test before integration.

## B007 implementation order

1. Pin/copy the exact generated CPU with its license/provenance; retain the CPU-free B006 baseline. Do not regenerate or silently substitute another CPU configuration.
2. Build a small isolated 60 MHz SoC with uncached command/status registers and bounded BRAM; exclude audio, SDRAM and PSRAM initially. Preserve the exact SDR5 format, two slots and independent host oracle.
3. First let the CPU drive the proven storage engine via a single serialized request interface. Capture request/ownership/sequence/completion and byte ranges independently over JTAG. Then expose the reviewed APF crossing directly in a separate experiment to isolate the added transport boundary.
4. Replay identical settings-sized records and all damaged/blank/conflict/overflow cases. Use separate tests for instruction cache fetch, data cache publication, endian conversion, byte strobes, held Wishbone beat/registered ACK, sequence wrap, stale DONE and delayed completion after timeout. Issue no second owner while busy.
5. Qualify reset between commands first; independently model reset while outstanding before any hardware interruption. Fail closed without overwriting forensic records or releasing a timed-out payload.
6. Freeze new sources, simulate, review native UI, compile/qualify every corner/resources and only then program hardware. Existing B005/B006 histories and files must remain preserved.
7. Add Tau's memory sources and playback load one at a time; derive permitted save cadence from measured FIFO margin and command occupancy. Full Tau playback and real power-loss qualification remain later gates in TAU_TEST_MATRIX.md.

No B007 hardware image or CPU-driven persistence claim exists yet.

## Actual generated CPU command simulation — PASS

`python3 sim/test_tau_cpu_card.py --toolchain <RISC-V compiler bin directory>` builds a 276-byte freestanding RV32IM test firmware and executes it on the exact hash-pinned VexRiscv plus Tau crossing. Four clock ratios and a fifth 60 MHz case with three bus wait cycles and a longer modeled APF delay each pass 300 commands: 1,500 total. The firmware samples sequence before GO, tests busy ownership with a second GO, checks every error/selection and wraps the sequence. Instruction fetch uses the actual CPU cache; command MMIO is uncached. Complete local logs/firmware remain under work/sim/tau-cpu and public source/report hashes under work/evidence/tau-cpu-command-simulation.json.

This advances the CPU-execution gate, but uses a small test bus and synthetic APF completion. It does not qualify target payload routing, real serialization, persistence, independent-domain reset, the full Tau SoC or audio playback. Compiler path defaults to the existing read-only sibling toolchain; override it for another checkout. No Tau file/build output was changed.


## Independent reset diagnostic — limitation observed

The isolated exact crossing confirms that rst_sys clears CPU busy before an accepted modeled APF write finishes, and a delayed completion then increments the post-reset sequence. Evidence: tau-cdc-reset-diagnostic.json/.log and sim/tb_tau_card_reset.sv. This is an observed unsupported reset/cancellation condition, not a reset-safety pass. No hardware reset was attempted and Tau remains unchanged. A CPU integration must preserve the payload/parameter owner until actual completion, prohibit fresh requests after a timeout/reset until safe recovery, and define coordinated reset behavior.

## CPU save-format/staging prototype — simulated PASS

`sim/test_tau_cpu_save.py` builds a separate firmware and runs it on the pinned exact CPU/crossing with uncached TX/RX word buffers and modeled bounded APF read/write completion. Eight cases pass: four saves each from clean/blank/corrupt-newest/high-generation states, plus refusal of both-damaged records, guard damage, equal-generation conflict and uint64 exhaustion. Host code independently verifies every final file byte/guard/record/CRC and 64-bit generation; refusal cases preserve all simulated bytes. CPU emits exactly four 128-byte writes and one full 8 KiB verification read per save; parameters/TX words remain owned until genuine completion, with sequence-before-GO and an explicit fence before publication.

This is an isolated C/CPU/bus/format prototype, not a B007 Pocket image. APF copies modeled big-endian words between arrays, with all read words delivered. Real bridge serialization, received-word completeness, cache aliases, reset/lifecycle and audio playback are still unqualified. For production, retain B006's hardware received-word mask; scanning stale guard values alone cannot establish complete transfer. Original command simulations/CPU sources remain unchanged. Source/firmware/full-file hashes and trial outcomes are in tau-cpu-save-simulation.json; private generated firmware/logs remain under work/sim/tau-cpu-save.

## CPU fault diagnostics — expected stops and a completeness gap

Six additional modeled-transport diagnostics completed. Boot command error preserves both files; an error after the first chunk leaves exactly the modeled 128-byte prefix in the inactive file and preserves the last valid file; verification error/returned guard damage stops after a complete new record. A reduced 500-poll timeout diagnostic halts before issuing another command, with the APF request still outstanding. This does not qualify later completion/reset recovery.

The deliberate missing-guard-word test is a limitation: when RX's stale word already equals 0xA5, the original CPU scanner accepts it. Successful record/guard comparisons alone cannot establish complete receipt. Retain this failed robustness expectation in tau-cpu-save-fault-diagnostics.json; it is not counted as a robustness pass. The next prototype adds an explicit per-read received-word lease cleared while idle, with 2,048 distinct received bits required before consuming RX. B006 already enforces the actual hardware mask; a CPU path should retain that mechanism instead of relying on a data scan.

Prototype MMIO/buffer addresses belong to its isolated test bus. In particular, the receive-lease prototype's 0x80000034 register overlaps Tau's PCM status in the full SoC; it must not be pasted into Tau. Tau's real decoder uses a 512-byte MMIO page and has additional peripheral/memory aliases. Full integration requires an audited nonoverlapping map and version interlock, as well as real bridge routing and coherent clock-domain publication.
