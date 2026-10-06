# Tau CPU prototypes — isolated simulations

[All suites](README.md) · [Overall feasibility](../research/FEASIBILITY_STATUS.md)

## Goal

Explore exact VexRiscv command ownership, crossings, save-format recovery, and fault handling before hardware integration.

## Method

Use the pinned CPU/crossing with synthetic APF completion and independent modeled files. Exercise multiple clock ratios, command selections/errors, busy/stale-DONE/sequence wrap, corruption/refusal, missing words, and long save profiles.

## Corrections

Increase a separate Icarus testbench budget from 200 to 300 ms after the original stopped at 302/322 commands. Compile identical Verilator inputs in a temporary path without spaces. Replace a prototype data-only scanner with an explicit received-word lease after a stale matching guard escaped detection. Independent reset still clears CPU busy too early; it remains an integration limitation.

## Result details

**Simulation passes with explicit limitations.** CPU execution, format/recovery, and received-lease profiles passed. Original missing-word acceptance and independent-reset behavior remain documented limitations; physical CPU persistence and production CDC/MMIO/playback are pending.

### CPU-CDC — crossing

**Goal:** Verify selection/errors, stale DONE, busy ownership, and sequence wrap.

**Method:** Four clock ratios with 300 modeled commands each.

**Corrections:** None recorded for the passing crossing corpus.

**Result details:** 1,200 crossing-level modeled commands passed; physical flush support is not inferred.

### CPU-COMMAND — exact generated CPU

**Goal:** Run genuine firmware on pinned VexRiscv through the crossing.

**Method:** Four ratios plus one 60 MHz bus-wait/delayed-APF profile, 300 commands each.

**Corrections:** None recorded in these passing profiles.

**Result details:** 1,500 CPU-executed commands passed, including sequence wrap and busy extra-GO rejection.

### CPU-RESET — outstanding command

**Goal:** Test ownership after CPU reset while APF is still busy.

**Method:** Reset the CPU side during one accepted modeled write and observe delayed completion.

**Corrections:** No completed integration fix claimed; coordinated ownership/reset is required in B008.

**Result details:** LIMITATION: busy cleared before the accepted APF command completed; delayed completion advanced the post-reset sequence. Not a reset-safety pass.

### CPU-FORMAT — eight starting states

**Goal:** Validate the alternating-file format and refusal conditions.

**Method:** Eight initial profiles: clean/blank/corrupt-newest/high-generation saves and damaged/guard/conflict/exhaustion refusals.

**Corrections:** Keep MMIO and buffers isolated from the full Tau map.

**Result details:** 16 modeled saves matched exact files/guards/CRC/generations; refusal cases preserved simulated bytes.

### CPU-FAULT — six diagnostics

**Goal:** Stop safely on command/verification errors, timeout, and incomplete receipt.

**Method:** Inject modeled failures at boot, first chunk, verification, timeout, and missing-guard-word receipt.

**Corrections:** Data comparisons alone accepted one stale matching missing word; retain this gap and add the explicit received lease separately.

**Result details:** Error/timeout diagnostics stopped as described; original missing-word robustness expectation FAILED. No later-completion/reset safety inferred from timeout stop.

### CPU-RECEIVED — remedy

**Goal:** Require every word to be received before consuming the buffer.

**Method:** Separate per-read received-bit lease; clean and missing stale guard words at boot/verification.

**Corrections:** Add distinct receipt bookkeeping cleared while idle. Its prototype MMIO address overlaps Tau PCM and must be remapped for integration.

**Result details:** Simulated clean saves passed; both missing-word cases stopped with 0x23 and preserved the last valid file.

### CPU-LONG — eight 64-save profiles

**Goal:** Exercise repeatability and recovery state selection with actual CPU firmware.

**Method:** Clean, carry, blank, A-newest, corrupt-newest, only-B-valid, generation-tie and high-generation profiles.

**Corrections:** Separate larger simulation budget and space-free Verilator build path; preserve failed harness runs.

**Result details:** 512 modeled saves / 2,576 modeled commands passed exact bytes/guards/CRC/generations. Physical persistence, real serialization, and playback remain pending.

### Evidence and scope

[Integration plan](../research/TAU_CPU_INTEGRATION.md), [crossing](../../work/evidence/tau-cdc-simulation.json), [commands](../../work/evidence/tau-cpu-command-simulation.json), [faults](../../work/evidence/tau-cpu-save-fault-diagnostics.json), [received remedy](../../work/evidence/tau-cpu-save-received-simulation.json), [long-profile qualification](../../work/evidence/tau-cpu-stress-fast-qualification.json). These prototypes do not satisfy the new B008 CPU-to-B007-engine gate.
