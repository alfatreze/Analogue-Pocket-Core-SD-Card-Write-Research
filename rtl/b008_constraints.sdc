# B008: clk_74a and the CPU PLL output are related clocks. Never cut this
# relationship wholesale: ordinary setup/hold bounds apply to bundled data.
# Display-only pixel outputs stay grouped together; no false cut between the
# 0/90-degree outputs. SPI, second reference and display are separate domains.
set_clock_groups -asynchronous \
 -group {bridge_spiclk} \
 -group {clk_74b} \
 -group [get_clocks {*mp1*}] \
 -group [get_clocks {clk_74a *mp_cpu*}]
# Cut only first synchronizer stages. Second/third stages remain timed.
# Firmware payload/response bundles are deliberately NOT false-pathed.
proc b008_required_registers {patterns} {
 set regs [get_registers $patterns]
 if {[get_collection_size $regs] == 0} {error "B008 required timing registers missing: $patterns"}
 return $regs
}
set_false_path -to [b008_required_registers {*cpu_soc*|*mailbox*|ack1 *cpu_soc*|*mailbox*|req1 *cpu_soc*|*mailbox*|rst1}]
set_false_path -to [b008_required_registers {*cpu_soc*|keys1* *cpu_soc*|snap1}]
# The source bundle changes with its toggle. Two synchronizers plus the
# settling cycle defer sampling until at least three destination periods later.
# Grant only three cycles to those named bundles, never the whole clock pair.
set b008_command [b008_required_registers {*cpu_soc*|*mailbox*|command*}]
set b008_action [b008_required_registers {*cpu_soc*|*mailbox*|held_code* *cpu_soc*|*mailbox*|write_pulse *cpu_soc*|*mailbox*|read_pulse}]
set_multicycle_path -setup -end -from $b008_command -to $b008_action 3
set_multicycle_path -hold -end -from $b008_command -to $b008_action 2
set b008_reply [b008_required_registers {*cpu_soc*|*mailbox*|held_code* *cpu_soc*|*mailbox*|held_flags* *cpu_soc*|*mailbox*|held_completed* *cpu_soc*|*mailbox*|held_tag* *cpu_soc*|*mailbox*|action_count*}]
set b008_capture [b008_required_registers {*cpu_soc*|*mailbox*|response_code* *cpu_soc*|*mailbox*|snapshot_flags* *cpu_soc*|*mailbox*|snapshot_completed* *cpu_soc*|*mailbox*|snapshot_tag* *cpu_soc*|*mailbox*|snapshot_actions*}]
set_multicycle_path -setup -end -from $b008_reply -to $b008_capture 3
set_multicycle_path -hold -end -from $b008_reply -to $b008_capture 2
