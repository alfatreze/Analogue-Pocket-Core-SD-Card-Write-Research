`timescale 1ns/1ps
// Actual pinned serial bridge, not a replacement bus timing model.
module tb_stress_spi;
parameter integer TOTAL_PAIRS=64;
reg clk=0; always #5 clk=~clk;
reg ss=1,drive=1,clock_out=0,mosi_out=0,miso_out=0;
tri spi_clock,spi_mosi,spi_miso;
assign spi_clock=drive?clock_out:1'bz;
assign spi_mosi=drive?mosi_out:1'bz;
assign spi_miso=drive?miso_out:1'bz;
wire [31:0] addr,wdata,rdata,generation;
wire rd,wr;
reg running=0,write_button=0,done=0;
wire tr,tw;
wire [31:0] offset,source,length,completed,passed;
wire [3:0] status;
io_bridge_peripheral serial(.clk(clk),.reset_n(1'b1),.endian_little(1'b0),
 .pmp_addr(addr),.pmp_addr_valid(),.pmp_rd(rd),.pmp_rd_data(rdata),
 .pmp_wr(wr),.pmp_wr_data(wdata),.phy_spimosi(spi_mosi),
 .phy_spimiso(spi_miso),.phy_spiclk(spi_clock),.phy_spiss(ss));
lab_stress #(.TOTAL_PAIRS(TOTAL_PAIRS)) probe(.clk(clk),.reset_n(running),.write_button(write_button),.read_button(1'b0),
 .bridge_addr(addr),.bridge_rd(rd),.bridge_wr(wr),.bridge_wr_data(wdata),.bridge_rd_data(rdata),
 .target_read(tr),.target_write(tw),.slot_offset(offset),.source_addr(source),.transfer_length(length),
 .completed(completed),.loaded_generation(passed),.debug_source(32'd0),.target_done(done),.target_err(3'd0),.generation(generation),.status(status));
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
reg [31:0] value,held_offset,held_source,held_length;
reg [7:0] file_bytes[0:262143];
integer index,byte_index,fd,commands=0;
initial begin
 for(index=0;index<262144;index=index+1)file_bytes[index]=8'ha5;
 ss=0;tick(1);ss=1;tick(TOTAL_PAIRS+10);running=1;
 if(status!==0)$fatal(1,"batch serial startup");
 write_button=1;tick(1);write_button=0;
 while(completed<TOTAL_PAIRS)begin
  wait(tr||tw||completed==TOTAL_PAIRS);
  if(completed<TOTAL_PAIRS)begin
   held_offset=offset;held_source=source;held_length=length;done=0;tick(5);
   if(held_source==32'h10000000)begin
    read_transaction(held_source,value); // prime previous-request response
    for(index=0;index<(held_length+3)/4;index=index+1)begin
     read_transaction(held_source+4+index*4,value);
     for(byte_index=0;byte_index<4;byte_index=byte_index+1)
      if(index*4+byte_index<held_length)
       file_bytes[held_offset+index*4+byte_index]=value[31-byte_index*8 -: 8];
    end
   end else begin
    for(index=0;index<(held_length+3)/4;index=index+1)begin
     value=0;
     for(byte_index=0;byte_index<4;byte_index=byte_index+1)
      if(index*4+byte_index<held_length)
       value[31-byte_index*8 -: 8]=file_bytes[held_offset+index*4+byte_index];
     write_transaction(held_source+index*4,value);
    end
   end
   done=1;tick(1);commands=commands+1;
  end
 end
 tick(2);
 if(status!==4||passed!==TOTAL_PAIRS||commands!=TOTAL_PAIRS*2)$fatal(1,"batch serial summary");
 fd=$fopen("stress-spi-written.hex","w");
 for(index=0;index<262144;index=index+1)$fdisplay(fd,"%02x",file_bytes[index]);$fclose(fd);
 $display("PASS B004 actual APF SPI: %d pairs, %d commands, all payload words",TOTAL_PAIRS,commands);$finish;
end
initial begin #500000000;$fatal(1,"batch SPI watchdog");end
endmodule
