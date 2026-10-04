# FSM-002 — CARDWRITE02 hardware run

Status: corrected source passes direct-command and serial-bridge simulation and all reported internal Quartus timing corners. CARDWRITE02 installation and protected-file verification are recorded in CURRENT_STATUS.md. FSM-002-R1 physical-byte and immediate-readback checks PASS; cold reload pending.

## What changed

- Payload response is held until an APF bridge read strobe, matching the previous-request serial response convention.
- Generation 1 and the initial comparison payload are established by clocked startup logic before buttons are accepted. Startup does not cancel an outstanding command later in the session.
- Power-up don't-care optimization disabled for this build. The cause of minimal01's hardware generation-zero observation remains unresolved.
- Separate core ID `alfatreze.CARDWRITE02`, separate output path and frozen build stage. CARDWRITE01 and its malformed output are retained.

## First run: exactly one write and one read

1. Insert CARDWRITE and go to **Tools > Developer > Builds** and explicitly select **CARDWRITE02**, authored by **alfatreze**. Avoid resuming the previous core. Banner must say **CARD WRITING LAB 02**.
2. Before pressing anything, expect **IDLE**, **EXPECT GEN 00000001**, **COMPLETE 00000000**. Take a screenshot. If generation differs, stop and capture it.
3. Press **A** once and release. Wait for **WRITE CMD OK**, generation 1, completion 1, error 0. Take a screenshot.
4. Press **B** once and release. Expect **READ MATCH**, expected/read generation 1, completion 2, error 0. Take a screenshot. Preserve any different result.
5. Quit normally to the Pocket menu, shut down normally, and remount CARDWRITE on the computer. Report whether you used this exact sequence.
6. The host collector verifies the file independently, preserves it, and compares all protected files. A green screen alone is not a physical-file verdict.

Expected output: `/Volumes/CARDWRITE/Assets/cardwrite/alfatreze.CARDWRITE02/write64.bin`, exactly 64 bytes. Generation-1 SHA-256: `b7b05ccadcfa2eb7ed53aee6b5b12db57a06217da1351728a82810ad757f393c`.

```sh
python3 tools/read_results.py minimal02 --test-id FSM-002-R1 --firmware 2.7 --generation 1
```

The card-generated runtime metadata reports firmware 2.7; record Settings > About if it differs. Do not run CARDWRITE01 or the official control during FSM-002.

## Separate cold-reload gate, after the host file passes

Safely eject and cold-relaunch CARDWRITE02. Press **B only**, without A. Expect READ MATCH with generation 1 and completion 1. Capture the screen, quit normally, shut down, and remount. Collect under a different immutable test ID, `FSM-002-COLD`.

Further generations, repeatability, power interruption, different cards and CPU integration follow only after both these gates pass. TIMEOUT freezes the channel; photograph it and use Quit/relaunch if available.


Build identity: minimal02 seed 1; installed RBF_R SHA-256 `d0d17448b5347e7916f8171fe20aa75c411b43fa6166eadcc501fa14a115bff5`. The JTAG cable/chain is verified, but no JTAG programming was performed. A plain SD boot of CARDWRITE02 is the next baseline observation; a separately instrumented batch build follows.


The first attempted repeat showed LAB 01 and left CARDWRITE02's file untouched. It is retained as a wrong-build observation under FSM-002. Use FSM-002-R1 for the corrected-core repeat.


FSM-002-R1 passed: the physical file matches every expected byte, and the supplied LAB 02 screenshot shows READ MATCH. The next physical step is the B-only cold-reload gate above, collected as FSM-002-COLD.
