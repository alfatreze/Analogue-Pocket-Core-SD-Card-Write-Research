`timescale 1ns/1ps
module tb_probe;
reg clk=0;
always #5 clk=~clk;
reg run=1,wr_button=0,rd_button=0;
reg [31:0] addr=0,wdata=0;
reg rd=0,wr=0;
wire [31:0] pdata,cdata;
wire [31:0] data=addr[31:24]==8'hf8 ? cdata : pdata;
wire t_read,t_write,t_done,t_ack;
wire [2:0] t_err,last_error;
wire [15:0] slot;
wire [31:0] offset,source,length,generation,loaded,completed,elapsed;
wire [3:0] status;
reg setup=0;
wire host_reset;
lab_probe #(.TIMEOUT_CYCLES(2000)) probe(
 .clk(clk),.reset_n(run),.write_button(wr_button),.read_button(rd_button),
 .bridge_addr(addr),.bridge_rd(rd),.bridge_wr(wr),.bridge_wr_data(wdata),.bridge_rd_data(pdata),
 .target_read(t_read),.target_write(t_write),.slot_id(slot),.slot_offset(offset),
 .source_addr(source),.transfer_length(length),.target_done(t_done),.target_err(t_err),
 .status(status),.generation(generation),.loaded_generation(loaded),.completed(completed),
 .last_error(last_error),.elapsed_cycles(elapsed));
core_bridge_cmd cmd(.clk(clk),.reset_n(host_reset),.bridge_endian_little(1'b0),
 .bridge_addr(addr),.bridge_rd(rd),.bridge_rd_data(cdata),.bridge_wr(wr),.bridge_wr_data(wdata),
 .status_boot_done(setup),.status_setup_done(setup),.status_running(run),
 .dataslot_requestread_ack(1'b1),.dataslot_requestread_ok(1'b1),
 .dataslot_requestwrite_ack(1'b1),.dataslot_requestwrite_ok(1'b1),
 .savestate_supported(1'b0),.savestate_addr(32'd0),.savestate_size(32'd0),.savestate_maxloadsize(32'd0),
 .savestate_start_ack(1'b0),.savestate_start_busy(1'b0),.savestate_start_ok(1'b0),.savestate_start_err(1'b0),
 .savestate_load_ack(1'b0),.savestate_load_busy(1'b0),.savestate_load_ok(1'b0),.savestate_load_err(1'b0),
 .target_dataslot_read(t_read),.target_dataslot_write(t_write),
 .target_dataslot_getfile(1'b0),.target_dataslot_openfile(1'b0),
 .target_dataslot_ack(t_ack),.target_dataslot_done(t_done),.target_dataslot_err(t_err),
 .target_dataslot_id(slot),.target_dataslot_slotoffset(offset),.target_dataslot_bridgeaddr(source),
 .target_dataslot_length(length),.target_buffer_param_struct(32'd0),.target_buffer_resp_struct(32'd0),
 .datatable_addr(10'd0),.datatable_wren(1'b0),.datatable_data(32'd0));
task tick(input integer count); repeat(count) begin @(posedge clk); #1; end endtask
task put(input [31:0] a,input [31:0] v);
 begin @(negedge clk);addr=a;wdata=v;wr=1;tick(1);@(negedge clk);wr=0;tick(3);end
endtask
task get(input [31:0] a,output [31:0] v);
 begin @(negedge clk);addr=a;rd=1;tick(4);v=data;@(negedge clk);rd=0;end
endtask
task request(input bit reading);
 begin @(negedge clk);if(reading)rd_button=1;else wr_button=1;tick(1);
 @(negedge clk);wr_button=0;rd_button=0;end
endtask
task await_command(input [15:0] code);
 integer limit;
 begin
  limit=0;
  while(cmd.target_0 !== {16'h636d,code} && limit<500)begin tick(1);limit=limit+1;end
  if(limit==500)$fatal(1,"command did not start %h",code);
 end
endtask
task await_status(input [3:0] expected);
 integer limit;
 begin
  limit=0;
  while(status!==expected && limit<2500)begin tick(1);limit=limit+1;end
  if(limit==2500)$fatal(1,"wrong status wanted %d got %d",expected,status);
 end
endtask
reg [31:0] file_words[0:15];
reg [31:0] value,saved_addr;
integer i,handle;
task transfer_write(input integer gen);
 begin
  await_command(16'h0184);
  get(32'hf8001020,value);if(value!==32'h22)$fatal(1,"wrong slot");
  get(32'hf8001024,value);if(value!==0)$fatal(1,"wrong offset");
  get(32'hf8001028,value);if(value!==32'h10000000)$fatal(1,"wrong source");saved_addr=value;
  get(32'hf800102c,value);if(value!==64)$fatal(1,"wrong length");
  put(32'hf8001000,32'h62750000);
  for(i=0;i<16;i=i+1)begin get(saved_addr+i*4,value);file_words[i]=value;end
  if(file_words[3]!==gen)$fatal(1,"wrong generation");
  put(32'hf8001000,32'h6f6b0000);
  await_status(3);
 end
endtask
task transfer_read(input bit corrupt,input bit omit_last);
 begin
  await_command(16'h0180);
  get(32'hf8001028,value);if(value!==32'h10000100)$fatal(1,"RX mapping");
  put(32'hf8001000,32'h62750000);
  for(i=0;i<16-(omit_last?1:0);i=i+1)
   put(32'h10000100+i*4,(corrupt && i==6)?(file_words[i]^1):file_words[i]);
  put(32'hf8001000,32'h6f6b0000);
 end
endtask
initial begin
 // Intel FPGA fabric control registers without explicit initializers power up 0.
 // Make that vendor-template convention explicit only in this simulation.
 cmd.hstate=0;cmd.tstate=0;cmd.host_cmd_start=0;
 cmd.status_setup_done_1=0;cmd.target_dataslot_read_1=0;cmd.target_dataslot_write_1=0;
 cmd.target_dataslot_getfile_1=0;cmd.target_dataslot_openfile_1=0;
 tick(12);setup=1;await_command(16'h0140);put(32'hf8001000,32'h6f6b0000);tick(8);
 request(0);transfer_write(1);
 handle=$fopen("generation-1.hex","w");for(i=0;i<16;i=i+1)$fdisplay(handle,"%08x",file_words[i]);$fclose(handle);
 if(completed!==1)$fatal(1,"completion count");
 request(0);tick(5);if(status===3)$fatal(1,"stale DONE accepted");transfer_write(2);
 handle=$fopen("generation-2.hex","w");for(i=0;i<16;i=i+1)$fdisplay(handle,"%08x",file_words[i]);$fclose(handle);
 request(1);transfer_read(0,0);await_status(4);
 if(loaded!==2)$fatal(1,"read generation");
 request(1);transfer_read(1,0);await_status(5);
 request(1);transfer_read(0,1);await_status(5);
 request(0);await_command(16'h0184);put(32'hf8001000,32'h6f6b0002);await_status(6);
 if(last_error!==2)$fatal(1,"wrong error");
 request(0);await_command(16'h0184);saved_addr=source;value=generation;
 // Buttons and host Reset Enter cannot mutate an outstanding payload/command.
 request(0);run=0;tick(100);run=1;
 if(source!==saved_addr||generation!==value)$fatal(1,"ownership violated");
 await_status(7);put(32'hf8001000,32'h6f6b0000);request(0);request(1);tick(100);
 if(status!==7||generation!==value||t_read||t_write)$fatal(1,"timeout reopened channel");
 $display("PASS real-template integration: payloads, stale DONE, read corruption, missing bytes, errors, timeout ownership");
 $finish;
end
initial begin #1000000;$fatal(1,"bench watchdog");end
endmodule
