# JTAG and faster experiment turnaround

## Current status

User identified the programmer as a Terasic Blaster, a supported manufacturer in the official guide. User confirmed physical connection and enabled VM USB passthrough. Read-only chain scan succeeds: USB-Blaster [5-3], ID 02B050DD, 5CE(BA4|FA4). No FPGA programming has occurred in this project. Initial scan before passthrough reported no hardware; both observations are retained locally.

CARDWRITE02 has SignalTap disabled. Its SOF can support JTAG reload after compatibility and chain identity are confirmed, but it cannot provide internal SignalTap captures without a separate instrumented build. JTAG does not shorten FPGA synthesis/fitting; it can shorten installation and inspection cycles.

## Confirm setup before using the cable

- Identify the cable/programmer and connector. Analogue supports Intel/Altera or Terasic USB/Ethernet Blaster equipment; a generic JTAG cable is not automatically compatible.
- Confirm the actual Pocket JTAG access and orientation using Analogue's illustrated guide; do not infer a pinout from an unrelated board. The optional cartridge Developer Key is distinct from the rear JTAG interface.
- Route the programmer USB device to the existing Linux Quartus VM. Confirm the cable appears in Quartus and scan the chain with `jtagconfig` before programming.
- Identify the openFPGA target matching the compiled 5CEBA4F23C8 device. Record the observed chain/device IDs and selected position. Do not select a device solely from its ordinal or program a different FPGA.
- Reload only a qualified research SOF while its matching research core is active. Record the loaded SOF hash and core metadata/build. A JTAG reload is a new initialized session, not continuation of the previous FPGA state.

## Instrumented batch build

Create a separately named debug build, retain its timing/resource reports, and preserve its source manifest and SOF hash. Instrument clk_74a signals around:

- one-time boot flag, expected generation, state and boot payload index;
- bridge address/read/write strobes, TX held response and RX write data;
- target request/ack/done/error, parameter address/length and elapsed cycles;
- received-word mask, comparison mismatch and completion counter.

Trigger on target write/read start or a generation/startup mismatch. Capture a short window around the first/last payload reads and completion, rather than trying to record an entire multi-second transfer at full sample rate. Keep a software-visible bounded event log for longer batch history. Instrumentation may change fitting/timing and must be qualified independently.

## Faster card verification

After normal Quit, Pocket Developer USB SD Access can expose the small scratch/results files without physically removing the card. Attach only from the menu, use host read-only verification, safely eject, and detach before resuming the core. Never allow simultaneous host and core filesystem access. This is a useful iteration observation but not the same experiment as power-off/card-remount or a cold-relaunch persistence gate.

## Official references

- [Getting Started](https://www.analogue.co/developer/docs/openfpga/getting-started): approved programmers, connector access, automatic reinitialization after JTAG reload and USB Link.
- [Packaging a Core](https://www.analogue.co/developer/docs/openfpga/packaging-a-core): SOF for JTAG, reversed RBF for SD packaging.
- [Debugging Aids](https://www.analogue.co/developer/docs/openfpga/debugging-aids): Pause Core Boot, Pause Load Data to arm SignalTap, USB SD Access, and debug logs.

JTAG captures establish what the FPGA did. Physical file verification and independent cold/interruption runs establish persistence and recovery behavior.


## Read-only Tau Alpha lessons extracted

References consulted without modifying Tau Alpha: `tau-alpha/docs/procedures/JTAG_DEBUG_ACCESS.md` sections 1–3, 5–6; AUDIT_TRAIL.md B-439/B-444; and the 2026-09-30 Scope-blend handoff.

- The known setup is Terasic USB-Blaster 09fb:6001, UTM USB passthrough, existing VM udev rule, and absolute Quartus 25.1 tool paths. A noninteractive SSH PATH omits Quartus by default.
- Live ISSP register access is hardware-proven in Tau. Use `claim_service issp $path ""`, not `open_service`, and `issp_read_probe_data $claimed` positionally. Select the intended probe by instance ID rather than assuming the first service path is correct.
- Re-selecting a core in the Pocket menu replaces a JTAG debug image with the SD image. Verify the actually loaded SOF identity and reprogram only when intentionally starting a new session.
- JTAG programming loses volatile state and looks like a reboot. A probe requiring firmware changes needs matching SD firmware too; JTAG only changes FPGA configuration.
- Polling transient values was an actual methodological dead end in Tau. Batch outcomes should be latched, with coherent retained snapshots or an event log. Use triggered capture for short transfer phases, not opportunistic host polling.
- Tau's SignalTap work was synthesis-only, not a proven full hardware capture. Its generated configuration once cached stale settings and requested MLAB storage actually used M10K. Inspect resource reports and enabled debug nodes rather than assuming the session file had the intended effect.
- If USB passthrough is visibly present but the scan has no cable, Tau once encountered a stale `jtagd` USB handle after reconnection. Check USB inventory first; daemon restart is a recovery action, not something to do routinely or during another active debug session.

For this project's batch build, prefer a small ISSP control/status block and stable result history first, because Tau provides working evidence for that setup. Add SignalTap only when the retained results leave a specific timing question unresolved. CARDWRITE02 still contains neither facility.
