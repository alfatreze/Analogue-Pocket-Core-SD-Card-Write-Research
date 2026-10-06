// New isolated one-output clock configuration using the same altera_pll
// parameter interface and fractional mode as the pinned Tau clock reference.
// Requested 60 MHz is nominal; fitted PLL/timing reports establish actual rate.
module b008_cpu_pll(input wire refclk,output wire cpu_clk,output wire locked);
 altera_pll #(.fractional_vco_multiplier("true"),
  .reference_clock_frequency("74.25 MHz"),.operation_mode("normal"),
  .number_of_clocks(1),.output_clock_frequency0("60.000000 MHz"),
  .phase_shift0("0 ps"),.duty_cycle0(50),.pll_type("General"),.pll_subtype("General")) pll(
  .refclk(refclk),.rst(1'b0),.outclk(cpu_clk),.locked(locked),.fboutclk(),.fbclk(1'b0));
endmodule
