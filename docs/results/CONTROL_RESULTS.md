# Official target-data reference control

[All suites](README.md) · [Overall feasibility](../research/FEASIBILITY_STATUS.md)

## Goal

Establish whether the unmodified official target-data example can persist its expected file on the designated Pocket/card.

## Method

Pin the upstream package, install and hash-check all package files, and compare protected card content. Functional write/read/Quit/cold-restart execution is a separate gate.

## Corrections

None recorded for the unchanged upstream package. The shipped upstream bitstream was treated as a reference, without claiming a new custom compile.

## Result details

**Preparation PASS; functional persistence PENDING.** Installation evidence exists. The retained record does not establish a completed official-reference save/reload campaign.

### CONTROL-PREP — package installation

**Goal:** Install a known reference without collateral file changes.

**Method:** Verify the 13 installed package files and compare the card inventory before/after.

**Corrections:** None recorded.

**Result details:** All 13 hashes passed; pre-existing non-OS files remained identical.

### CONTROL-EXEC — reference persistence

**Goal:** Confirm expected saved bytes after Quit and cold restart.

**Method:** The planned Select-save/Start-reload sequence requires exact host file comparison.

**Corrections:** None; no verified functional outcome is promoted from installation.

**Result details:** PENDING in the retained evidence. This control is not counted as a finished persistence suite.

### Evidence and scope

[Procedure](../procedures/FIRST_HARDWARE_RUN.md) and [dated status](../status/CURRENT_STATUS.md). Installation inventories remain in the local `work/evidence/install-official-control/` archive.
