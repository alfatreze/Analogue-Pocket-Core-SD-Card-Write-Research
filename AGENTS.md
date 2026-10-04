# Card-writing lab working agreements

Keep this project independent of Tau Alpha and its other variants. Read siblings as references; do not change their files or invoke their build tools that write into their dist/work trees.

Use the pinned official sources in vendor/PINNED.json. Never edit a vendor checkout. Put a reviewed adaptation in rtl/ with an explicit description and retained source notices.

Hardware mutations use only the user-designated disposable volume, checked by mount name, UUID and removable-media identity. Produce a concrete plan first; use tools/install.py for first installs, with file hashes and a before/after protected-content comparison. Approval already granted in chat applies to the agreed experiment scope; do not invent extra per-command confirmation requirements.

Keep compilation sources frozen after launch. Check for existing Quartus compiles before launching another. Preserve logs, complete timing reports, resources, source hashes and both raw/reversed bitstream hashes. Never substitute the template's shipped bitstream for a failed custom compile.

Append implementation decisions, failures and actual hardware outcomes to DECISIONS.md and CURRENT_STATUS.md. Distinguish code review, host tests, RTL simulation, Quartus verification and Pocket evidence. Keep missing firmware/card results pending.

Screen readouts need named native RTL framebuffer captures under work/sim; inspect them before package delivery. Simulation models do not establish physical IP timing or persistence.
