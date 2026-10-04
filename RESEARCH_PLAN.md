# Research plan: reliable SD writes from an Analogue Pocket core

Prepared 2026-10-04. Planning and source review only; no new hardware experiment has been run.

## Research question and possible outcomes

Can a Pocket core write its own persistent data, recover correctly, and leave Tau's music and other card contents untouched, repeatedly under a defined set of conditions?

Report capabilities separately rather than a single yes/no:

| Capability | Required evidence |
|---|---|
| Clean-shutdown persistence | Exact bytes survive normal Quit and cold relaunch. |
| Runtime persistence | Exact bytes survive a completed runtime update and a cold restart without relying on later Quit writeback. |
| Recovery from interrupted update | A restart selects a complete valid old or new record; never a mixed record. |
| Protection of unrelated files | Pre/post file manifests and hashes match outside the approved output files. |
| Suitability during playback | No added audio underruns; command latency and memory use fit measured Tau budgets. |
| Broad repeatability | The above results reproduce across the declared firmware, card, filesystem and build matrix. |

Security here means bounded destinations and sizes, correct slot ownership, validation of loaded data, and preventing collateral writes. A checksum detects accidental damage; it does not authenticate hostile modifications. Authentication/encryption is a separate feature if Tau later requires it.

A positive result may support only small saves on clean Quit, or only saving while paused. That is still useful. Do not claim unconditional power-loss safety or universal card compatibility from a finite test campaign.

## Evidence that changes the starting plan

Tau's local evidence is stronger and more cautionary than the initial project summary:

- A-088/A-090 and KB-023: fixing the BRIDGE source from `0xF8000000` to `0xF8002000` made an immediate target read return the written signature. The physical file still held zeros. Immediate readback is therefore an insufficient persistence oracle.
- A-090 and KB-022: a custom `0x0188` implementation waited 10 seconds without completion; the next read also timed out. The installed Pocket firmware version was not confirmed. Reproduce with trace evidence before generalizing.
- `fw/settings.inc` reports earlier library damage and hangs, and names overlap between a filename response structure and the APF slot-size table as a historical cause. The comments are a reason to isolate tests and audit address ownership, not proof that every correctly implemented target write is broken.
- A-089's historical note treated `parameters` bits as nonvolatile/deferload flags. Current official docs define those as separate JSON booleans. Use the actual documented fields; retain the old experiment as evidence with a configuration uncertainty.
- Tau currently uses `VexRiscv`, the target command crossing in `tgt_cmd.v`, a sequence counter for real completions, and APF Interact persistence for settings. Production `data.json` currently exposes media/firmware/assets slots without a dedicated output slot. A test variant must introduce one explicitly.

Official documentation defines target open/write/flush operations and nonvolatile slots, while the official kbmouse example supplies a useful reference control. Neither establishes durable behavior on our current hardware by itself. See the source links below.

## Proposed sequence

### Phase 0 — freeze the protocol, fixtures and observability

Give this project its own platform and core IDs, for example `cardwrite` / `alfatreze.CARDWRITE`, and a dedicated output root. Validate identifiers before packaging. Use only sacrificial cards with synthetic music and unrelated sentinel files. Keep source fixtures and the expected file manifest on the computer.

Freeze one manifest per experiment: source revision, build flags, CPU configuration if present, JSON files, RBF/ROM hashes, Pocket firmware, required framework, card model/capacity/filesystem/cluster size, initial files, operation sequence, PRNG seed, and expected output. Record slot position and ID separately.

Use a small deterministic record: magic, format version, payload length, generation, test ID, payload, and checksum. Initially 64 bytes, then 512 bytes and 4 KiB. Use an independent host verifier that checks every byte and exact file length, not merely the record's own checksum.

Observe request, acceptance, completion, result, sequence number, timestamps and BRIDGE address/length. Keep trace/output evidence outside the SD-writing path being tested: on-screen snapshot plus host capture, JTAG or external logging where available. Do not depend on the new file writer to report its own failure.

Audit staging addresses before hardware: payload memory, command structures and the 32-entry size table must not overlap. The reserved table occupies `0xF8002000..0xF80020FF`; any scratch use elsewhere needs its own explicit address map and bounds. Keep parameters stable until completion.

Gate: fixture oracle and protocol implementation reviewed; relevant RTL simulation passes; the compiled build meets timing; packaged bitstream hash matches. No production integration yet.

### Phase 1 — establish an independent reference control

Run the official `core-example-kbmouse-targetdata` behavior using its documented configuration. Its Select action saves `saved.bin`, and Start reloads it. Inspect the file on the computer after Quit and after a cold restart. Keep the example configuration unchanged for the control; place it only on the sacrificial card.

If it fails, first establish whether the same failure occurs on another card and supported firmware. If it succeeds, preserve the exact source/JSON/build as a comparison point. Do not spend rounds modifying Tau before determining whether the reference can persist bytes on the same device.

### Phase 2 — minimal custom core, no CPU

Use a small BRAM payload in the BRIDGE clock domain and one serialized FSM. Avoid SDRAM, PSRAM, caches and playback in the first build. Reuse a reviewed APF command implementation with preserved source/license notices; keep payload routing explicit.

Compare these mechanisms in separate builds or strictly isolated runs:

| Order | Method | Main question |
|---|---|---|
| 1 | `0x0184` to a dedicated, existing deferload file | Can the simplest runtime write persist without `0x0188`? |
| 2 | `0x0192` create/open then `0x0184` | Does first-file creation differ from update of an existing file? |
| 3 | Nonvolatile slot with BRAM readback on normal Quit | Can APF shutdown writeback work with correct fields, address and table size? |
| 4 | Missing nonvolatile file, initialization bit 5 off/on | Is missing-file initialization sufficient to produce the first save? |
| 5 | Explicit `0x0188` after a proven write | Does it complete, add durability, or block the channel? |
| 6 | Slot reopen/rebind followed by an independent read | Does observed data survive eviction/reopening rather than just same-slot caching? |

For methods 1–4, check after immediate read, reopening where applicable, normal Quit, and cold power cycle. Use separate runs to avoid one lifecycle action concealing another mechanism's failure. Check full host-read file contents after each relevant boundary.

`0x0188` gets a finite diagnostic budget: one traceable reproduction and one justified alternative configuration. If it still blocks, classify it unsupported for the tested scope and continue with other paths. A local timeout does not cancel an APF command: freeze the payload, prohibit new commands and require a known safe recovery/restart. Never clear local busy and reuse parameters while completion could still arrive.

Gate: one method survives 100 clean independent reopen/restart cycles with exact file results and no unexpected changes. Classify its lifecycle limitations before proceeding.

### Phase 3 — recoverable formats and alternative approaches

Once a raw write path works, test improvements independently:

| Candidate | Purpose and decision |
|---|---|
| Fixed preallocated file, bounded updates | Reduce allocation/truncation during ordinary saves; still test real filesystem/card behavior. |
| Two precreated files, alternating generations | Keep the last valid record while updating the other. On boot validate both and choose the newest valid generation. No rename API or third selector file required. |
| Two records in one preallocated file | Compare speed/complexity with separate files; account for shared sectors and one shared directory entry. |
| Append-only fixed-size record ring | Useful for logs; validate records individually, recover the valid prefix/latest generation, define wrap and retention. |
| Commit marker written last | Compare with checksum-only recovery. The marker itself is not assumed atomic or durable. |
| Bounded chunks with yield points and coalesced saves | Reduce command monopolization, slot switching and write frequency. Measure whether this actually helps playback. |
| APF Interact fallback | Preserve current settings/compact diagnostics if file writing remains unsuitable; finite field budget and signed-value behavior remain constraints. |

A/B and journal designs improve application recovery only if writes to one area do not corrupt the other. They cannot guarantee that a consumer SD card preserves filesystem metadata during power loss. Test this limitation explicitly.

Chip32 can be investigated for boot-time file setup if that becomes a measured problem; the documented file-process page is not evidence of a general runtime write/durability API. Raw SD access, direct FAT mutation and undocumented commands are outside the first campaign: the documented core interface is APF and no supported raw-sector path has been established.

Gate: state format rejects damaged/truncated records, recovers old/new state consistently, and passes all planned interruption points on sacrificial media.

### Phase 4 — the same CPU and command path as Tau

Add the exact VexRiscv generated RTL and configuration from a pinned Tau revision, using Tau's default 60 MHz configuration unless a selected build proves otherwise. Reuse the winning BRAM transport and canonical operation sequence initially; retain the no-CPU build as a differential reference.

Then introduce one boundary at a time: MMIO command registers, `tgt_cmd.v` crossing/sequence handling, BRAM CPU writes, uncached PSRAM/SDRAM staging, then any relevant cached aliases. Do not assume a CPU address is a BRIDGE-readable address, or that a dirty cached buffer is visible to APF. Define ownership and explicit publication before GO, and preserve the source until genuine completion or restart.

Test stale DONE, back-to-back commands, sequence wrap, held Wishbone beats/registered ACKs, reset during commands, delayed completion after timeout, and competing request sources. Use exactly the same payload corpus and expected outputs as Phase 2.

Gate: CPU and FSM versions produce identical persistent outputs and error behavior; no missing/duplicate commands; supported memory sources pass.

### Phase 5 — Tau workloads and qualification

Use an isolated Tau-like diagnostic core with synthetic assets and the existing CPU, firmware load, decoder, audio FIFO, visualizers, cold image and memory arbitration. First save while idle/paused, then during representative playback, then during worst supported measured workload. Stage the output slot separately from every input slot.

Qualify the first actual use case: settings/custom meter configuration. Follow with resume/bookmarks and compact diagnostic records; only then evaluate growing logs and large exports. Host-owned music, library index, cold image and asset packs remain protected inputs.

If saving during playback breaks audio deadlines, support paused/idle saves and publish that restriction. Measure the longest command occupancy, CPU stall, FIFO margin, added underruns, RAM/stack use, and BRIDGE traffic before choosing save frequency/chunk size. Do not invent a universal millisecond limit; derive it from the actual FIFO reserve and worst decoder workload.

Gate: [Tau test catalogue](TAU_TEST_MATRIX.md) passes for the declared capability and environment, with unresolved exclusions documented.

## Qualification and stop rules

Start with 100 small restart cycles for discovery. Qualification targets at least 10,000 mixed runtime update/read operations, 1,000 clean Quit/cold-relaunch cycles across the campaign, and at least 20 repetitions at each reproducible interruption boundary for the selected recovery format. Runtime operations are not counted as independent cold durability trials.

Use at least three cards from two manufacturers, with both FAT32 and exFAT where the tested configuration supports them, and at least two filesystem allocation/fragmentation conditions. Test the confirmed current firmware and one additional supported version if available. Results for untested firmware, cards or Pocket units remain unqualified.

Zero observed failures is evidence, not proof. Under an independent identical-trial assumption the approximate 95% upper failure probability is 3/N; correlated operations on one card do not satisfy that assumption. Retain per-card and per-lifecycle counts rather than announcing one misleading pooled reliability number.

Stop a run immediately on an unrelated-file change, filesystem damage, incorrect slot/path, unbounded wait, malformed output accepted as valid, or a write to a protected input. Preserve evidence, reproduce on a restored disposable fixture and identify the cause before expanding the matrix. Do not repair the failing image before preserving it.

Final report should be one of: suitable for clean Quit only; suitable for runtime saves while idle; suitable during playback; recoverable under specified interruption tests; or insufficient evidence/unsuitable. List limits and all excluded tests.

## Sources and next concrete step

- [Analogue host/target commands](https://www.analogue.co/developer/docs/openfpga/host-target-commands): command parameters, file open/create/resize and data-slot table.
- [Analogue data.json](https://www.analogue.co/developer/docs/openfpga/core-definition-files/data-json): nonvolatile/deferload booleans and parameter bitmap.
- [Official target-data example](https://github.com/open-fpga/core-example-kbmouse-targetdata): reference control.
- [Chip32 file process](https://www.analogue.co/developer/docs/openfpga/chip32-vm/file-process): optional boot-path investigation only.
- Local Tau references: `fw/settings.inc`, `src/fpga/core/tgt_cmd.v`, `src/fpga/core/core_bridge_cmd.v`, `src/fpga/core/mp3_soc.v`, `dist/Cores/alfatreze.TAU/data.json`, and audit A-088..A-093.
- Local skill evidence: KB-001/003/005/007/022/023/025/074/076. Preserve the status and scope of each claim.

Next implementation: freeze the source/build of the official example, prepare an independent payload/file verifier and sentinel manifest, and specify the minimal BRAM core/address map. Hardware execution begins after those artifacts exist. This plan does not claim any newly validated method.
