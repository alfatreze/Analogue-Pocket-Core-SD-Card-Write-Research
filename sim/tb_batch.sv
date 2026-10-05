`timescale 1ns/1ps
module tb_batch;
parameter integer COLD=0, INJECT=0, COMMAND=0, JTAG=0;
reg clk=0;always #5 clk=~clk;
reg run=0, wb=0, rb=0, done=1;
reg [2:0] error=0;
reg [31:0] addr=0,wdata=0,debug_source=0;
reg rd=0,wr=0;
wire [31:0] pdata,cdata;
wire [31:0] data=addr[31:24]==8'hf8 ? cdata:pdata;
wire cd,ca;wire [2:0] ce;reg setup=0;wire host_reset;
wire [31:0] offset,source,length,completed,passed,case_number;
wire [15:0] slot;
wire tr,tw;
wire [3:0] status;
wire [255:0] snapshot;
lab_batch #(.TIMEOUT_CYCLES(20000)) dut(.clk(clk),.reset_n(run),
 .write_button(wb),.read_button(rb),.bridge_addr(addr),.bridge_rd(rd),.bridge_wr(wr),
 .bridge_wr_data(wdata),.bridge_rd_data(pdata),.target_read(tr),.target_write(tw),
 .slot_id(slot),.slot_offset(offset),.source_addr(source),.transfer_length(length),
 .target_done(COMMAND?cd:done),.target_err(COMMAND?ce:error),.status(status),.completed(completed),
 .loaded_generation(passed),.generation(case_number),.debug_source(debug_source),.debug_probe(snapshot));
core_bridge_cmd cmd(.clk(clk),.reset_n(host_reset),.bridge_endian_little(1'b0),
 .bridge_addr(addr),.bridge_rd(rd),.bridge_rd_data(cdata),.bridge_wr(wr),.bridge_wr_data(wdata),
 .status_boot_done(setup),.status_setup_done(setup),.status_running(run),
 .dataslot_requestread_ack(1'b1),.dataslot_requestread_ok(1'b1),
 .dataslot_requestwrite_ack(1'b1),.dataslot_requestwrite_ok(1'b1),
 .savestate_supported(1'b0),.savestate_addr(32'd0),.savestate_size(32'd0),.savestate_maxloadsize(32'd0),
 .savestate_start_ack(1'b0),.savestate_start_busy(1'b0),.savestate_start_ok(1'b0),.savestate_start_err(1'b0),
 .savestate_load_ack(1'b0),.savestate_load_busy(1'b0),.savestate_load_ok(1'b0),.savestate_load_err(1'b0),
 .target_dataslot_read(tr),.target_dataslot_write(tw),
 .target_dataslot_getfile(1'b0),.target_dataslot_openfile(1'b0),
 .target_dataslot_ack(ca),.target_dataslot_done(cd),.target_dataslot_err(ce),
 .target_dataslot_id(slot),.target_dataslot_slotoffset(offset),.target_dataslot_bridgeaddr(source),
 .target_dataslot_length(length),.target_buffer_param_struct(32'd0),.target_buffer_resp_struct(32'd0),
 .datatable_addr(10'd0),.datatable_wren(1'b0),.datatable_data(32'd0));
reg [7:0] file_bytes[0:262143];
reg [31:0] value,saved_offset,saved_source,saved_length;
integer i,j,b,fd,ops=0;
task tick(input integer n);repeat(n)begin @(posedge clk);#1;end endtask
task get(input [31:0] a,output [31:0] v);
begin @(negedge clk);addr=a;rd=1;tick(4);v=data;@(negedge clk);rd=0;tick(1);end endtask
task put(input [31:0] a,input [31:0] v);
begin @(negedge clk);addr=a;wdata=v;wr=1;tick(1);@(negedge clk);wr=0;tick(3);end endtask
task capture(input [4:0] c,input [1:0] p);
begin
 debug_source={25'd0,p,c};tick(8);debug_source[31]=1;tick(8);
end endtask
initial begin
 for(i=0;i<262144;i=i+1)file_bytes[i]=8'ha5;
 if(COLD && INJECT!=5)$readmemh("batch-written.hex",file_bytes);
 cmd.hstate=0;cmd.tstate=0;cmd.host_cmd_start=0;
 cmd.status_setup_done_1=0;cmd.target_dataslot_read_1=0;cmd.target_dataslot_write_1=0;
 cmd.target_dataslot_getfile_1=0;cmd.target_dataslot_openfile_1=0;
 tick(100);
 if(COMMAND)begin
  setup=1;wait(cmd.target_0==32'h636d0140);put(32'hf8001000,32'h6f6b0000);tick(8);
 end
 if(status!==0)$fatal(1,"batch boot not ready");
 run=1;
 if(JTAG)begin debug_source[COLD?29:30]=1;tick(1);end
 else begin if(COLD)rb=1;else wb=1;tick(1);rb=0;wb=0;end
 while(completed<32 && status!=7)begin
  wait(tr||tw||status==7||completed==32);
  if(status==7||completed==32)begin end
  else begin
   saved_offset=offset;saved_source=source;saved_length=length;
   if(slot!==16'h23 || length<1 || length>4096 || offset+length>262144)
    $fatal(1,"out of bounds request");
   if(ops==0)begin
    // A stale completion and reset/buttons cannot complete or mutate the request.
    run=0;wb=1;rb=1;tick(5);run=1;wb=0;rb=0;
    if(completed!=0 || offset!==saved_offset || source!==saved_source || length!==saved_length)
     $fatal(1,"stale DONE or ownership failure");
   end
   if(COMMAND)begin
    wait(cmd.target_0==(saved_source==32'h10000000 ? 32'h636d0184:32'h636d0180));
    get(32'hf8001020,value);if(value!==32'h23)$fatal(1,"command slot");
    get(32'hf8001024,value);if(value!==saved_offset)$fatal(1,"command offset");
    get(32'hf8001028,value);if(value!==saved_source)$fatal(1,"command source");
    get(32'hf800102c,value);if(value!==saved_length)$fatal(1,"command length");
    put(32'hf8001000,32'h62750000);
   end
   done=0;tick(3);
   if(INJECT==4 && case_number==8 && saved_source==32'h10002000)begin
    tick(20010);done=1;tick(5);wb=1;rb=1;run=0;tick(20);
    if(status!==7 || tr || tw || completed!==7)$fatal(1,"timeout reopened or advanced");
   end else begin
    for(j=0;j<(saved_length+3)/4;j=j+1)begin
     if(saved_source==32'h10000000)begin
      get(saved_source+j*4,value);
      for(b=0;b<4;b=b+1)if(j*4+b<saved_length)
       file_bytes[saved_offset+j*4+b]=value[31-b*8 -: 8];
     end else begin
      value=0;
      for(b=0;b<4;b=b+1)if(j*4+b<saved_length)
       value[31-b*8 -: 8]=file_bytes[saved_offset+j*4+b];
      // Bytes beyond the request can be arbitrary and must be ignored.
      if(saved_length%4!=0 && j==(saved_length+3)/4-1)value=value|32'hff;
      if((INJECT==1 && case_number==8 && j==0)||(INJECT==8 && case_number==29 && dut.ordinal==1 && j==0))value=value^32'h01000000;
      if(!(INJECT==2 && case_number==8 && j==(saved_length+3)/4-1))
       put(saved_source+j*4,value);
     end
    end
    error=((INJECT==3 && case_number==8 && saved_source==32'h10002000)||(INJECT==6 && case_number==8 && saved_source==32'h10000000)||(INJECT==7 && case_number==29 && saved_source==32'h10002000))?3'd2:3'd0;
    if(COMMAND)put(32'hf8001000,32'h6f6b0000|error);
    else begin done=1;tick(1);end
    error=0;ops=ops+1;
   end
  end
 end
 tick(1);
 if(INJECT==4)begin
  capture(7,0);
  if(!snapshot[15+64])$fatal(1,"timeout not retained");
 end else begin
  if(completed!==32 || passed!==(INJECT==0?32:INJECT==5?0:31) || status!==(INJECT==0?4:5))
   $fatal(1,"wrong summary status=%d completed=%d passed=%d",status,completed,passed);
  if(ops!=(COLD?32:INJECT==6?75:INJECT==7?72:76))$fatal(1,"wrong command total %d",ops);
  capture(INJECT==7||INJECT==8?5'd28:INJECT?5'd7:5'd28,INJECT?2'd0:2'd2);
  if(snapshot[255:224]!==32'h53445703 || !snapshot[223] || !snapshot[221])$fatal(1,"snapshot handshake");
  if(INJECT==0 && snapshot[95:64] !== (COLD?32'h80000006:32'h80000007))
   $fatal(1,"retained result wrong %h",snapshot[95:64]);
  if(INJECT!=0 && (snapshot[95:64] & 32'h00000700)==0)$fatal(1,"error not retained");
  if(INJECT==0 && !COLD)begin
   fd=$fopen("batch-written.hex","w");
   for(i=0;i<262144;i=i+1)$fdisplay(fd,"%02x",file_bytes[i]);$fclose(fd);
  end
  value=snapshot[95:64];debug_source[4:0]=31;tick(10);
  if(snapshot[95:64]!==value)$fatal(1,"snapshot changed without handshake");
  capture(0,3); // Encoded ordinal 4 wraps to 0 and must be rejected, not index RAM.
  if(snapshot[95:64]!==32'h80000000)$fatal(1,"invalid result index not rejected");
  wb=1;rb=1;tick(100);
  if(completed!==32||tr||tw)$fatal(1,"finished session reopened");
 end
 $display("PASS B003 cold=%d inject=%d commands=%d",COLD,INJECT,ops);$finish;
end
initial begin #20000000;$fatal(1,"batch watchdog");end
endmodule
