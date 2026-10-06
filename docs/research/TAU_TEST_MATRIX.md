# Tau Alpha card-writing test catalogue

2026-10-04. Planned tests, not test results. Activate the full catalogue only after a method passes the minimal-core persistence gate in [RESEARCH_PLAN.md](RESEARCH_PLAN.md). Execute transport/security tests earlier as appropriate.

## Tau needs and priority

| Use case | Actual need/reference | Qualification target |
|---|---|---|
| Settings and custom meter configuration | `fw/settings.inc` already uses APF Interact; custom hand-tuned meter values lack a complete persistence path. | Small structured saves, stable IDs, safe migration, no music changes. |
| Resume and future bookmarks | `fw/player.c`, `fw/settings.inc`; library identity guards in library spec. | Correct track/time/context, reject stale library identity, bounded save frequency. |
| Diagnostic summaries | KB-025/A-091..093 show compact Interact records; larger file records could remove field-budget pressure. | Exact independent decoding; report a writer failure without relying on that writer. |
| Optional session/performance logs | Settings architecture proposes dedicated `/Saves/tau/` output. | Bounded growth/rotation, low overhead and recovery. |
| Optional screenshot/export | Settings architecture currently defers runtime export. | Large chunked writes only after small saves qualify; optional capability. |
| Music, playlists, index, cold code, asset packs | Inputs consumed by Tau; current packaged slots include these assets. | Preserve byte-for-byte. Editing these inputs is not needed to qualify own-state writing. |

P0 = required for any method shipped in Tau. P1 = required for the relevant feature or operating condition. P2 = expansion beyond the first use case. A failure can remove a capability from the supported scope; do not silently turn it into a pass.

## Common oracle and corpus

Record command count/results, expected/actual full file bytes and length, host SHA-256, generation and record validation, cold reload result, output file allocation, and an unchanged manifest of all protected files. Capture filesystem consistency without modifying it after interruption tests. Preserve a failing card image before repair/reformat where practical.

Payloads: all-zero, all-ones, alternating bits, byte ramps, distinct per-word/per-sector patterns, seeded pseudorandom bytes, and generation-dependent values. This exposes byte order errors, shifted reads, stale buffers and repeated blocks. Each result includes a seed and a replayable operation trace.

Size corpus: 0, 1, 2, 3, 4, 7, 15, 31, 63, 64, 255, 256, 511, 512, 513, 4095, 4096, 4097 bytes; then 65535, 65536, 65537 and 66048 bytes (the community-reported 64 KiB boundary). For every actual supported maximum and filesystem cluster size C add max−1/max/max+1 and C−1/C/C+1. Invalid cases must be rejected by the application before issuing a write.

Use full Cartesian coverage for the small defined record-format/validation state space and deterministic command race cases. Use pairwise environment coverage plus specifically risky combinations for larger matrices, then seeded operation-sequence fuzzing. “Exhaustive” means complete coverage of the declared boundaries/invariants, not every possible card, byte string and failure timing.

## Protocol, addressing and persistence

| ID | Priority | Test | Required result |
|---|---|---|---|
| W01 | P0 | Known existing file: one 64-byte write. | Exact bytes/length after host remount and cold core reload. |
| W02 | P0 | Create absent file using supported create path; repeat when it exists. | Expected create/open status; no unrequested truncation. |
| W03 | P0 | Nonvolatile slot with existing file, normal Quit. | Correct memory readback and persistent file; apply only if this path is supported. |
| W04 | P0 | Missing save, initialization bit 5 off/on in separate runs. | Explicitly characterize first-file behavior and size; no hang. |
| W05 | P0 | Slot IDs different from their positions; reorder slots. | Correct ID selected and correct position-indexed size word. |
| W06 | P0 | Read back table before/after open/write/resize. | Only expected table entries change; command structs never overlap it. |
| W07 | P0 | Run payload and size corpus, including first/last bytes. | All supported cases exact; unsupported sizes bounded and rejected. |
| W08 | P0 | Partial overwrite at start/middle/end and word/sector/cluster boundaries. | Only specified range changes; guards and untouched tail match. |
| W09 | P0 | Write same bytes repeatedly, then new generations. | No duplicate/omitted operation or stale result; no accidental resize. |
| W10 | P0 | Same-slot read, reopen read, Quit/relaunch, cold restart in separate runs. | Durability boundary identified; cache-visible data alone never counted as durable. |
| W11 | P0 | `0x0188` with full trace if used. | Genuine bounded completion plus persistence; timeout freezes further requests until safe recovery. |
| W12 | P1 | Resize smaller/larger/zero and regrow. | Documented size/content policy; no stale tail accepted as current data. |
| W13 | P1 | Alternate two slots, reopen files and query filenames. | Correct binding, size and file contents despite slot-cache changes. |
| W14 | P2 | `0x0185` / offsets beyond 32 bits. | Only if a real need exists; correct high bits/framework/format, bounded arithmetic. |

## Security, destination protection and invalid inputs

Tests against invalid paths use only synthetic files on disposable media; an application allowlist should reject them before APF sees them. Bypassing that guard to probe host behavior is a separate diagnostic build.

| ID | Priority | Test | Required result |
|---|---|---|---|
| S01 | P0 | Snapshot hash manifest of music, playlist, index, firmware, cold image, art/assets and other synthetic cores. | Every protected file unchanged after each campaign/run boundary. |
| S02 | P0 | Attempt GO with a media/input/undefined slot ID. | Rejected before transfer; output remains within dedicated slot. |
| S03 | P0 | Read-only slot, zero/oversize length, offset+length overflow, out-of-range BRIDGE source. | Checked failure; no mutation, no memory exposure. |
| S04 | P0 | Paths outside allowlisted output root: `..`, absolute alternate root, repeated separators, embedded NUL, malformed/missing terminator. | Reject before open; no unintended target binding. |
| S05 | P0 | Path limit, extension/case variants and same-name collisions. | Deterministic identity and rejection rules; no ambiguous overwrite. |
| S06 | P0 | Writable slot binding changes through user reload/instance/config. | Writer checks expected binding or prevents reassignment; refuses stale destination. |
| S07 | P0 | Initialized payload surrounded by memory canaries; short payload in larger staging buffer. | Exact intended length; no uninitialized memory in output, no buffer overwrite. |
| S08 | P0 | Malformed JSON slot configuration, wrong boolean vs bitmap interpretation. | Package validation fails or clearly reported boot failure; never silently proceeds with uncertain configuration. |
| S09 | P0 | Full card / insufficient space / absent parent / missing or replaced file. | Bounded failure, last valid state preserved where supported; no success notification on failure. |
| S10 | P0 | Corrupt record header/length/type/version/checksum and malicious value ranges. | Parser checks bounds before allocation/use; invalid state falls back safely. |
| S11 | P1 | Request rapid saves from multiple controls/features. | One command owner; requests queued/coalesced with explicit limits. |
| S12 | P1 | Application “cancel” after issue and late completion. | No claim of rollback/cancellation; source and parameters remain owned until genuine completion/restart. |

## CPU, BRIDGE and memory correctness

| ID | Priority | Test | Required result |
|---|---|---|---|
| C01 | P0 | Replay canonical corpus on FSM and exact Tau VexRiscv build. | Identical files, outcomes and mutation boundaries. |
| C02 | P0 | Stale DONE high before issue; back-to-back issue/poll. | Sequence advances only on genuine completion; no false immediate success. |
| C03 | P0 | Sequence counter rollover and long-delayed completion. | Each operation matched once; wrap does not misidentify an old request. |
| C04 | P0 | Issue while busy; mutate command selection/parameters during ownership. | Second issue refused or serialized; accepted parameters stay stable. |
| C05 | P0 | Registered ACK and a held Wishbone beat. | Exactly one transfer, not a duplicate beat (regression tied to A-093/KB-024). |
| C06 | P0 | Back-to-back BRIDGE reads with changing addresses; first/last word. | No one-word shift, repeated word or stale return. |
| C07 | P0 | Both clock phases/ratios, reset timing and CDC pending work. | No lost/duplicate request/completion; all data published before use. |
| C08 | P0 | Firmware timeout while APF remains busy; next request; late completion. | Explicit fault state and safe restart; no reuse of live payload. |
| C09 | P1 | BRAM, uncached PSRAM and SDRAM sources independently. | CPU checksum, BRIDGE view and persistent output match for supported mappings. |
| C10 | P1 | Dirty cached alias versus uncached BRIDGE view. | Publication protocol prevents stale data; unsupported alias rejected. |
| C11 | P1 | CPU/DMA/decoder attempts to alter active write buffer. | Ownership prevents alteration; output is one coherent generation. |
| C12 | P1 | Near RAM/stack/heap limit, reset during load, last write still in CDC queue. | No overrun/early consumption; feature disabled on memory proof failure. |

## Recovery and interrupted updates

| ID | Priority | Test | Required result |
|---|---|---|---|
| R01 | P0 | Empty/one-valid/two-valid/two-invalid A/B records. | Deterministic valid-record selection or safe defaults. |
| R02 | P0 | Torn header/payload/checksum, valid header plus short file, mixed generations. | Invalid record rejected; previous valid record retained. |
| R03 | P0 | Equal generations, rollover and corrupted implausible generation. | Defined tie/order policy; no corrupted value wins by magnitude alone. |
| R04 | P0 | Cut/update interruption before issue, during transfer, after completion, before verification and before commit indication. | On restart old or new valid state only; classify any filesystem/collateral damage. |
| R05 | P0 | Normal menu entry/Quit/power-off at each relevant state. | No deadlock; documented persistence boundary; state matches observation. |
| R06 | P1 | Controlled hard power loss/removal at repeated/random delays on sacrificial media. | Record recoverability and filesystem integrity; scope excludes unsafe outcomes. |
| R07 | P1 | Sleep/wake during dirty/pending state. | Only if core declares support; current Tau package declares `sleep_supported:false`, so initially N/A. |
| R08 | P1 | Grow/create/resize failure versus preallocated overwrite. | Compare collateral damage and preservation of last state; choose measured safer policy. |
| R09 | P1 | Log ring wrap, full record area, truncated last record. | Valid recovery and bounded retention; no overwrite of protected files. |
| R10 | P1 | Retry after error with same logical generation. | Idempotent policy or explicit new generation; no duplicated log/event masquerading as one. |

## Tau functional and performance qualification

| ID | Priority | Test | Required result |
|---|---|---|---|
| T01 | P0 | Save/reload all supported settings and custom meter values, min/max/default. | Exact values; stable IDs; unknown/out-of-range values fall back. |
| T02 | P0 | New/old format, firmware upgrade/downgrade, unavailable meter/preset. | Explicit migration/rejection; no setting silently mapped to a different meaning. |
| T03 | P1 | Resume after MP3/FLAC seek, track change, playlist change and standalone file. | Correct context/time under defined accuracy; standalone behavior follows Tau policy. |
| T04 | P1 | Library rebuilt/reordered, track removed, card swapped and namespace changed. | Stale resume/bookmark rejected using identity; never resume wrong track. |
| T05 | P1 | Latest diagnostic record decoded independently on host. | Build/test identity and data exact; writer failure still observable elsewhere. |
| T06 | P1 | Idle versus pause versus ordinary/worst supported MP3 and FLAC. | Zero added underruns relative to clean baseline; latency/FIFO reserve recorded. |
| T07 | P1 | Supported stereo bitrate, mono speech, Cymo/tempo, EQ, visualizer and cold-code contention. | Writes satisfy measured budgets or are deferred while these workloads run. |
| T08 | P1 | Save at track refill/seek/art load/library open/slot switch. | No lost media reads, wrong binding, audible disturbance or playback stall. |
| T09 | P1 | Slider held/repeated changes, rapid navigation and pause/unpause. | Coalesced writes retain final state; documented maximum save rate. |
| T10 | P1 | Worst-case command latency, fragmented card, nearly full card. | Bounded behavior; saving does not exceed actual audio buffer reserve when enabled in playback. |
| T11 | P1 | Session logging enabled/disabled; retention cap and counter rollover. | Bounded storage/CPU/memory; no logging feedback loop. |
| T12 | P2 | Screenshot/export in chosen actual encoding and size, chunked cancellation/interruption. | File decodes independently; partial export recognized; source assets unchanged. |
| T13 | P1 | Host-only card edits between core sessions and newer unknown save schema. | Revalidate at boot; never overwrite an unrecognized save without defined policy. |

## Environment and long-run campaign

| ID | Priority | Test | Required result |
|---|---|---|---|
| E01 | P0 | Confirmed current Pocket firmware, framework minimum and packaged build identity. | No ambiguity about which implementation was tested. |
| E02 | P0 | Three cards/two makers; FAT32/exFAT where supported; multiple cluster/allocation conditions. | Per-environment qualification results; incompatibilities declared. |
| E03 | P1 | Another supported firmware/Pocket unit where available. | Version/unit effects recorded; unavailable combinations marked unqualified. |
| E04 | P0 | Clean, fragmented and nearly-full fixture; dense directory and AppleDouble junk. | Correct destinations and bounded behavior despite host-created files. |
| E05 | P0 | 10,000 mixed operations and 1,000 Quit/cold-relaunch cycles across campaign. | No silent corruption, unintended changes, false successes or stuck channels; counts per environment retained. |
| E06 | P0 | Seeded sequences of create/write/read/open/fail/restart/save. | Every sequence independently verified and replayable; any minimal failing sequence retained. |
| E07 | P1 | Build with changed fit seed or timing/resource conditions. | Timing closes; canonical suite repeats, avoiding reliance on one marginal fit. |

## Running and reporting

Each test instance records ID, phase, applicable method/build, environment, payload/seed, expected behavior, observed bytes/status, evidence path and verdict. A test is N/A only with an explicit reason (e.g. sleep unsupported or export not implemented). Missing hardware evidence is pending, never pass.

Required suite for initial settings writing: applicable P0 tests plus T01/T02/T09/T13. Add all playback P1 tests before enabling saves while playing; add resume, logging and export tests as those features enter scope. Interruption-recovery claims require R04/R06 for the claimed conditions.

The final report links each supported capability to completed test instances and lists failures, exclusions, card/firmware coverage, resource/timing results and remaining uncertainty.

## Evidence update — 2026-10-05 connected interval

The catalogue above remains the required scope, rather than a blanket pass. Current evidence narrows several gates:

| Gate | Evidence achieved | Still required |
|---|---|---|
| Repeated physical saves | B004 10,000 write/read pairs with host checks; B005 647 committed saves and seven between-command FPGA interruption recoveries | B005 final remount, independently confirmed power cycles and actual card power interruptions |
| Record/guard validation | B006 707 RTL trials and full compile/internal timing qualification | Actual B006 Pocket trial and protected whole-card host comparison |
| Exact CPU command transport | 1,500 commands executed by pinned generated CPU over modeled APF completion | Actual payload bridge, full SoC bus and physical SD transport |
| Exact CPU save format | Eight modeled cases; separate fault diagnostics and received-mask remedy | Qualified CPU hardware implementation, cache/publication and lifecycle policy |
| Reset while outstanding | Exact crossing diagnostic exposes delayed completion after CPU-side reset | Coordinated ownership/reset fix and replay of all affected timing boundaries |
| Connected tooling | Owned console lifecycle passes harmless VM scripts and safety fixtures | Real ISSP session through the new client after connection restoration |

Additional P0 CPU completeness and lifecycle tests, prompted by the observed gaps:

| ID | Test | Required result |
|---|---|---|
| C13 | Omit any received index while its old RX word already matches expected data; duplicate other indices. | No completion accepted until every distinct expected index arrives; duplicates cannot increase coverage. |
| C14 | Deliver out-of-range, misaligned, wrong-slot or old-lease words. | Reject or quarantine before RX/coverage mutation; preserve current owner and last valid record. |
| C15 | CPU reset or timeout while APF owns TX/parameters; allow a delayed completion, then request again. | No buffer reuse or new owner until coordinated recovery; delayed old completion cannot publish a new save. |
| C16 | Publish final RX word and completion at every relative CPU/bridge phase; read coverage/data immediately. | Completion and coverage become visible only after the entire data set is coherent. |
| C17 | Full Tau MMIO map/version mismatch, including the isolated lease address overlapping PCM status. | Refuse incompatible firmware/RTL before command issue; no writes to audio registers or memory aliases. |

These additional tests are planned hardware/full-SoC gates. The current isolated model catches missing boot/verify guard words, but does not implement production CDC, a compatible MMIO map or coordinated reset recovery. Private stopped histories remain locally reproducible; sanitized public outcomes are in work/evidence/b005-connected-public-summary.json. No B007 hardware image exists.

Long CPU campaign follow-up: eight profiles × 64 saves pass (512 modeled saves / 2,576 commands), covering blank, damaged newest, one-valid, identical ties, counter wrap and high-generation carry. This expands isolated CPU-format evidence; C13–C17 production hardware/full-SoC gates remain pending.

## Parked future expansion

Directory discovery, library-index generation/replacement, derived cover images, and playlist creation are tracked in [FUTURE_TESTS.md](FUTURE_TESTS.md). These optional tests are not active qualification requirements or completed capabilities. Existing source-media protection remains in force until a specific generated-output experiment is selected.
