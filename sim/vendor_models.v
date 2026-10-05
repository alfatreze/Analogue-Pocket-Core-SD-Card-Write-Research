// Simulation-only substitutes. Real builds use the pinned Altera IP.
module mf_datatable(input [7:0] address_a,address_b,input clock_a,clock_b,
    input [31:0] data_a,data_b,input wren_a,wren_b,output reg [31:0] q_a,q_b);
reg [31:0] mem[0:255];
integer i;
initial for(i=0;i<256;i=i+1) mem[i]=0;
always @(posedge clock_a) begin
    if(wren_a) mem[address_a]<=data_a;
    q_a<=mem[address_a];
end
always @(posedge clock_b) begin
    if(wren_b) mem[address_b]<=data_b;
    q_b<=mem[address_b];
end
endmodule
// Compilation-only ISSP stub. JTAG transport is qualified separately in Quartus/hardware.
module altsource_probe #(parameter sld_auto_instance_index="YES", sld_instance_index=0,
 instance_id="NONE", probe_width=1, source_width=1, source_initial_value="0",
 enable_metastability="NO")(
 input source_clk, source_ena, input [probe_width-1:0] probe,
 output [source_width-1:0] source);
assign source={source_width{1'b0}};
endmodule
module mf_pllbase(input refclk,rst,output outclk_0,outclk_1,output locked);
assign outclk_0=refclk;
assign outclk_1=refclk;
assign locked=!rst;
endmodule
