# Card-writing lab working agreements

Keep this project independent of Tau Alpha and its other variants. Read siblings as references; do not change their files or invoke their build tools that write into their dist/work trees.

Use the pinned official sources in vendor/PINNED.json. Never edit a vendor checkout. Put a reviewed adaptation in rtl/ with an explicit description and retained source notices.

Hardware mutations use only the user-designated disposable volume, checked by mount name, UUID and removable-media identity. Produce a concrete plan first; use tools/install.py for first installs, with file hashes and a before/after protected-content comparison. Approval already granted in chat applies to the agreed experiment scope; do not invent extra per-command confirmation requirements.

Keep compilation sources frozen after launch. Check for existing Quartus compiles before launching another. Preserve logs, complete timing reports, resources, source hashes and both raw/reversed bitstream hashes. Never substitute the template's shipped bitstream for a failed custom compile.

Append implementation decisions, failures and actual hardware outcomes to DECISIONS.md and CURRENT_STATUS.md. Distinguish code review, host tests, RTL simulation, Quartus verification and Pocket evidence. Keep missing firmware/card results pending.

Screen readouts need named native RTL framebuffer captures under work/sim; inspect them before package delivery. Simulation models do not establish physical IP timing or persistence.


## Build naming and active-core workflow (owner preference, 2026-10-05)

Keep one persistent active research core on CARDWRITE so the owner can resume it without selecting a different core for each build. Use the currently selected `alfatreze.CARDWRITE02` identity as the stable entry unless a migration is explicitly needed. Give every subsequent build a unique human-readable build number, metadata version/description and matching on-screen banner (for example `SD Write Research B003`); record exact source/bitstream hashes. The fixed APF shortname/folder identity is separate from the displayed build identity.

Archive prior qualified sources, metadata, SOF/RBF, package and experiment outputs in this project before updating the active entry. Use tools/update.py for the audited minimal02-to-B003R2 update, with verified backups and card identity/hash checks; tools/install.py remains first-install-only. Later updates require the same safeguards against their actual prior build. Do not reset prior result files silently. Preserve the qualified minimal02 image/output and its completed reload evidence.

B004 uses tools/update_stress.py for the audited B003R2-to-B004R2 update. Require unchanged verified B003 physical outputs, archive prior qualification, and preserve both write64.bin and batch-b003.bin. Its new stress-b004.bin must be absent before first installation. Never reset it for a later run.
