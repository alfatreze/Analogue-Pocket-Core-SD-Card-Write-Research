# Source provenance

Pinned upstream references:

- `open-fpga/core-example-kbmouse-targetdata`, commit `acedd4530600aa3a79bc6c8df7462ceae5373c34`.
- `open-fpga/core-template`, commit `da3a021b1eaf742604d86d8dc9b33a6666263e6a`.

`vendor/PINNED.json` contains file hashes. Original Analogue/Intel source notices are retained; these downloaded files and IP are not relicensed by this project. They are local research/build references. Review the applicable upstream/tool terms before redistributing them.

`rtl/core_top.v` retains the template physical interface and unused-I/O tie-offs and adds the lab logic. `rtl/core_bridge_cmd.v` is the template command module with the data-table declarations moved ahead of their first use for Icarus compatibility; no protocol behavior is intentionally changed. Build minimal01 was staged before that declaration reorder and uses the original pinned command module; the simulation copy differs only in declaration order.

The custom lab probe, readout, testbenches and host tools are in this project. No implementation files were imported from Tau Alpha; its source was consulted for architecture and failure history.


## License scope

The root MIT LICENSE applies to original project code, documentation and original modifications, copyright 2026 alfatreze. It does not grant rights to third-party material or override its terms.

The pinned upstream submodules, copied Analogue framework/template portions in `rtl/core_top.v` and `rtl/core_bridge_cmd.v`, copied template/IP files in the frozen `work/build/` stage, and upstream control assets/bitstreams in `work/packages/official-control/` retain their original notices and applicable upstream/tool terms. Generated bitstreams may incorporate third-party framework/IP and are not represented as exclusively MIT-licensed. Hash manifests and build reports document provenance rather than granting rights to their referenced material.
