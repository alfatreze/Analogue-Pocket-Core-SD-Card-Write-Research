# B008 isolated CPU command mailbox

[Simulation results](../results/B008_RESULTS.md) · [Integration plan](TAU_CPU_INTEGRATION.md)

## Ownership and clocks

`rtl/b008_mailbox.sv` connects an isolated CPU bus to the unchanged B007R5
engine. The CPU requests actions; it never owns the APF bridge, TX/RX buffers,
slot, offset, length, or image tag. B007 alone retains these through real target
completion. A CPU mailbox acknowledgment means delivery/rejection of the
supervisor action, **not completion or durable storage of an SD write**.

The simulation executes the pinned VexRiscv on a nominal 60 MHz clock, with
16 KiB ROM/RAM and uncached MMIO. Engine clock is nominal 74.25 MHz. Commands
and coherent response bundles stay stable through request/response toggles,
two synchronizer stages, and an extra settling cycle. Configuration initializes
the mailbox; CPU reset does not reinitialize its toggles or completion counter.
Hardware needs reviewed CDC constraints, synchronizer placement and timing
before these modeled crossings can be treated as qualified.

## Isolated register map

Byte base `0x80010000` is a simulation address, **not an approved Tau SoC map**.
The CPU Wishbone bus addresses words; the adapter receives byte offsets.

| Offset | Read or write | Meaning |
|---|---|---|
| 0x00 | Full-word write | Command submission. Other byte strobes are rejected. |
| 0x04 | Read | bit 0 pending, bit 1 CPU reset lock, bit 2 local submission error. |
| 0x08 | Read | 32-bit delivered-response sequence, preserved across CPU reset. |
| 0x0C | Read | Last delivered response code. |
| 0x10 | Read | Coherent snapshot: status bits 3:0, error 6:4, idle bit 8, validated bit 9, fault bit 10, synchronized CPU reset bit 11. |
| 0x14 | Read | Completed B007 writes in that snapshot. |
| 0x18 | Read | Loaded image tag in that snapshot. |
| 0x1C | Read | CPU-side rejected submission count. |
| 0x20 | Read | Delivered engine mailbox action count in that snapshot. |
| 0x24 | Read | Local issue: 1 pending, 2 reset lock, 3 malformed submission; 0 accepted submission. |

A held unchanged Wishbone beat is acknowledged/acted on once. A subsequent
changed address/control beat can be acknowledged without requiring CYC to
fall, as observed with the actual CPU. A pending second command is rejected;
it cannot replace the held command or request toggle.

## Commands and responses

| Command | Operation | Acceptance condition |
|---|---|---|
| 1 | Cold read | Engine idle and free of fault/reset. |
| 2 | Start B007 alternating-image write loop | Engine idle with a validated image and free of fault/reset. |
| 3 | Stop after current write | Write arming or active; never interpreted as idle cold-read. |
| 4 | Snapshot | Safe read-only observation, including fault/reset lock. |
| 5 | Recover CPU reset lock | CPU reset released, engine idle and free of fault. |

Delivered response codes: 0 accepted, 1 invalid command, 2 engine busy/wrong
state, 3 cold read required, 4 reset restriction, 5 engine fault. Check local
submission errors separately: a locally rejected request produces no response
sequence increment. Firmware must drain a pending request before submitting anew,
samples the sequence before submission, and waits for its change.

## Reset and timeout policy

CPU reset immediately locks new CPU actions, preserves pending handshake state,
and requests one stop-after-current-write in the engine domain. An accepted
read/write remains owned through target completion. A START still in transit
is rejected if the engine sees CPU reset before delivery. Safe idle recovery
explicitly unlocks the CPU; it does not reset or retry B007.

A B007 target timeout retains its outstanding owner even if DONE later arrives.
Recovery/start remain rejected. Clearing this condition requires a separately
reviewed lifecycle/reconfiguration procedure, not another mailbox command.

## Reproduce the simulation

Run `make test-b008-cpu-engine` from this repository. Requires Python 3,
Icarus Verilog, Verilator with timing support, and the existing read-only pinned
RISC-V compiler under the sibling Tau checkout. Compilation reads that toolchain
but writes all generated files here. Each invocation creates a fresh dated
`work/sim/b008/` directory with source snapshots, firmware, compile/run logs,
whole-file outputs, and failures; public evidence is indexed in
`work/evidence/b008-cpu-engine-simulation.json`.

This deliverable is synthesizable mailbox RTL plus a CPU/ROM/RAM/engine
simulation harness. The harness memory bus and test-exit ports are not a Pocket
SoC implementation. FPGA top-level, CPU clock/PLL, BRAM initialization, native
UI, reset wiring, CDC/STA review, Quartus fit and physical tests remain next.
