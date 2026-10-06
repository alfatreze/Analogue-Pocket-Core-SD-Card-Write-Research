# B008R1 Pocket candidate

[Ordered results](../results/B008_SOC_RESULTS.md) · [Mailbox contract](../research/B008_MAILBOX.md)

## Components and immutable identity

| Component | Implementation |
|---|---|
| Separate Pocket top-level | `rtl/b008_core_top.v`, staged as `core/core_top.v`. Retained upstream physical interface/tie-offs; APF protocol unchanged. |
| CPU | Exact pinned `references/tau-7b98a2e/VexRiscv_Full.v`; RV32IM firmware. |
| CPU bus and RAM | `rtl/b008_soc.sv`: 16 KiB initialized synchronous dual-port-style memory with M10K hint and byte writes. Inference remains a Quartus gate. |
| Firmware | `firmware/b008/`: 528 bytes; SHA-256 `7567fe73eac9245baa9a1b67bf519f9eef13204aa70a775c9fd84310ab05453d`. |
| Command mailbox | Unchanged `rtl/b008_mailbox.sv` from the first gate. |
| APF/payload owner | Unchanged B007R5 `rtl/lab_powercut.sv`; engine clock never follows CPU reset. |
| CPU clock | New `b008_cpu_pll.v`, requested 60 MHz from 74.25 MHz using the pinned Tau fractional PLL parameter interface. Actual rate awaits report. |
| Native screen | Separate `b008_video.sv`, B008R1 title and eleven reviewed states; original B007 renderer preserved. |
| Build/core identity | `cpu08r1` / B008R1 / metadata 0.8.1 / stable `alfatreze.CARDWRITE02`. |
| New fixture | `Assets/cardwrite/alfatreze.CARDWRITE02/cpu-b008.bin`, preallocated 262,144-byte B007-format tag-0 image, APF slot 0x27. Prior files remain protected. |

`tools/prepare_b008.py` refuses an existing stage or package. It validates
source/report/capture hashes and requires the staged firmware bytes to equal
all four interactive trials. Frozen files are indexed in the source manifest;
no source was edited after launch. Package metadata and fixture are prepared
without an RBF. The existing package tool does not yet admit this new build,
which keeps it unavailable for installation until the separate audit is ready.

## Reset, fault and CPU bus

The CPU PLL and APF run state hold the CPU in reset at startup. Reset release
passes through two CPU clock edges. X requests CPU-only reset; existing engine
ownership, buffer data, receive coverage and command completion persist.
The mailbox requests one stop-after-current-write. Firmware drains a pending
mailbox, observes the engine until safely idle, and explicitly recovers; a fault
never causes recovery or retry. Buttons cross through two registers in the CPU
domain. The CPU firmware requires new edges, not held startup buttons.

Unknown CPU instruction/data addresses and firmware-reported failure latch a
CPU fault and reset the CPU/mailbox client; an active engine finishes via the
same stop policy. Simulated test-exit addresses are compiled out of the Pocket
SoC. Firmware changes no target parameter or payload. There is no CPU-hang
watchdog yet; X and APF reset remain the modeled stop/recovery controls.

Mailbox map remains the isolated `0x80010000` page. Additional uncached offsets:
0x30 synchronized buttons; 0x40 heartbeat; 0x44 last response; 0x48 flags;
0x4C last instruction address; 0x50 firmware-ready; 0x5C latched firmware fault.
This map is not approved for full Tau. The high address bit is the CPU uncached
alias for its small RAM; addresses outside that bounded RAM/MMIO fault.

## Clock crossing and timing review

The CPU PLL and engine share clk_74a as their reference. Keep their related
clocks in one timing group; do not mask the whole CPU/engine pair. SPI, clk_74b
and display clocks form separate groups; both pixel phase outputs stay together.
Only mailbox ack1/req1/rst1 and button/debug first stages have false-path
exceptions. Later synchronizer stages remain timed.

Command bits remain stable until response. The destination first synchronizer,
second synchronizer and extra settle cycle defer command consumption. The held
response bundle follows the same pattern in reverse. Only named command/action
and response/snapshot registers receive three destination-cycle setup and two
cycle hold exceptions; these do not relax unrelated CPU/engine paths. Required
register collections must be nonempty or STA fails. See the
[official TimeQuest multicycle syntax](https://resources.altera.com/quartushelp/15.1/analyze/sta/sta_db_set_multicycle_path.htm)
for destination-relative setup/hold options. Post-fit matching, exception
coverage, actual source/destination paths and all corners still need review.

Display telemetry is observation only and may tear while changing. JTAG CPU8
captures a coherent CPU-domain bundle on source bit-31 toggle and holds it until
another toggle. SDW8 separately captures the engine's unchanged B007 diagnostic
format, so the payload magic remains SDW7 despite the new endpoint name. These
are two snapshots at different domain instants, not one atomic combined record.

CPU8 words, most significant first: magic `0x43505508`, heartbeat, last response,
last flags, last instruction address, firmware-ready, fault code, reset/fault
bits. A future collector must validate both endpoints and the build identity.
Do not use the old SDW7 collector unmodified. JTAG requires the Pocket powered
on with the core running; capture before Quit/power-off.

## Pending qualification

1. Complete compile; preserve failed reports as well as successful output.
2. Review RAM inference, ALMs/DSPs/RAM/PLL counts, actual clocks, every STA corner,
   recovery/removal/pulse checks, exception matching and all warnings. Internal
   timing alone does not qualify inherited external APF/scaler/JTAG delays.
3. Record raw SOF/RBF and bit-reversed RBF hashes; require source/UI/simulation
   consistency before making any installable package.
4. Prepare an audited B007-to-B008 updater and SDW8/CPU8 collector; preserve all
   previous output files and create `cpu-b008.bin` exclusively after verifying
   designated card identity, backup and protected inventory.
5. Pocket cold read, CPU-controlled write/clean stop, JTAG before Quit, full
   shutdown/remount and exact host oracle/protected-file check.
6. Separately qualify X/APF reset while idle and live, errors/timeouts and
   cold restart. Active SD power loss and Tau playback remain later gates.

Compilation was launched around 19:46 Europe/Lisbon on 2026-10-06; estimated
finish about 20:31 (range 20:16–20:46). No periodic monitor was restarted.
