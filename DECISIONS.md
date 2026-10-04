# Decisions and research history

## NCW-001 — 2026-10-04: minimal core before Tau integration

Decision: use the official target-data example as an independent reference, then a single-clock BRAM/FSM core, then Tau's exact VexRiscv CPU/command crossing, then external memory and playback contention. Canonical fixtures and independent persistent-file verification follow every stage.

Reason: this distinguishes APF/firmware behavior from CPU, CDC, memory or audio workload failures. Starting with a full Tau fork would add too many possible causes and risk repeating previous ambiguous probes. A/B save records and bounded logs are candidate recovery formats, conditional on a proven transport.

Evidence grade: source review and research planning. No new simulation, Quartus build, card write or Pocket validation.

Affected runtime: neither hot nor cold path is changed; project documents only. Next gate: reference fixture/address map and minimal implementation.

## NCW-002 — 2026-10-04: correct the initial evidence summary

The first project's notes omitted the local hardware evidence KB-022/023/025 and audit A-088..090. They also underrepresented the distinction between a missing flush implementation in the stock template and the custom implementation already present in Tau.

Correction: Tau's custom flush timed out; immediate readback after a corrected target write succeeded while the actual file remained zero. Historical parameter changes in A-089 were based on an unverified bitmap interpretation; current official docs define `nonvolatile` and `deferload` as booleans. The research must measure durability independently and must not infer the semantics of a documented flag from the old experiment's prose.

Retain earlier conclusions as superseded where relevant. Evidence remains limited to the described builds/device; installed firmware in the old probe was unconfirmed. See RESEARCH_PLAN.md and the dated local audit for scope.

## NCW-003 — 2026-10-04: implement existing-file probe and independent control

Decision: the first custom bitstream uses no CPU and no external RAM, only a fixed 64-byte target write to one precreated dedicated file. Exclude custom open/flush/nonvolatile paths from this build so an update result has one explanation. Retain the official unmodified target-data example as an independent hardware control.

Sources are pinned in vendor/PINNED.json. The independent byte oracle is manually specified in Python and checks actual RTL-transferred bytes. The template's implicit power-up state and Altera data-table/PLL are explicitly modeled for simulation, so simulation does not claim to validate physical IP or SD firmware behavior.

One compatibility failure was observed: Icarus rejected the vendor command module's data-table declarations after first procedural use. rtl/core_bridge_cmd.v moves those declarations only; the frozen vendor remains unchanged. The first Quartus stage uses the original declaration ordering (Quartus accepts it); simulation uses the reorder. The relevant protocol logic is identical.

Verification: host + RTL simulation passed; eight renderer states captured/inspected. Quartus synthesis passed, full fit pending. No Pocket evidence. Production Tau paths remain reference material; this implements neither a Tau feature nor a durability guarantee.

Build staging correction: the template checkout includes a shipped output_files RBF. The first stage contains it, but collection requires a new successful compile and timing reports, and no prebuilt RBF is allowed as a custom fallback. Future staging excludes output_files/db/incremental_db. Preserve the first stage and its manifest unchanged for audit.

Card install: user identified CARDWRITE as the test card. The official 13-file first-install plan had no replacement/deletion targets or existing catalog caches. Installer checked volume UUID/removability and package hashes, used exclusive file creation, synced and compared protected content. All checks passed; install evidence is retained. Pocket firmware and write/reload results remain pending.


## NCW-004 — compiled probe installed; physical evidence pending

Collected the seed-1 Quartus full compile and its reports. All reported internal timing corners pass; external bridge/scaler I/O delays remain unconstrained and Pocket interface margins are unqualified. BUILD_AUDIT.md records exact identities, resource use and warning limitations. Installed both independent cores on designated CARDWRITE using exclusive new-file creation; package hashes and protected contents verified. Safely ejected the card for CONTROL-001.

The custom installation dry-run exposed a Python variable-shadowing error before card mutation. Renamed the input-label loop variable; corrected dry-run and actual installation completed. No hardware write or persistence result is inferred from host installation, simulation or compilation.


## NCW-005 — first physical write is malformed; fix the measurement core before qualification

FSM-001 changed the physical 64-byte file, but it is exactly a generation-zero record shifted left by one word with a zero tail. Screenshots show successful target command responses, then READ DIFF; expected generation 0 and read generation 0x00010001. The generation-1 oracle remains unchanged and fails this output. Protected baseline files are unchanged.

The payload port currently continuously reads RAM from the current bridge address. In the pinned actual SPI peripheral, outgoing read data is captured before `pmp_rd` is asserted; the official command/framebuffer implementations update responses after a read strobe for a later transaction. The observed one-word shift is consistent with that response-pipeline mismatch. A strobe-driven address/response adaptation is a candidate, not yet reproduced or hardware-qualified. Initial generation 0 is a separate unresolved discrepancy; simulation initializes it to 1 and has no real FPGA startup model.

Do not escalate to CPU integration or infer universal firmware failure. First capture actual SPI transaction timing and deterministic startup in the measurement core, qualify a separately identified build, and repeat physical byte verification. Metadata identifies firmware 2.7; exact shutdown actions and cold reload remain pending.


## NCW-006 — CARDWRITE02 fixes and stronger transfer evidence

The pinned serial bridge explicitly buffers reads by one word. Serial regression using its actual state machines reproduces minimal01's omitted-header shift, while CARDWRITE02's strobe-latched response passes every word against the unchanged independent byte oracle. The serial test also writes all 16 RX words and obtains READ MATCH with the received mask complete. A syntax-only Icarus adaptation is generated outside vendor; its priming response is discarded as required by the pipeline. Direct-command integration and six host checks pass.

Added clocked one-time boot initialization and boot payload construction, and disabled power-up don't-care optimization. This removes reliance on a nonzero declaration initializer for the expected generation; it is not a confirmed explanation for the prior generation-zero hardware result. Intel documents that declared initial values normally synthesize to power-up settings and that don't-care optimization applies to undefined states: https://docs.altera.com/r/docs/683283/18.1/quartus-prime-standard-edition-user-guide/power-up-don-t-care .

Build/package/installer/collector now accept minimal02 explicitly and keep original default identities for historical workflows. The second build has an exclusive frozen stage and separate core/output path. No compiled source is edited after launch. The old build and output remain preserved. NEXT_HARDWARE_RUN.md defines startup, one-write/read, physical-file and separate cold-reload gates.


## NCW-007 — batch the valid transport tests

User requested a more efficient series of write tests. Keep CARDWRITE02 as the already-frozen transport repair gate, then use one automatic batch core with independently addressed records, guard regions and a complete host oracle. Repeated overwrites retain immediate per-operation results but only the final version can be checked on the remounted file. Cold restart and interrupted-write boundaries remain distinct physical runs. BATCH_TEST_PLAN.md specifies the case families and avoids one compile per parameter combination.


## NCW-008 — confirmed JTAG setup and read-only Tau reuse

User identified a Terasic Blaster, confirmed connection to Pocket/computer, and enabled USB passthrough into the existing VM. A read-only scan changed from no hardware to USB-Blaster [5-3], ID 02B050DD, 5CE(BA4|FA4). No FPGA was programmed. Read Tau Alpha's JTAG procedure and historical audits without changing its files or invoking its build tools.

Reuse the proven ISSP service/instance selection procedure for stable batch results; retain per-event history rather than polling transient bus signals. SignalTap was not a fully proven Tau capture workflow, and its cached configuration/RAM-type issues need fresh qualification. Matching core metadata/assets must be installed before a JTAG reload, which resets volatile FPGA state. JTAG_WORKFLOW.md records the exact lessons and official reference links.


## NCW-009 — CARDWRITE02 qualified for its physical trial

Collected the successful 17:25 full compile, complete reports, RBF and SOF. All reported internal timing corners pass (setup +4.169 ns, hold +0.150 ns); report confirms power-up don't-care disabled. Same inherited external I/O constraints limitations remain. Installed the separate qualified package with hash verification, protected-file comparison and backed-up catalogue-cache refresh. Original failed output and screenshots unchanged. Next action is the user-operated startup/A/B/normal-Quit run in NEXT_HARDWARE_RUN.md. No physical success is claimed for CARDWRITE02 yet.


## NCW-010 — confirm the active core before interpreting a repeat

The next supplied screenshots still show LAB 01; lastcore.bin names CARDWRITE01. CARDWRITE02's installed code/metadata hashes match its package and its dedicated output remains all zeros. The collector was initially invoked for minimal02 based on the intended procedure; its immutable output is retained, and observations.json records why it is not a valid corrected-build trial. Explicit Developer > Builds selection and the LAB 02/generation-1 startup gate are required for the repeat. Do not change the corrected RTL based on this wrong-build observation.


## NCW-011 — repaired transport passes its first physical byte oracle

FSM-002-R1 produces the exact generation-1 record on the remounted physical card and screenshots show LAB 02 with READ MATCH. Retain the strict collector's inconclusive flag and append explicit review: its only protected differences are lastcore/recent runtime records identifying the deliberately selected CARDWRITE02. Other protected bytes are unchanged. This is a single existing-file success, not robust/repeatable qualification. Advance to cold B-only reload and batch transport work; keep fault-boundary and cross-card tests separate.


## NCW-012 — stable launcher, distinct build identity

Owner requested distinct build naming without repeatedly selecting a new core. Future delivery uses one persistent active card core (currently CARDWRITE02), updated in place with backed-up prior artifacts, and uniquely numbered versions/descriptions/screen banners. This avoids the old-core resumption problem caused by adding a separate menu entry for each compile. Existing first-install tooling must gain an audited update path before this convention is used; no card change is made during the pending cold-reload observation.
