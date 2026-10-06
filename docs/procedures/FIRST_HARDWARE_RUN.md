# First Pocket hardware run

Status: both the official control and CARDWRITE01 custom probe are installed on CARDWRITE and host hashes verified. Custom simulation and internal timing checks pass. FSM-001 has now failed intended-record verification; see CURRENT_STATUS.md. The original minimal01 probe should be retained as failure evidence.

CARDWRITE was identified as a removable exFAT card, 127,832,031,232-byte volume, 131,072-byte allocation blocks, UUID `0C5F72C5-8851-3E82-94F5-5902CF4180FE`. Existing `Test Album`, recovered-file and other non-OS files were retained and hash-checked during install. macOS indexing/trash/event directories and Windows System Volume Information are excluded from protected-content comparisons because the OS updates them.

## Run CONTROL-001 first

1. Record the installed Pocket firmware version from Settings > About. A firmware file on a card is not evidence of the installed version.
2. Safely eject CARDWRITE, put it in the Pocket and open **Keyboard Mouse Target Data**, authored by **Example Author** (the official example core). The platform comes from the official `ex_platform` metadata.
3. Press **A** to load the first supplied image. Wait until it has finished changing. Avoid drawing/mouse/keyboard input so the expected framebuffer remains the supplied image.
4. Press **Select** once to save the framebuffer to slot `0x22`, `saved.bin`. Wait a few seconds.
5. Press **Start** to reload the saved framebuffer. Record whether it displays the same image. This is an immediate-read observation, not the final persistence verdict.
6. Quit the core normally back to the Pocket menu, then shut down normally. Remount CARDWRITE on the computer for file inspection.

Expected file:

`/Volumes/CARDWRITE/Assets/ex_platform/Example Author.Keyboard Mouse Target Data/saved.bin`

Expected bytes: exactly 184,320, equal to the first 184,320 bytes of the pinned `ex_image_all.bin`. If output differs, preserve it; do not modify the oracle to fit the observation. A mismatch could be a write failure, byte order/addressing issue, or different behavior in the upstream prebuilt image.

Host verification (read-only with respect to the card):

```sh
python3 tools/lab.py verify-control '/Volumes/CARDWRITE/Assets/ex_platform/Example Author.Keyboard Mouse Target Data/saved.bin' --image 0
```

Then eject, cold-boot the core and press Start without Select; record the reload result. Quit normally again before removing the card. This supplies a distinct cold persistence observation. Capture screenshots where useful and record command/action timing, firmware and full file hash.

`tools/read_results.py official-control --test-id CONTROL-001 --firmware <installed-version>` preserves the output file on the computer, verifies it and compares every existing protected file with the post-install baseline. It lists new APF files for review. It cannot infer which button actions or cold reloads occurred; those observations must be recorded separately.

## Original FSM-001 procedure (completed with failure; do not treat minimal01 as qualified)

The custom **CARDWRITE01** core uses BRAM, one command owner and a 64-byte dedicated existing output file. It makes no runtime flush request.

1. On first boot the expected generation is `00000001`; the output file begins as 64 zero bytes.
2. Press **A** once. Expect **WRITE CMD OK**, generation `00000001`, and completion count 1. This only says the target command completed.
3. Press **B** once. Expect **READ MATCH**, loaded generation `00000001`, and completion count 2. Poisoned readback RAM and a per-word received mask prevent missing reads from passing.
4. Quit and remount. Verify all 64 bytes with `python3 tools/lab.py verify /Volumes/CARDWRITE/Assets/cardwrite/alfatreze.CARDWRITE01/write64.bin --generation 1`.
5. Cold-relaunch and press B without A. Expected generation initializes to 1 so the first saved record can be compared. After later generations, host verification remains authoritative; a cold probe expects generation 1 and will report READ DIFF for another valid generation.

Each additional A press during a session advances the generation. The host oracle requires the matching explicit generation. TIMEOUT freezes the command source and prevents further requests; record the screen and recover through Quit/relaunch if the menu responds. If it does not, report the state before deciding on a power-loss test.

The first custom build tests existing-file updates only. Missing-file creation, nonvolatile Quit saves, explicit flush, A/B recovery and CPU integration are later experiments. Do not combine them into FSM-001.

## Result record

| Field | CONTROL-001 | FSM-001 |
|---|---|---|
| Installed firmware | pending | device metadata reports 2.7; About confirmation pending |
| Build identity | official commit acedd4530600aa3a79bc6c8df7462ceae5373c34, upstream prebuilt RBF hash in install manifest | Quartus 25.1std, seed 1; RBF_R SHA-256 `1d1ab747086c0c057af4c05f4c0763243c9a5e6f8e0eb4731afd047f5a292860` |
| Immediate reload | pending | READ DIFF; error 0, completion 2 |
| Post-Quit host file verification | pending | FAIL, malformed 64-byte physical file; exact shutdown actions pending |
| Cold reload | pending | pending |
| Protected contents unchanged after Pocket run | pending | PASS for pre-existing protected files |
| Verdict | pending | FAILED intended-record test; probe timing/startup investigation required |
