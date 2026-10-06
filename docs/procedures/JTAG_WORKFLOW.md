# JTAG and faster experiment turnaround

## Current status

User identified the programmer as a Terasic Blaster, a supported manufacturer in the official guide. User confirmed physical connection and enabled VM USB passthrough. Read-only chain scan succeeds: USB-Blaster [5-3], ID 02B050DD, 5CE(BA4|FA4). No JTAG programming has occurred in this project. Initial scan before passthrough reported no hardware; both observations are retained locally.

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

## B003R2 retained-results interface

B003R2 updates the same CARDWRITE02 entry and adds **SDW3**, source width 32 / probe width 256. The older minimal02 image has no debug endpoint. `tools/jtag_batch.py status|results|start|cold` accesses the endpoint without programming. Start/cold refuses a host-mounted CARDWRITE volume. The Tcl code selects the exact instance name and widths, checks the FPGA signature and acknowledges each snapshot. Results must be terminal; no transient polling is treated as event history. Tcl semantics are tested with a fake service; physical B003R2 JTAG operation is demonstrated by the first warm batch: all 38 retained records decoded cleanly. Durable file/cold-read qualification remains separate.

Source bits: 31 snapshot toggle; 30 write-session toggle; 29 cold-read toggle; 6:5 ordinal-minus-one; 4:0 case. Hold index stable before toggling snapshot. Write/read triggers are accepted only at READY and ignored during/after a session.

The snapshot contains eight 32-bit words, most significant first:

| Word | Meaning |
|---|---|
| 0 | Signature 0x53445703 (SD write build 3) |
| 1 | Bit 31 snapshot acknowledgement; 30 cold mode; 29 terminal; 28:24 selected case; 23:22 ordinal; 21:14 revision (2); 3:0 status |
| 2 | Four bytes: command count, failed cases, passed cases, completed cases |
| 3 | File offset |
| 4 | Maximum read length / current write length, two 16-bit halves |
| 5 | Flags: 31 completed log; 15 timeout; 13/12 timed-out read/write; 10 comparison failure; 9/8 read/write command error; 22:20 read error; 18:16 write error; 2 comparison pass; 1 read command OK; 0 write command OK |
| 6 | Write cycles (zero for cold read) |
| 7 | Read cycles |

Before a record completes, flags are zero. A timed-out record has bit 15 and retained cycles but not the completed-log flag. While a session is busy, indexed result words are suppressed and the terminal bit is zero. An invalid ordinal also suppresses the indexed result. The host decoder requires all expected completed records and exact clean flags (0x80000007 write/read, 0x80000006 cold read), plus correct offset/length/revision and summary counts. JTAG success is immediate-result evidence, not a physical persistence claim.

The installed Java JIT crashed during first JTAG-fabric generation under VM emulation. `_JAVA_OPTIONS=-Xint` is scoped to the research compiler/System Console process; it changes no global VM settings. Full compilation/timing remains mandatory. API reference: [Intel System Console ISSP commands](https://cdrdv2-public.intel.com/704766/ug-qpp-debug-21-2-683819-704766.pdf).

### Physical console invocation correction

The installed System Console can return banner/exit 0 without running --script when SSH stdin closes at launch. The wrapper now keeps stdin open, sends an absolute source command, captures stdout/stderr, waits for explicit completion, and then closes input. Its Tcl environment has no exit command. An actual revision-checked summary and request acknowledgement are required; a zero process exit alone is never success. The physical first warm batch is recorded in work/evidence/b003r2-physical-jtag-write.json.

## B004R2 retained stress endpoint (physical qualification pending)

SDW4 uses source 32 / probe 511, header revision 2. The constant-zero leading signature bit is omitted physically; decoding restores the 16-word logical packet. `tools/jtag_stress.py status|start|cold|results` follows the proven held-stdin console route, refuses host-mounted-card starts, validates coherent revision/index acknowledgements, and collects every operation before Quit. Result collection has a 15-minute tool deadline because 10,000 held-index snapshots need several minutes. Success requires exact operation ordering, counts, flags, offsets/lengths and extrema reconstructed from retained cycle records. In a failed session, individual clean records remain marked successful; the overall session remains failed. Full packet layout and physical run sequence are in B004_HARDWARE_RUN.md. No FPGA programming is performed.

## 2026-10-05 console lifetime correction

Historical jtag_recovery/jtag_guarded clients are retained as exact qualification evidence, but their SSH shutdown leaks remote System Console processes in this VM. Use the separate `tools/jtag_session.py --build B005|B006 <mode>` for future console access; unchanged Tcl/decoders and all fresh-ready/request gates remain. It requires complete markers, validates signature/revision, records its remote PID/start ticks and closes only that exact client. Tcl exit is unsupported in the installed SDK. `jtag_reload_session.py` and `jtag_load_session.py` add hash-bound client qualification to the existing exact-SOF/preserved-state/cable/device safety gates.

Two harmless live transport tests and host/pure safety tests pass. Real ISSP through the new client is pending. The B005 campaign/continuation stopped when the FPGA chain became unreadable; do not retry the old blanket runner or overwrite its failed evidence. Follow [B005 connected results](../results/B005_CONNECTED_RESULTS.md)'s preservation/restoration conditions and create a separately identified resumed trial. Physical card power/remount checks cannot be inferred from console reconnection or cleanup.

Current B005/B006 resumed workflow: preserve failed histories, require the exact stopped physical backup and restored endpoint, and use resume_recovery.py / jtag_load_resumed.py / connected_guarded_resumed.py through jtag_session.py. Do not rerun existing checkpoints. verify_guarded_completion.py qualifies the entire fixed B006 plan after independent replay. Later remount uses read_guarded_resumed_results.py; the separate updater requires that actual host result and preserved whole-card snapshot. SD metadata remains B005 during JTAG-only B006 testing.

## Completed B006 audit

Use verify_guarded_resumed_r2.py and verify_guarded_completion_r2.py for the separate corrected audit of the completed resumed campaign. Preserve the original failed post-hardware transition and frozen verifier. Raw transport histories are private; a public clone alone cannot reproduce their replay. B006 is now installed on SD; do not use JTAG while CARDWRITE is host-mounted.
