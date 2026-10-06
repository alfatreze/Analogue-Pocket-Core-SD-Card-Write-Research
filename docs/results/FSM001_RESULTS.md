# FSM-001 — first minimal writer

[All suites](README.md) · [Overall feasibility](../research/FEASIBILITY_STATUS.md)

## Goal

Write and recover one exact 64-byte generation-1 record through a CPU-free APF target write.

## Method

Compile/qualify the minimal01 core, issue write/read, preserve the screen observations, then remount and independently compare the entire file.

## Corrections

After the mismatch, preserve the original file and oracle. Reproduce the one-word shift using the real APF serial state machines; the corrected response/startup implementation belongs to the separately qualified FSM-002 suite.

## Result details

**FAILED intended-record verification.** Command success did not imply correct persisted bytes.

### FSM-001 — write/read/remount

**Goal:** Store the intended 64-byte record with the expected generation.

**Method:** User write/read actions, screenshots, then full host byte comparison.

**Corrections:** None applied to this frozen run. The failure was retained for diagnosis.

**Result details:** The file was 64 bytes but failed the generation-1 oracle. It matched a diagnostic generation-zero record shifted by one word, with a zero word appended. SHA-256 `40e733d070f38a15467d752210fa4a84ca83d31e1d85e465362c68630276879c`. Protected files were unchanged.

### Evidence and scope

[Original observations](../status/CURRENT_STATUS.md#fsm-001--first-pocket-observation), [first procedure](../procedures/FIRST_HARDWARE_RUN.md). This failed run establishes no cold persistence, repeatability, or interruption safety.
