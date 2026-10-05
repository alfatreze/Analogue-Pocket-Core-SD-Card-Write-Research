# B006 connected trials

## Entry gates

Finish the B005 connected campaign and preserve its final full results. Require a successful full guarded06 compile, every internal timing corner passing, matching frozen source/test/display hashes and real map/fit RAM/resource reports. Keep existing B005 save files and prior outputs intact.

`tools/jtag_load_guarded.py --previous-result <preserved B005 final result> --from-build B005` checks the old/new slot/framework ABI, qualified package and SOF hashes, exact cable/device, host-unmounted state, completed B005 campaign and live state matching the retained PASS. It then programs only the qualified B006 image. No blind retry after an unknown programming outcome. SD metadata deliberately stays version 0.5.0; the debug-loaded image/banner is B006/0.6.0. The package contains no save fixtures.

Capture fresh SDW6 READY with zero commands before requesting cold. Preserve results from `tools/jtag_guarded.py cold` and `results`; independently compare the full 64-bit generation, valid mask, raw header generations and chosen CRC with the final B005 model. B006 additionally checks every received word and guard in each fixed 8 KiB region.

## Bounded campaign

`tools/connected_guarded_campaign.py --initial-result <preserved B006 first cold result> --batches 5 --rounds 1` performs five 64-save batches, each followed by qualified matching-SOF reload/read-only recovery, four single-save pause/resume controls, four between-command FPGA interruptions and a final repair/read-only check. It stops on any mismatch, retains each full history before reload and refuses to replace an existing campaign checkpoint. All pause reloads require the exact PAUSED state and command count; no reconfiguration while a command is outstanding.

Starting from the planned B005 generation 649, this campaign would finish at 974 (320 batch saves + four controls + one repair), with A=973/B=974. Those are planned values until actual evidence proves them. The independent byte model tracks partial inactive records; it never substitutes for physical host-read files.

## Remaining computer-side checks

After the owner can swap the card, preserve raw files before any additional writes. Verify exact 8,192-byte size, both records/generations/CRCs and every guard against the last completed campaign's predicted file hashes. Compare every unrelated file against the preserved B005 installation/cleanup baseline; explicitly review added screenshots/runtime files. Preserve all three earlier physical output files unchanged. B006 checks the fixed region on FPGA, but cannot detect extra bytes beyond that region or changes to unrelated files.

FPGA reconfiguration leaves Pocket and card powered. These trials do not establish full Pocket power-cycle recovery, SD power-loss atomicity, durable filesystem flush, multiple-card repeatability or authenticated storage. Separate confirmed lifecycle/power experiments remain required.

## Prepared remount collector and later installation

Once the connected campaign is independently verified and the owner can mount CARDWRITE, run `tools/read_connected_results.py --build B006 --test-id CONNECTED-006-FINAL --firmware 2.7` (firmware is explicitly owner-reported). It preserves both physical files and compares exact full-file bytes/sizes/guards against the final connected model, all prior protected contents against the B005 cleanup baseline, and detects changes during collection. It records experiment B006 separately from the card's B005 metadata version; newly added runtime/screenshots remain listed for review. Ten temporary-card collector tests pass.

Only after this physical gate passes, `tools/update_guarded.py --verified-run CONNECTED-006-FINAL` creates a concrete hash-bound plan. Applying that plan requires the matching token; it first archives qualified B005 sources/binaries/metadata/histories, backs up current core/cache/all five output files, rechecks card identity/snapshot, updates only existing core/platform paths and verifies every installed hash/protected file. The B006 package cannot contain save fixtures. Sixteen temporary-card update tests pass, including refusal of damaged/changed output, wrong active core, changed host raw backup, failed physical gate, symlinks/traversal and an attempted save reset. No actual host card update is performed while the card is inside the Pocket.
