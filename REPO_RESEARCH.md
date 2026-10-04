# Local repository research: SD-card writing

Reviewed the local Tau Alpha workspace on 2026-10-04. This is a quick repository search, not a hardware run.

Follow-up review: Tau's `core_bridge_cmd.v` and `tgt_cmd.v` do implement `0x0188`; audit A-088..090 and skill KB-022/023 record immediate successful write/readback but absent physical-file persistence and a blocked flush. The statement below about no current controlled result means no validated durable success; the negative experiments are material evidence. `fw/settings.inc` also records historical collateral library damage and a command-structure/slot-table overlap. These details drive the isolated test strategy in RESEARCH_PLAN.md.

## Directly relevant to core-side writes

The authoritative local technical notes are in the sibling skill `tau-alpha/.claude/skills/analogue-pocket-dev`:

- `references/host-target-commands.md`: target commands `0x0184`/`0x0188`, the slot ID/size table at `0xF8002000`, the shutdown writeback path, and the stock template FSM gap.
- `references/json-files.md`: `data.json` slot flags, nonvolatile and deferload behavior, parameter bit 5, and how the slot size is supplied.
- Knowledge entries KB-001, KB-005, KB-007, KB-074, KB-076: evidence status and validation plans. See [CORE_KNOWLEDGE.md](CORE_KNOWLEDGE.md) for the extracted findings.

Important current unknown: durable target `0x0184` reliability is disputed. The official example and a firmware changelog suggest it can work, but local A-088..090 probes show immediate readback without durable file contents. The stock template reviewed by the skill lacks `0x0188`; Tau's custom implementation exists and timed out on its earlier hardware probe. The current firmware/device configuration needs a new controlled test.

## Existing Tau Alpha project record

`tau-alpha/CLAUDE.md` and `tau-alpha/docs/AUDIT_TRAIL.md` record many core packages installed on an SD card, mostly with backup, hash verification, and cache-clearing procedures. These are core-install operations from the host, not proof of a core writing arbitrary data files to SD. They are useful for packaging/recovery discipline only.

`tau-alpha/docs/TEST_SCRIPT_ALPHA34.md` and related handoffs track Pocket validation, core builds and SD installs. They do not establish an APF target-write method for this new experiment.

## Adjacent Tau Omega findings (host-to-card, different writer)

`Tau Omega/docs/STATUS_HANDOFF.md` has a dated “Real hardware write validation (2026-09-23)” section. It records sync, package install, and core removal against a mounted Pocket card at `/Volumes/Pock`, performed from a desktop app/CLI. All three paths were staged low-to-high risk and reviewed between steps. This is not a core-originated SD write, but it demonstrates:

- use a separate platform/core namespace to avoid touching the installed Tau files;
- start with a tiny copy and verify it by scanning;
- retain backup/hash evidence for card mutations;
- real removable media contains AppleDouble `._*` files, an edge case that host code had to handle.

Tau Omega's `crates/tau-core/src/sync.rs` writes through a temp file, syncs, verifies SHA-256/readback, then renames into place. `Tau Omega/src-tauri/src/main.rs` serializes card writes with a try-lock. `Tau Omega/SAFETY_RULES.md` requires a reviewed plan before writes and verification after each write. These are host-side design lessons, not core command documentation.

## Recommended distinction in future notes

Always label who performs the write:

- **Pocket/APF shutdown writeback** for nonvolatile slots;
- **Pocket/APF target command** for a core-issued `0x0184`/`0x0188` operation;
- **desktop host write** for Tau Omega or manual file copies.

Mixing these paths would make an experiment's result ambiguous.
