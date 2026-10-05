`timescale 1ns/1ps
module tb_recovery;
parameter integer MODE=0,COMMITS=64,INJECT=0,HOLD=-1,KILL=0,COMMAND=0,SPI=0,EXPECT_STATUS=4;
parameter [63:0] EXPECT_GEN=64;
reg clk=0;always #5 clk=~clk;
reg run=0,wb=0,rb=0,done=1,setup=0;
reg [2:0] error=0;reg [31:0] addr=0,wdata=0,debug_source=0;
reg rd=0,wr=0;wire [31:0] pdata,cdata,data;
wire [31:0] offset,source,length,completed,generation,validmask;
wire [15:0] slot;wire tr,tw;wire [3:0] status;wire [511:0] snapshot;
wire cd,ca,host_reset;wire [2:0] ce;
reg ss=1,drive=1,clock_out=0,mosi_out=0,miso_out=0;
tri spi_clock,spi_mosi,spi_miso;
assign spi_clock=drive?clock_out:1'bz;assign spi_mosi=drive?mosi_out:1'bz;assign spi_miso=drive?miso_out:1'bz;
wire [31:0] serial_addr,serial_wdata;wire serial_rd,serial_wr;
io_bridge_peripheral serial(.clk(clk),.reset_n(1'b1),.endian_little(1'b0),
 .pmp_addr(serial_addr),.pmp_addr_valid(),.pmp_rd(serial_rd),.pmp_rd_data(pdata),
 .pmp_wr(serial_wr),.pmp_wr_data(serial_wdata),.phy_spimosi(spi_mosi),.phy_spimiso(spi_miso),.phy_spiclk(spi_clock),.phy_spiss(ss));
assign data=addr[31:24]==8'hf8 ? cdata:pdata;
lab_recovery #(.TIMEOUT_CYCLES(SPI?500000:20000),.COMMITS(COMMITS)) dut(.clk(clk),.reset_n(run),
 .write_button(wb),.read_button(rb),.bridge_addr(SPI?serial_addr:addr),.bridge_rd(SPI?serial_rd:rd),.bridge_wr(SPI?serial_wr:wr),
 .bridge_wr_data(SPI?serial_wdata:wdata),.bridge_rd_data(pdata),.target_read(tr),.target_write(tw),
 .slot_id(slot),.slot_offset(offset),.source_addr(source),.transfer_length(length),
 .target_done(COMMAND?cd:done),.target_err(COMMAND?ce:error),.status(status),.completed(completed),
 .generation(generation),.loaded_generation(validmask),.debug_source(debug_source),.debug_probe(snapshot));
core_bridge_cmd cmd(.clk(clk),.reset_n(host_reset),.bridge_endian_little(1'b0),
 .bridge_addr(addr),.bridge_rd(rd),.bridge_rd_data(cdata),.bridge_wr(wr),.bridge_wr_data(wdata),
 .status_boot_done(setup),.status_setup_done(setup),.status_running(run),
 .dataslot_requestread_ack(1'b1),.dataslot_requestread_ok(1'b1),.dataslot_requestwrite_ack(1'b1),.dataslot_requestwrite_ok(1'b1),
 .savestate_supported(1'b0),.savestate_addr(32'd0),.savestate_size(32'd0),.savestate_maxloadsize(32'd0),
 .savestate_start_ack(1'b0),.savestate_start_busy(1'b0),.savestate_start_ok(1'b0),.savestate_start_err(1'b0),
 .savestate_load_ack(1'b0),.savestate_load_busy(1'b0),.savestate_load_ok(1'b0),.savestate_load_err(1'b0),
 .target_dataslot_read(tr),.target_dataslot_write(tw),.target_dataslot_getfile(1'b0),.target_dataslot_openfile(1'b0),
 .target_dataslot_ack(ca),.target_dataslot_done(cd),.target_dataslot_err(ce),.target_dataslot_id(slot),
 .target_dataslot_slotoffset(offset),.target_dataslot_bridgeaddr(source),.target_dataslot_length(length),
 .target_buffer_param_struct(32'd0),.target_buffer_resp_struct(32'd0),.datatable_addr(10'd0),.datatable_wren(1'b0),.datatable_data(32'd0));
reg [7:0] files[0:16383];reg [31:0] value,held_offset,held_source,held_length;reg [15:0] held_slot;reg held_write;
integer i,j,b,fd,ops=0,writes=0,base;
task tick(input integer n);repeat(n)begin @(posedge clk);#1;end endtask
task busget(input [31:0] a,output [31:0] v);begin @(negedge clk);addr=a;rd=1;tick(4);v=data;@(negedge clk);rd=0;tick(1);end endtask
task busput(input [31:0] a,input [31:0] v);begin @(negedge clk);addr=a;wdata=v;wr=1;tick(1);@(negedge clk);wr=0;tick(3);end endtask
task send_address(input [31:0] a);integer n;begin
 drive=1;clock_out=0;ss=0;tick(8);
 for(n=30;n>=0;n=n-2)begin clock_out=0;mosi_out=a[n+1];miso_out=a[n];tick(4);clock_out=1;tick(4);end
 clock_out=0;if(!a[0])drive=0;
end endtask
task spiget(input [31:0] a,output [31:0] v);integer n,limit;begin
 send_address(a);limit=0;while(serial.spis!==serial.ST_SEND_0&&limit<100)begin tick(1);limit=limit+1;end
 if(limit==100)$fatal(1,"SPI response absent");v=0;
 for(n=0;n<16;n=n+1)begin @(negedge spi_clock);#1;v={v[29:0],spi_mosi,spi_miso};end
 tick(8);ss=1;tick(12);drive=1;clock_out=0;
end endtask
task spiput(input [31:0] a,input [31:0] v);integer n;begin
 send_address(a|1);tick(8);for(n=30;n>=0;n=n-2)begin clock_out=0;mosi_out=v[n+1];miso_out=v[n];tick(4);clock_out=1;tick(4);end
 clock_out=0;tick(12);ss=1;tick(12);
end endtask
task get(input [31:0] a,output [31:0] v);begin if(SPI)spiget(a,v);else busget(a,v);end endtask
task put(input [31:0] a,input [31:0] v);begin if(SPI)spiput(a,v);else busput(a,v);end endtask
task dump;begin fd=$fopen("written.hex","w");for(i=0;i<16384;i=i+1)$fdisplay(fd,"%02x",files[i]);$fclose(fd);end endtask
task snapshot_at(input integer n);begin debug_source=(debug_source&32'hffffffc0)|n;tick(8);debug_source[31]=!debug_source[31];tick(8);end endtask
initial begin
 $readmemh("initial.hex",files);
 cmd.hstate=0;cmd.tstate=0;cmd.host_cmd_start=0;cmd.status_setup_done_1=0;cmd.target_dataslot_read_1=0;cmd.target_dataslot_write_1=0;cmd.target_dataslot_getfile_1=0;cmd.target_dataslot_openfile_1=0;
 ss=0;tick(1);ss=1;tick(70);
 if(COMMAND)begin setup=1;wait(cmd.target_0==32'h636d0140);busput(32'hf8001000,32'h6f6b0000);tick(8);end
 if(status!==0)$fatal(1,"not ready");run=1;
 if(MODE==2)begin debug_source[28]=1;if(HOLD>=0)begin debug_source[27]=1;debug_source[9:8]=HOLD;end tick(1);wait(dut.state!=dut.READY);#1;end
 else begin if(MODE==1)rb=1;else wb=1;tick(1);rb=0;wb=0;end
 while(!dut.terminal)begin
  wait(tr||tw||dut.terminal||status==8);
  if(status==8)begin
   if(dut.commands!==2+HOLD||dut.completed!=0||tr||tw)$fatal(1,"pause point incorrect");
   run=0;wb=1;rb=1;done=1;tick(100);if(status!==8||tr||tw)$fatal(1,"pause changed on buttons/reset");run=1;wb=0;rb=0;
   if(KILL)begin dump();$display("PASS paused prefix %d, external power cut simulated by new process",HOLD);$finish;end
   debug_source[26]=!debug_source[26];tick(1);wait(status!=8);#1;
  end else if(!dut.terminal)begin
   held_write=tw;held_slot=slot;held_offset=offset;held_source=source;held_length=length;
   if((slot!=16'h25&&slot!=16'h26)||offset<512||offset+length>1024||(held_write&&length!=128)||(!held_write&&length!=512))$fatal(1,"unsafe bounds");
   if(held_write&&dut.destination==(dut.valid_a&&(!dut.valid_b||dut.gen_a>=dut.gen_b)?0:dut.valid_b?1:2))$fatal(1,"writing newest valid file");
   if(ops==0)begin run=0;wb=1;rb=1;tick(5);run=1;wb=0;rb=0;if(offset!==held_offset||slot!==held_slot||length!==held_length||source!==held_source||dut.commands!=0)$fatal(1,"stale done ownership");end
   if(COMMAND)begin
    wait(cmd.target_0==(held_write?32'h636d0184:32'h636d0180));
    busget(32'hf8001020,value);if(value!=={16'd0,held_slot})$fatal(1,"command slot");
    busget(32'hf8001024,value);if(value!==held_offset)$fatal(1,"command offset");
    busget(32'hf8001028,value);if(value!==held_source)$fatal(1,"command address");
    busget(32'hf800102c,value);if(value!==held_length)$fatal(1,"command length");busput(32'hf8001000,32'h62750000);
   end
   done=0;tick(3);base=(held_slot-16'h25)*8192;
   if((INJECT==4&&ops==2)||(INJECT==7&&ops==6))begin
    tick(20010);done=1;run=0;wb=1;rb=1;tick(50);
    if(status!==7||tr||tw)$fatal(1,"timeout reopened");
   end else begin
    if(SPI&&held_write)spiget(held_source,value);
    for(j=0;j<held_length/4;j=j+1)begin
     if(held_write)begin
      get(SPI?held_source+4+j*4:held_source+j*4,value);
      for(b=0;b<4;b=b+1)files[base+held_offset+j*4+b]=value[31-b*8 -: 8];
     end else begin
      value={files[base+held_offset+j*4],files[base+held_offset+j*4+1],files[base+held_offset+j*4+2],files[base+held_offset+j*4+3]};
      if(INJECT==1&&ops==6&&j==12)value=value^32'h01000000;
      if(!(INJECT==2&&ops==6&&j==127))put(held_source+j*4,value);
     end
    end
    error=(INJECT==3&&ops==2)||(INJECT==5&&ops==0)||(INJECT==6&&ops==6)?3'd2:3'd0;
    if(COMMAND)busput(32'hf8001000,32'h6f6b0000|error);else begin done=1;tick(1);end
    error=0;if(held_write)writes=writes+1;ops=ops+1;
   end
  end
 end
 tick(3);
 if(status!==EXPECT_STATUS)$fatal(1,"wrong status %d reason %h",status,dut.reason);
 if(EXPECT_STATUS==4&&dut.selected_gen!==EXPECT_GEN)$fatal(1,"wrong generation %h expected %h",dut.selected_gen,EXPECT_GEN);
 if(INJECT==0&&EXPECT_STATUS==4&&dut.commands!==(MODE==1?2:2+5*(MODE==2?1:COMMITS)))$fatal(1,"command total");
 if(MODE==1&&writes!=0)$fatal(1,"cold wrote");
 if(EXPECT_STATUS==4&&MODE!=1)for(i=0;i<(MODE==2?1:COMMITS);i=i+1)begin
  snapshot_at(i);
  if(snapshot[511:480]!==32'h53445705||snapshot[478]!==1||snapshot[467:464]!==4)$fatal(1,"debug header");
  if((snapshot[127:96]&32'hfffffff7)!==32'h80000007||snapshot[31:0]==0)$fatal(1,"history record");
 end
 snapshot_at(0);value=snapshot[127:96];debug_source[5:0]=63;tick(10);if(snapshot[127:96]!==value)$fatal(1,"unheld snapshot");
 wb=1;rb=1;run=0;tick(50);if(tr||tw||status!==EXPECT_STATUS)$fatal(1,"terminal reopened");
 dump();$display("PASS B005 mode=%d injection=%d hold=%d command=%d spi=%d saves=%d cmds=%d generation=%h",MODE,INJECT,HOLD,COMMAND,SPI,completed,dut.commands,dut.selected_gen);$finish;
end
initial begin #500000000;$fatal(1,"watchdog");end
endmodule
