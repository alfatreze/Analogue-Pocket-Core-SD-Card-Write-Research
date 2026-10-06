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

## NCW-013 — implement the bounded first batch

B003 uses one preallocated 256 KiB slot 0x23 file, 32 disjoint 8 KiB regions and 38 write/read pairs. The exact configuration lives in experiments/b003.json. A separate Python byte oracle checks all payloads, guards and preserved tails. RTL generates initialized BRAM payloads, holds APF response data until the next read strobe, masks only bytes beyond each read's requested length, and requires receipt of every requested word. Timeout never releases command ownership. Errors and comparison failures remain in retained per-operation logs. B on a fresh launch reads the final expected payloads without writing. One session cannot be accidentally rerun by buttons.

The SDW3 ISSP instance supplies a stable 256-bit indexed snapshot with a toggle/acknowledgement, and optional start/read controls accepted only at READY. Host index changes precede a snapshot toggle; results are read only at a terminal state. This implements the retained-history approach learned from Tau. It adds no SignalTap. Simulation substitutes do not establish physical JTAG or APF timing.

## NCW-014 — preserve and correct the JTAG fabric build failure

Initial batch03 synthesis failed because Quartus's bundled Java 8 JIT received SIGILL under VM emulation while generating alt_sld_fab; the subsequently reported missing entity is a consequence. Preserve that stage/log, do not remove debug logic to hide it. The new exclusive batch03r1 stage uses Java interpreter mode (_JAVA_OPTIONS=-Xint) scoped to the research compile process, removes an inherited stale SLD_FILE reference, and carries a distinct B003R1 screen/version. No Tau source or global VM setting is changed. Full fit/timing evidence is still required before card delivery.

## NCW-015 — audited in-place update of the stable entry

tools/update.py requires exact hashes of the installed minimal02 core and the qualified replacement package. Before mutation it archives prior sources, metadata, SOF/RBF and package; backs up every old active-core file, known catalogue caches and the successful physical write64.bin; revalidates card identity and plan; then replaces only reviewed core files and creates a fresh scratch file. File hashes and protected-content snapshots are verified afterward. An existing batch file, changed old core, changed package or symlink is refused. Cache refresh is backed up and journalled; no prior test output is silently reset.

## NCW-016 — resource evidence requires synchronous RAM output ports

B003R1 did generate the JTAG fabric, but its synthesis report showed TX and retained-log arrays uninferred, with estimated ALMs beyond device capacity. Preserve the partial report and explicitly label the agent-stopped attempt. B003R2 uses dedicated unconditional clocked RAM read registers, then applies address-validity/held-response logic one clock later. The previous-request APF convention is retained and must pass the actual serial peripheral simulation again. ISSP index is held before the snapshot toggle so its synchronous log reads are ready when latched. RAM inference must be checked in the real Quartus report before installation.

## NCW-017 — validate console output, not its process exit alone

Physical System Console returned only its banner with exit 0 when --script ran with closed SSH stdin. Holding stdin open and sourcing the absolute script produced the live SDW3 endpoint and READY signature. Tcl exit is not available in this console. The host now sources the isolated script interactively, captures both output streams, waits for explicit completion, closes stdin normally, and requires a real summary plus start/cold acknowledgement. Any missing/error output fails. No reconfiguration, SOF programming or global VM changes are needed. The first physical 32-case batch then passed all 38 write/read pairs; durable card bytes remain a separate gate.

## NCW-018 — retain the full stress history in bounded RAM

B004 rounds through the proven 32 case regions 10,000 times in total, using each case's maximum B003 length and a visit-dependent XOR over its base pattern. Each adjacent visit changes that region's data, including the single-byte case; small payloads cannot have unlimited unique values. Every operation retains a separate 96-bit flags/write/read record, rather than a rolling summary that might hide an earlier failure. The design needs about 960,000 bits for history plus existing payload buffers; require real RAM inference/resource/timing evidence before installation. SDW4 supplies a coherent 512-bit indexed snapshot plus counts, first failure and extrema. Terminal records cannot be overwritten by button reruns; timeouts never relinquish ownership. The final physical file verifies only the last 32 payloads, with all guards; earlier overwritten payloads have immediate results only.

## NCW-019 — preserve the demonstrated B003 baseline during the next update

The B004 updater requires exact installed B003R2 core hashes and unchanged write64.bin/batch-b003.bin against the collected BATCH-003-COLD snapshot. Include their hashes in the reviewed plan and revalidate them after backups. Archive qualified B003 sources/metadata/SOF/RBF/reports, verify every local backup, create the new scratch exclusively, and compare all unrelated protected files. Do not modify frozen sources or install a prebuilt template if B004 compilation fails. B004 stress and later cold cycles are new evidence; the prior completed baseline remains independently recoverable.

## NCW-020 — respect the actual ISSP width limit without losing result bits

Quartus's local altsource_probe implementation rejects widths above 511. Preserve the first failed B004 stage. B004R1 uses the lower 511 bits of the 512-bit logical packet: only the constant-zero high bit of magic 0x53445704 is omitted, so all counters/flags/timings survive and host unsigned conversion reconstructs the same 16 words. Require physical service width 511 and header revision 1; increment visible banner/version and use a new frozen compile stage. Do not reinterpret mock success as IP qualification.

## NCW-021 — compare global timings against every retained record

The full-history test must reconstruct extrema from all retained operations, in addition to flags/counters. This exposed the original inherited one-clock read-time convention: global extrema used elapsed at DONE, but logs used elapsed one cycle afterward. B004R2 stores read_cycles at the completion edge and uses that value in both summary/history. Error completions receive the same treatment; outstanding timeouts retain elapsed without releasing ownership. Preserve R1's frozen stage and scoped stop evidence; compile a distinctly versioned R2. This is timing-accounting correction, not an observed payload fault or physical fit failure.

## NCW-022 — preserve and publish complete physical stress history

For the first B004R2 physical session, collect all 10,000 retained records while the owner remains powered. Preserve raw and decoded originals privately, and publish the complete decoded history compressed losslessly with zero gzip timestamp alongside a readable summary and raw/decoded/archive hashes. Verify decompression byte for byte and independently reconstruct all global timing extrema. A passing immediate session remains separate from post-Quit whole-file durability, cold reads and interrupted-write recovery.

## NCW-023 — test alternating records before adding the Tau CPU

B005 keeps the latest valid generation in one preallocated file while updating the other in four 128-byte chunks. A 512-byte record validates fixed header, 64-bit nonzero generation, reserved flags, CRC and exact readback; equal-generation disagreement and wrap refuse writes. Commit publication follows full readback, without claiming a flush or physical atomicity. Four controlled pause points permit reproducible prefix interruption experiments. CRC is accidental-corruption detection, not authentication. Keep every failure and require independent raw-file/guard checks and explicit power-action evidence before claiming recovery.

## NCW-024 — retain simulation and card-update evidence separately

B005 passes 36 RTL trials, seven independent host-oracle tests, six mock JTAG tests, twelve mock updater tests, nine mock collector tests and five mock cleanup tests. Tests cover the real pinned command/serial modules, 64 commits, generation carry, prefix recovery/resume, malformed records and permanent error/timeout ownership. Nine native RTL screen states were inspected. Frozen recovery05 sources are compiling independently; physical B005 remains pending. Superseded research cores may be removed only after qualified installation and verified local backups, while every prior output remains on the card.

## NCW-025 — qualify the actual B005 fit and audit cleanup

The frozen B005 stage fits at 32% ALMs, with TX in registers and RX/retained A/history in RAM. Keep this exact implementation and its passing four-corner timing evidence; any later memory optimization needs a new frozen revision. Full compile took 42:23, exceeding the earlier-build estimate; retain actual fit/full timestamps. B004 archives and all package/backup hashes were independently verified after the update. Remove only the two superseded research core directories requested by the owner, preserving every asset/result; use the completed cleanup snapshot for subsequent B005 host comparisons. Physical B005 remains pending.

## NCW-026 — use qualified matching-SOF reloads for connected experiments

Owner requested all feasible development/tests without a card swap. Official Pocket documentation and Tau's verified procedure support FPGA reload with the same core metadata; JTAG chain and qualified SOF hashes are checked first. Preserve full result history and compare it to live terminal state before reload. A separate explicit pause mode permits only known between-command FPGA interruption. Busy/fault/host-mounted states are refused. Record this as FPGA-session recovery, not SD power loss or physical remount durability. First reload read recovers generation 64 with two reads/zero writes.

## NCW-027 — full-file guards and nonblank initialization refusal

B006 reads entire existing 8 KiB files, requires all 2,048 words and intact 0xA5 guards, and accepts initialization only for an exactly blank pair. A damaged nonblank pair cannot silently become generation 1. Unified TX addressing aims to infer RAM; use real reports to qualify it. Existing filenames/record format remain compatible and packages contain no replacement save fixtures. Preserve the first fault-injection harness failure, correct only the testbench and rerun; frozen RTL remains unchanged.

## Connected B006 campaign and pinned Tau crossing (2026-10-05)

The owner requested all feasible tests/development while unable to swap the card for several hours. Continue the bounded B005 campaign, then permit B006 JTAG-only loading only after a completed B005 PASS, matching data/framework ABI, all qualification hashes, exact cable/device and preserved live-state checks. SD stays at B005 metadata while B006 debug image runs; no fixture files are included or reset. Separate B006 tools retain histories and stop on any mismatch. Power interruption and host-remount durability are excluded from this connected-only evidence.

Read-only Tau reference 7b98a2e is hash-pinned; exact copied target crossing passes 1,200 modeled commands across four clock ratios, including stale DONE, busy GO rejection, one-hot selections, error codes and sequence wrap. This prepares integration without editing Tau or claiming CPU/Pocket success. Independent-domain reset and cached-buffer publication remain gates; implementation order is TAU_CPU_INTEGRATION.md. Additional frozen B006 RTL simulation is running over all 513 byte-prefix boundaries, 128 seeded record-bit damages and 16 additional guard corruptions; record actual outcome before counting it.

Actual exact-Tau-CPU firmware execution now passes five isolated modeled-command trials (1,500 total), including delayed registered Wishbone responses and a longer APF completion delay. This extends the previous crossing-only result; it does not test payload routing/card persistence or qualify the full Tau SoC. Full retained source/compiler/firmware/log hashes are in tau-cpu-command-simulation.json. The additional B006 adversarial campaign completed successfully (657 trials, 707 combined RTL total); frozen compile sources remain unchanged.

The exact Tau crossing's independent CPU reset diagnostic observes busy clearing while an accepted modeled APF write remains outstanding, followed by the delayed pre-reset completion incrementing post-reset sequence. Record this as a reset/ownership limitation, not a reset-safety pass. Raw diagnostic and source hashes are retained in tau-cdc-reset-diagnostic.json/.log. No Tau modifications or physical reset were performed. B005/B006 connected reconfiguration remains restricted to verified between-command PAUSED/terminal states; CPU integration must add a coordinated owner/reset policy before testing this boundary on hardware.

B006 full compile completed 17:40:22 WEST and qualifies internally: 4,893 ALMs, 5,078 registers, 18 RAM blocks; worst setup +3.402 ns and hold +0.108 ns across four corners, all TNS zero. Real TX RAM eliminates register-heavy access while full-region validation fits. External APF/JTAG/scaler delays remain incomplete and are not board-margin qualification. Package source/test/display hashes match; no fixture assets. Permit the planned JTAG-only compatible trial after B005 completion, preserving the card's B005 metadata and all old histories. Full audit in BUILD_AUDIT.md.

Actual CPU save-format prototype passes eight modeled-transport cases with independent full-file verification: sixteen saves total across clean, blank, corrupt-newest and 32-bit carry; four refusal cases preserve bytes (both damaged, guard, equal conflict, uint64 exhausted). Uncached word staging makes byte order/publication explicit and does not borrow the APF size table. This is simulation-only and assumes complete modeled reads; B006's received-word tracking remains required for a real CPU transport. No B007 hardware image has been produced. Preserve all prototype/test/firmware hashes.

Prepared the connected remount collector (ten temporary-card tests) and B005-to-B006 updater (sixteen temporary-card tests) for the later owner swap. Exact final model equality, protected-content/snapshot stability and preserved raw host backups are prerequisites to any update. A/B fixtures are forbidden in the candidate package. Backups/archives and post-write hashes preserve every prior result. Tools are prepared only; no real mounted-card mutation is attempted now.

CPU prototype fault diagnostics preserve exact prefix/full-record outcomes and stop on command error/verification corruption/timeout. A deliberately omitted guard transfer is incorrectly accepted when the stale RX word is already A5: retain this as a completeness limitation, not a pass. The original scanner remains unchanged as evidence. Develop a separate received-mask lease variant, mirroring B006's hardware ownership/complete-word requirement. Its isolated MMIO address is not a production Tau allocation; 0x34 is already PCM status and the real page/aliases/version interlock must be audited before integration. No Tau code edits or CPU hardware programming.

## B005 connection stop and console leak (2026-10-05 18:08 WEST)

Stop before further programming on SDW5 claim failure; Blaster USB remains visible but FPGA chain reads fail. Preserve generation-647 last cold PASS, deliberately torn inactive B model and all failed/raw histories. B006 continuation correctly stops before loading. Corrected independent stopped-prefix audit confirms 647 saves, seven FPGA-only interruption recoveries, 17 reads and 3,326 counted commands. The original campaign remains failed/incomplete. Owner power/plug confirmation and physical forensic/remount checks are pending; do not silently repair or reset fixtures.

Old client SSH termination leaks remote consoles. Unique timestamp pairing plus exact PID/start/argv checks identifies 131 B005-owned orphan clients; scoped termination and independent observation close all, freeing about 9 GiB VM RAM. Chain still fails afterward, so cause remains unresolved. Keep unrelated sessions/daemon/hardware unchanged. SDK Tcl exit is unsupported, established by a harmless test; new client closes only its verified owned PID after done markers. Two harmless VM tests, nine host guards and twelve pure reload/load safety tests qualify the new tooling separately; original frozen proof sources remain intact. Actual ISSP through this client remains pending.

Separate CPU received-mask contract fixes the modeled stale-word gap: require all 2,048 distinct bits after idle lease clear and true command completion before consuming RX. Three model cases pass, with missing boot/verify guards stopping 0x23 while preserving latest valid state. Original deficient scanner/counterexamples remain unchanged. Real bridge/CDC/MMIO mapping and physical CPU/Pocket qualification are still required. Initial new-driver syntax error and audit-schema metadata error are preserved as harness-only corrections.

- Preserved a separate hash-verified stopped B005 archive: 624 qualified artifact/history/raw-transport files under work/archives/b005-stopped-20261005. Archive manifest and public verification report retain exact hashes. Rechecked every frozen B006 source, compiled report/bitstream and package file against the qualification manifests: unchanged. No card or FPGA access for this preservation.

- Publication privacy: automatic approval review rejected publishing the broad raw diagnostic set because it exposed local/VM paths. Originals and their hashes remain unchanged in private local archives. Public b005-connected-public-summary.json and console-transport-public-tests.json retain outcomes/hashes with tracebacks and process identifiers omitted. Qualification and replay tools continue to use the exact private originals; a public clone alone does not contain the physical raw history.

- Extend Tau's P0 catalogue with distinct-index completeness, duplicate/stale/out-of-range read data, coherent RX publication, coordinated reset/timeout ownership and MMIO version-map rejection. These gates follow observed prototype gaps and remain planned beyond isolated simulation; do not treat the temporary lease register as production RTL.

- Preserve the slow CPU64 test's global harness-budget failure (302/322 commands at 200 ms) without counting it as a storage pass. Separate R2 changes only the budget to 300 ms; installed timed Verilator completes eight 64-save profiles with exact independent whole-file outputs (512 saves / 2,576 modeled commands). Preserve the first Verilator output-path-space build failure; use a temporary compile directory and copy outputs back. Model CDC/warning limitations remain explicit and exact Tau sources untouched.

## Pocket boot incident — 2026-10-05

Owner reports Analogue logo followed by black screen, persisting after a full power-off and removal of SD, cartridge and JTAG lead. Hardware research remains stopped; cause unknown. Read-only CARDWRITE remount matches the exact stopped B005 file model: A generation 647 valid, B deliberately torn generation 648 invalid, both fixed-region guards intact. Every preexisting protected file matches the cleanup baseline; five added System menu-cache files are recorded separately. Card firmware metadata still 2.7 and SD core metadata 0.5.0; no root firmware update file or debug boot log found. Preserved raw two-slot evidence, full stable file snapshot and hash-verified file-level card backup privately under the boot-incident trial/archive. This does not qualify filesystem metadata or internal Pocket firmware/power/hardware health. Do not resume JTAG programming or change the research card during boot diagnosis.

## Power restored — preserved state and read-only recovery verified

Owner reports successful boot/core start after switching the faulty charging cable and charging. JTAG chain is readable again. B005 freshly started READY with zero operations; requested only read-only recovery, which passed with two SD reads / zero commits, selected generation 647, valid mask 1, raw generations A647/B648, matching CRC. Four real ISSP client sessions closed their exact owned console processes successfully. No FPGA programming or new save occurred.

The prior read-only physical remount matches both complete files exactly, including all guards, and every preexisting protected file matches the baseline. Five added System menu caches are preserved separately. This confirms recovery of the intentional two-chunk inactive-record interruption. The final pre-failure operation was already a completed read-only recovery; the next attempted action failed at status before reprogramming. Exact physical power-loss timing was not captured, so active-write power-loss durability remains unqualified. Failed campaign history stays immutable; no blanket resume or fixture reset. Sanitized outcome: work/evidence/b005-power-return-summary.json; private trial BOOT-INCIDENT-20261005-01 and full file-level backup retain original bytes.

## Resumed connected qualification — 2026-10-05

The failed B005 checkpoint remains unchanged. Separate tools/resume_recovery.py independently replays the failed prefix, checks the physical stopped-file backup and restored read-only endpoint, then journals the remaining point-3 control/cut and final repair. This trial completed: two additional commits, total B005 649, eight between-command FPGA interruption recoveries, final predicted A649/B648 both valid. Exact new physical remount remains pending. work/evidence/b005-resumed-summary.json is the independent proof.

B006 transition uses tools/jtag_load_resumed.py with that completed proof plus original qualified SOF/source/report/package/ABI/live-state/chain gates. The original loaders and failed continuation remain untouched. B006 is now loaded over JTAG with SD metadata still B005/0.5.0. Its first full-region read-only recovery passed at generation 649 with guards intact. The bounded five-batch/one-round campaign is running through the scoped console client. No physical power cuts or fixture resets are performed.

Independent full-sequence checker tools/verify_guarded_completion.py additionally requires all 25 planned events, 325 new saves, four cuts, 24 campaign reload journals and final repaired generation 974. tools/read_guarded_resumed_results.py and tools/update_guarded_resumed.py are separate later remount/update variants; their temporary-card tests pass 11 + 16. The first updater fixture run exposed old summary filenames; corrected only the separate derived updater and retained the failure privately. The running frozen campaign retains a legacy checkpoint filename, so a relative local read alias resolves the separate resumed verifier/collector path without changing source or bytes. Both raw checkpoint paths stay private. No real SD update has been applied.

## B006 completed and installed — 2026-10-05

The fixed Pocket campaign completed all 25 events: 325 new verified saves, four between-command FPGA reload interruption recoveries, 11 read-only sessions and 1,681 counted SD commands. Final generation 974 has valid A973/B974 records. Together with the separately completed B005 trial, this is 974 saves and 12 FPGA interruption recoveries on this card.

The original coordinator failed during its audit after hardware completion because a derived import substitution produced a tuple instead of the model module. Its frozen source, failed transition and completed raw hardware evidence remain preserved. Separate R2 audit tools independently replayed the full sequence and passed; three regression checks passed. No hardware trial was rerun to repair the audit. Reports: work/evidence/b006-connected-resumed-summary.json, b006-connected-resumed-completion.json and resumed-verifier-harness-correction.json. A verified 1,094-file archive preserves the completed campaign and qualification.

Owner quit/powered off and mounted CARDWRITE. GUARDED-006-RESUMED-FINAL01 passed exact whole-file bytes, sizes, generated payloads, CRCs and all guards; every unrelated preexisting file matched the baseline. Five added Pocket menu caches were reviewed, backed up and cleared during installation. tools/update_guarded_resumed.py archived qualified B005 and backed up the current core and all five outputs before replacing only the bitstream, core metadata and info file. B006 version 0.6.0 is installed in the same alfatreze.CARDWRITE02 entry; all package hashes passed and no unexpected file changed. Save fixtures were preserved. Public final evidence: work/evidence/b006-final-card-verification.json.

These results establish recovery for the tested FPGA reload boundaries on one card. Actual loss of SD power, full Tau CPU/bridge integration, multiple-card coverage and authenticated storage remain pending.


## Post-install SD-loaded B006 write and remount — 2026-10-05

After B006 was loaded from SD in a fresh session, one bounded 64-save batch completed with 322 counted SD commands. All 64 retained operation records passed; generations advanced 975 through 1038, leaving valid A1037/B1038 records. Independent model hashes were c66e51605f7b1aaf1584925e61e046301fbd058695558527b9e7ea6e27547e55 and a5d03367ba5cabbff739c229030bb28e0ebafe2e9f0c24b335f1334ac375a3dd.

After a full Pocket shutdown, the mounted CARDWRITE files matched both hashes exactly. Both 8,192-byte files had valid generated records and all guards intact; every unrelated existing file matched the installed-card baseline. Five Pocket menu caches were present. Sanitized evidence: work/evidence/b006-post-install-64-save-summary.json and b006-post-install-64-remount-summary.json. CARDWRITE was safely ejected after read-only verification.

This confirms the tested 64-save session persisted across the observed Pocket shutdown/remount. It does not test abrupt SD power loss during a write.


## B006 power-cycle after a partial-record prefix — PASS — 2026-10-05

At a verified fresh session, B006 pause point 1 completed one 128-byte write command into inactive A for generation 1039, then held in state 14/status 8 with no command outstanding. The owner fully powered off the Pocket at that boundary, restarted it and loaded B006 from SD. The cold recovery passed with valid mask A=0/B=1, selected generation 1038 and no command error. Host remount then matched the exact independently prepared full-file hashes: partial A `53e9757a53df7bfcbb92903008348001e41abc09c98bb34ed68b7547e0a9c6b6`, valid B `a5d03367ba5cabbff739c229030bb28e0ebafe2e9f0c24b335f1334ac375a3dd`. Both files are exactly 8,192 bytes, guards pass, protected files are unchanged and no new files appeared. Evidence: `work/evidence/b006-power-cycle-prefix-jtag-summary.json`, `work/evidence/b006-power-cycle-prefix-host-summary.json` and `work/evidence/b006-power-cycle-prefix-preparation.json`. CARDWRITE was safely ejected after collection.

This demonstrates recovery after full Pocket power-off with a completed partial-record prefix between SD commands. It does not test removal of SD power while a write command is active; that remains pending.

## B007 sequencing and active-write experiment (2026-10-05)

Reserve B007 for an isolated CPU-free active data-slot-write interruption experiment. Move the planned Tau CPU integration to a later separate stage (provisionally B008); do not combine architecture changes with physical power-cut trials. Use a new deferred slot/file, preserve B005/B006 records and B004 stress output, collect JTAG snapshots externally without pausing the core, and cold-recover read-only. Treat 256 KiB as a candidate only: APF file-size capacity does not prove the bridge source window can serve that many bytes. Verify source address range, data stability, byte order and completeness before hardware. Every physical classification requires a full shutdown/remount and independent host hash/content comparison. Manual off timing is not described as precise without measurement. This was the initial design direction; later implementation gates and outcomes are recorded in CURRENT_STATUS.md. No card or FPGA mutation has occurred for B007.

## B007R3 implementation decisions and current gate (2026-10-05)

Use a two-image alternating pattern so a torn active overwrite is distinguishable from the known 0/1 images after FPGA reconfiguration. The file path/slot is unique; B005/B006 data are not reused as B007 scratch. Require an explicit cold read before any write, a 65,536-bit receive-completeness mask, a host independent byte/word oracle, and no retry on command error/timeout. A stop request only relinquishes ownership after APF DONE. The on-screen cut cue requires target ACK and DONE low, and external JTAG samples must corroborate those bits. These are RTL/protocol controls, not proof of persistence.

Current implementation and simulation have passed their stated local gates. After sandbox approval, the launcher checked for other Quartus jobs and started `powercut07r3-s1`; fitter completion and reports are pending. Do not load B007, run a physical interruption, or update CARDWRITE until the exact frozen stage passes full fit/timing/resource/warning review and the B006-to-B007 updater rechecks the exact latest card inventory.

## B007R4 stop-edge correction (2026-10-06)

R3 simulation did not cover a B press during the `ISSUE_WRITE` cycle before target acknowledgement, so that request could be lost. R4 latches the request through command arming and waits for actual DONE before stopping. R4 has passed local simulation, host oracle, JTAG/updater tests, top-level compile, and reviewed display captures. R3's Quartus run is still in megafunction elaboration; it is superseded and must not be installed. Wait for that process to finish before launching the immutable R4 stage. No card write or physical interruption has occurred.

## B007R3 fit failure; R4 compiling (2026-10-06)

R3 fitter placement failed at 46,914 / 18,480 ALMs (254%) and reported 92,968 combinational nodes versus 36,960 available. The finished log and reports are preserved locally in `work/fpga/powercut07r3-s1/`. After confirming the old compile had exited, the separate immutable R4 stage was launched. R4 retains the received-word completeness mask, so FPGA capacity remains a material risk. Await R4 reports; do not update CARDWRITE unless all fit/timing/resource gates pass.

## B007R4 fit failure and capacity redesign gate (2026-10-06)

R4 failed after 2:41:34 at 46,936 / 18,480 ALMs (254%) and 93,013 combinational nodes versus 36,960 available. This matches R3's failure and points to the large 65,536-bit read-coverage mask as a likely capacity driver. Preserve both failed revisions and reports. Do not build or install another B007 revision until coverage bookkeeping is redesigned and simulations still prove full-file completeness and duplicate/missing-word rejection within the actual target FPGA budget. No Quartus process or card update is active.

## B007R5 RAM-backed coverage (2026-10-06)

R5 uses a synchronous 65,536x1 `M10K` bitmap, with direct per-address set writes and a sequential read scan after the target command completes. This avoids a live read-modify-write path and retains missing-plus-duplicate detection through exact count plus exhaustive bit scan. Full-size RTL and package/updater simulations pass. Quartus must confirm block-RAM inference and successful fit before any card work.

## B007R5 FPGA fit success; hardware gate remains (2026-10-06)

Quartus confirms the 65,536x1 coverage bitmap maps to M10K, and the full fit passes at 11% ALM utilization with positive reported timing (minimum +0.123 ns). All 161 warnings were reviewed; no latch or RAM-inference warning was found. The package is locally qualified. This does not authorize treating any physical write as proven: install/control/remount and interruption trials remain outstanding.
