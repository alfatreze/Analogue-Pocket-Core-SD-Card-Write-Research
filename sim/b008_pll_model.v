`timescale 1ns/1ps
// Elaboration-only PLL replacement; timing/IP are qualified by Quartus.
module b008_cpu_pll(input refclk,output reg cpu_clk=0,output locked);
 always #8.333 cpu_clk=~cpu_clk;
 assign locked=1'b1;
endmodule
