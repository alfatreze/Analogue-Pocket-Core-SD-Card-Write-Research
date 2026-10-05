set_clock_groups -asynchronous \
 -group {bridge_spiclk} \
 -group {clk_74a} \
 -group {clk_74b} \
 -group [get_clocks {*mp1*}]
