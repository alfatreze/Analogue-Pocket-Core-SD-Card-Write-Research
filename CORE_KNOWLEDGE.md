# Analogue Pocket core knowledge for SD writes

Source: the local `tau-alpha/.claude/skills/analogue-pocket-dev` skill and its knowledge base, inspected 2026-10-04. This is a focused extract for this project's scope, not a copy of the whole skill.

### Added local hardware evidence, 2026-10-04

- KB-022 (hardware-validated, narrow scope) and Tau audit A-090: Tau already has a custom `0x0188` implementation. It did not complete within 10 seconds and left the following read blocked. This is not a missing-implementation result; installed firmware was unconfirmed.
- KB-023 (hardware-validated) and A-088: the corrected BRIDGE base made immediate `0x0184`/`0x0180` readback return the signature, but the SD file remained zeros. This is not evidence of durable runtime persistence.
- KB-025 (hardware-validated): APF Interact carried a checksummed 64-byte diagnostic record on Quit, with signed-word encoding constraints. Current Tau extends its internal settings register capacity; do not assume that internal word capacity equals unlimited declared Interact variables.
- A-089's historical bitmap interpretation is not authoritative: `nonvolatile` and `deferload` are separate JSON booleans in the official data.json documentation. Parameter bits 6/7 concern reset/restart on loading.

The stock-template gap below remains valid for the template source reviewed by the skill, but it must not be applied to Tau's modified implementation. See RESEARCH_PLAN.md for current investigation priorities.

## Write paths

### 1. Nonvolatile slot writeback on shutdown

- A `data.json` slot marked `nonvolatile` is loaded by APF and written back during core exit, power off, or sleep. The size is taken from the core's data-slot ID/size table at BRIDGE base `0xF8002000`.
- The size-table entry is indexed by the slot's position in `data_slots[]`, not by its slot ID. The size word is at `0xF8002000 + (position * 8) + 4`; zero means zero bytes are available to write back.
- Read the entry back over BRIDGE before depending on it. Check the file under `/Saves/...` after a normal Quit and validate its exact size and contents.
- `parameters` bit 5 initializes a missing nonvolatile slot with `0xFF` up to `size_maximum`. A community report says this may be needed for the first file to exist; test it rather than assuming it.

Evidence: KB-001 is source-verified/high confidence for size and position. KB-074 is community-reported/medium confidence for only writing back a slot APF loaded and for first-file creation requirements.

### 2. Core-initiated target data-slot write (`0x0184`)

- The target write command transfers bytes from a BRIDGE address into a data slot. Parameters are slot ID, slot offset, BRIDGE address, and byte length (with the command's documented word layout).
- It is intended for deferload slots. `data.json` must expose the slot and its ID; use a dedicated test path/slot so save write tests cannot affect production data.
- A result code of zero means the operation reported completion, not that the correct contents were persisted. Check file size and compare a deterministic pattern or hash after removing/reloading the card.
- Reports conflict across firmware eras: an older LiteX note calls SD writing broken; the official `kbmouse-targetdata` example uses it; Analogue's 1.1 beta 7 changelog says it fixed a truncation bug. Current reliability remains unproven here.

Evidence: KB-005 is disputed/low confidence. Make a current firmware hardware run the deciding evidence.

### 3. Target flush (`0x0188`)

- The docs describe `0x0188` as flushing a data slot, but the stock core template target FSM does not implement it. The skill found no known public implementation proving its behavior.
- Normal nonvolatile writeback is APF-driven at shutdown; `0x0188` may not be needed for that path. Keep any `0x0188` test isolated from `0x0184` and APF shutdown writeback.

Evidence: KB-007 is source-verified/high confidence for the template gap, not for how Pocket firmware behaves with a custom implementation.

## Data-slot and lifecycle details

- `data.json` supports up to 32 slots; IDs are 16-bit and unique. Nonvolatile slots are automatically written back; deferload slots avoid automatic loading and are meant for target read/write commands.
- When testing nonvolatile slots, record both the slot's position and ID. A data-slot size table is two 32-bit words per slot: ID then size.
- Core-issued writes that cross from the BRIDGE clock domain into another memory clock may need ordering protection. A community implementation queues a fence behind prior writes and releases execution only after memory writes complete. Treat this as a design lead, not a Pocket SD-write rule (KB-076, community-reported/low confidence).
- If data was loaded into memory and is consumed after boot, do not assume `dataslot_allcomplete` also means asynchronous downstream memory writes have physically completed; verify ordering in RTL/simulation and on hardware if relevant.
- The template does not implement `0x0188`, `0x0181`, `0x0185`, or debug event `0x0152`; inspect `core_bridge_cmd` before relying on a documented target command.

## Test discipline carried over from the skill

1. Establish firmware and framework versions at the start of every hardware test.
2. Change one field or behavior at a time.
3. Use a small, recognizable byte pattern including data near the beginning and end of the file; compare full output, expected size, and checksum.
4. Test normal Quit separately from power loss/removal. Only normal shutdown triggers the documented APF save path; pulling the card risks unsaved data.
5. Rebuild and package the matching `.rbf_r` for every RTL change. Hash the card copy against the build output to rule out stale bitstreams.
6. Record the test ID, build/hash, card, observed file state, and evidence. Preserve unexpected or failed outcomes.

## Source map

- Skill router and workflow: `tau-alpha/.claude/skills/analogue-pocket-dev/SKILL.md`
- Target commands and size table: `references/host-target-commands.md`
- `data.json` slot flags and persistence: `references/json-files.md`
- SD paths and debug logging: `references/sd-packaging-assets.md`
- Evidence entries: `references/knowledge-base/entries/KB-001*`, `KB-005*`, `KB-007*`, `KB-074*`, `KB-076*`
- Skill status index: `references/knowledge-base/INDEX.md` and `INDEX.local.md`
