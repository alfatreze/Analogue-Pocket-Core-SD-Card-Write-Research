`timescale 1ns/1ps
// Actual pinned serial bridge, not a replacement bus timing model.
module tb_spi;
reg clk=0; always #5 clk=~clk;
reg ss=1,drive=1,clock_out=0,mosi_out=0,miso_out=0;
tri spi_clock,spi_mosi,spi_miso;
assign spi_clock=drive?clock_out:1'bz;
assign spi_mosi=drive?mosi_out:1'bz;
assign spi_miso=drive?miso_out:1'bz;
wire [31:0] addr,wdata,rdata,generation;
wire rd,wr;
reg running=0,read_button=0,done=0;
wire [3:0] status;
io_bridge_peripheral serial(.clk(clk),.reset_n(1'b1),.endian_little(1'b0),
 .pmp_addr(addr),.pmp_addr_valid(),.pmp_rd(rd),.pmp_rd_data(rdata),
 .pmp_wr(wr),.pmp_wr_data(wdata),.phy_spimosi(spi_mosi),
 .phy_spimiso(spi_miso),.phy_spiclk(spi_clock),.phy_spiss(ss));
lab_probe probe(.clk(clk),.reset_n(running),.write_button(1'b0),.read_button(read_button),
 .bridge_addr(addr),.bridge_rd(rd),.bridge_wr(wr),.bridge_wr_data(wdata),.bridge_rd_data(rdata),
 .target_done(done),.target_err(3'd0),.generation(generation),.status(status));
task tick(input integer count);repeat(count)begin @(posedge clk);#1;end endtask
task send_address(input [31:0] a);
 integer bit_index;
 begin
  drive=1;clock_out=0;ss=0;tick(8);
  for(bit_index=30;bit_index>=0;bit_index=bit_index-2)begin
   clock_out=0;mosi_out=a[bit_index+1];miso_out=a[bit_index];tick(4);
   clock_out=1;tick(4);
  end
  // Release bus before the peripheral becomes its clock/data driver.
  clock_out=0;if(!a[0])drive=0;
 end
endtask
task read_transaction(input [31:0] a,output [31:0] value);
 integer limit,bit_index;
 begin
  send_address(a);
  limit=0;
  while(serial.spis!==serial.ST_SEND_0 && limit<100)begin tick(1);limit=limit+1;end
  if(limit==100)$fatal(1,"serial response absent state=%d spi=%d addr=%h rx=%h byte=%h idx=%d count=%d",serial.state,serial.spis,addr,serial.rx_dat,serial.rx_byte,serial.rx_latch_idx,serial.addr_cnt);
  // Decode the actual outgoing two-wire serial word on its falling clocks.
  value=0;
  for(bit_index=0;bit_index<16;bit_index=bit_index+1)begin
   @(negedge spi_clock);#1;

   value={value[29:0],spi_mosi,spi_miso};
  end
  tick(8);ss=1;tick(12);drive=1;clock_out=0;
 end
endtask
task write_transaction(input [31:0] a,input [31:0] value);
 integer bit_index;
 begin
  send_address(a|1);tick(8);
  for(bit_index=30;bit_index>=0;bit_index=bit_index-2)begin
   clock_out=0;mosi_out=value[bit_index+1];miso_out=value[bit_index];tick(4);
   clock_out=1;tick(4);
  end
  clock_out=0;tick(12);ss=1;tick(12);
 end
endtask
reg [31:0] value;
integer index,fd;
initial begin
 ss=0;tick(1);ss=1;tick(40);
 if(generation!==1||status!==0)$fatal(1,"clocked startup not ready");
 running=1;
 // Prime first address; each next transaction returns the preceding request.
 read_transaction(32'h10000000,value);
 fd=$fopen("spi-generation-1.hex","w");
 for(index=0;index<16;index=index+1)begin
  read_transaction(32'h10000004+index*4,value);
  if(value!==probe.tx_mem[index])$fatal(1,"SPI shifted word %d: %h expected %h",index,value,probe.tx_mem[index]);
  $fdisplay(fd,"%08x",value);
 end
 $fclose(fd);
 read_button=1;tick(1);read_button=0;tick(40);
 if(status!==2)$fatal(1,"read request absent");
 for(index=0;index<16;index=index+1)
  write_transaction(32'h10000100+index*4,probe.tx_mem[index]);
 if(probe.received!==16'hffff)$fatal(1,"SPI readback word missing");
 done=1;tick(24);done=0;
 if(status!==4||probe.loaded_generation!==1)$fatal(1,"SPI readback mismatch");
 $display("PASS actual APF SPI: clocked startup and all 16 response words including first/last, RX mask and full readback");$finish;
end
initial begin #1000000;$fatal(1,"SPI watchdog");end
endmodule
