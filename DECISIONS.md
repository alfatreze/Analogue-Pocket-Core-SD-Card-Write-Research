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
