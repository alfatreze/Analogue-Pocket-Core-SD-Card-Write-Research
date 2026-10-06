`timescale 1ns/1ps
module tb_powercut;
 localparam integer BYTES=262144, WORDS=BYTES/4;
 reg clk=0,reset_n=1,write_button=0,read_button=0;
 reg [31:0] bridge_addr=0,bridge_wr_data=0,debug_source=0;
 reg bridge_rd=0,bridge_wr=0,target_done=1;
 reg [2:0] target_err=0;
 reg target_ack=0;
 wire [31:0] bridge_rd_data,slot_offset,source_addr,transfer_length;
 wire [15:0] slot_id;
 wire target_read,target_write;
 wire [3:0] status;
 wire [31:0] generation,loaded_generation,completed,elapsed;
 wire [2:0] last_error;
 wire [511:0] debug_probe;
 integer i;
 reg [31:0] expected;
 always #5 clk=~clk;
 lab_powercut dut(.clk(clk),.reset_n(reset_n),.write_button(write_button),.read_button(read_button),
   .bridge_addr(bridge_addr),.bridge_rd(bridge_rd),.bridge_wr(bridge_wr),.bridge_wr_data(bridge_wr_data),
   .bridge_rd_data(bridge_rd_data),.target_read(target_read),.target_write(target_write),.target_ack(target_ack),
   .slot_id(slot_id),.slot_offset(slot_offset),.source_addr(source_addr),.transfer_length(transfer_length),
   .target_done(target_done),.target_err(target_err),.status(status),.generation(generation),
   .loaded_generation(loaded_generation),.completed(completed),.last_error(last_error),
   .elapsed_cycles(elapsed),.debug_source(debug_source),.debug_probe(debug_probe));

 task automatic press_b;
 begin @(negedge clk);read_button=1;@(negedge clk);read_button=0;end
 endtask
 task automatic press_a;
 begin @(negedge clk);write_button=1;@(negedge clk);write_button=0;end
 endtask
 function automatic [31:0] model_word(input integer tag,input integer n);
 begin
   case(n)
     0:model_word=32'h41504357;
     1:model_word=32'h30303700;
     2:model_word=tag;
     3:model_word=BYTES;
     default:model_word=(n*32'h9e3779b1) ^ (tag*32'h85ebca6b) ^ 32'hb007c0de;
   endcase
 end
 endfunction
 initial begin
   if($bits(debug_probe)!=512)$fatal(1,"JTAG probe width");
   wait(status==0);
   // A must not create a dataslot write before a complete cold validation.
   press_a(); repeat(4)@(posedge clk);
   if(target_write || completed!=0)$fatal(1,"write escaped cold-read gate");
   if(slot_id!=16'h27 || slot_offset!=0 || transfer_length!=BYTES)
     $fatal(1,"slot/length contract mismatch");
   press_b(); wait(target_read); @(negedge clk); target_done=0;
   for(i=0;i<WORDS;i=i+1)begin
     bridge_wr=1;bridge_addr=32'h10040000+i*4;bridge_wr_data=model_word(0,i);
     @(negedge clk);
   end
   bridge_wr=0;target_done=1;
   wait(status==5 || status==6);
   if(status!=5)$display("READ DIAG count=%0d words=%0d cand0=%b cand1=%b missing=%b last=%08x",dut.received_count,dut.WORDS,dut.candidate0,dut.candidate1,dut.missing_seen,dut.last_bridge_address);
   if(status!=5)$fatal(1,"baseline cold read rejected");
   if(loaded_generation!=0 || completed!=0 || !dut.can_write)
     $fatal(1,"valid baseline did not unlock writes");

   @(negedge clk);write_button=1;
   @(negedge clk);write_button=0;read_button=1; // ISSUE_WRITE is pending this edge.
   @(posedge clk);#1;
   if(!dut.stop_pending || !target_write || status!=8 || !dut.active)
     $fatal(1,"stop issue edge pending=%b target_write=%b status=%0d active=%b state=%0d",
       dut.stop_pending,target_write,status,dut.active,dut.state);
   @(negedge clk);read_button=0;
   if(source_addr!=32'h10000000 || transfer_length!=BYTES || slot_id!=16'h27)
     $fatal(1,"write source/size/id mismatch");
   // Check first, header, middle, and final aligned bridge word addresses.
   for(i=0;i<4;i=i+1)begin
     @(negedge clk);target_done=0;target_ack=1;bridge_addr=32'h10000000+i*4;bridge_rd=1;
     @(posedge clk);#1;expected=model_word(1,i);
     if(bridge_rd_data!==expected)$fatal(1,"header word %0d: %08x expected %08x",i,bridge_rd_data,expected);
   end
   @(negedge clk);bridge_addr=32'h10000000+(WORDS/2)*4;
   @(posedge clk);#1;
   if(bridge_rd_data!==model_word(1,WORDS/2))$fatal(1,"middle address stream mismatch");
   @(negedge clk);bridge_addr=32'h10000000+(WORDS-1)*4;
   @(posedge clk);#1;
   if(bridge_rd_data!==model_word(1,WORDS-1))$fatal(1,"last address stream mismatch");
   @(negedge clk);bridge_rd=0;
   if(status!=2)$fatal(1,"active cut cue requires target ack");

   // B requests a stop, but the request owner waits for genuine target DONE.
   if(!dut.stop_pending || status!=2)$fatal(1,"stop did not remain pending during write");
   @(negedge clk);target_done=1;
   wait(status==4);
   if(completed!=1 || dut.write_tag!=1 || dut.state!=1)
     $fatal(1,"write did not stop at completed-command boundary");
   @(negedge clk);debug_source[31]=1;repeat(5)@(posedge clk);#1;
   if(debug_probe[511:480]!=32'h53445707)$fatal(1,"SDW7 probe magic");

   // A duplicate cannot hide an omitted address even when raw write count is full.
   press_b();wait(target_read);@(negedge clk);target_done=0;
   for(i=0;i<WORDS;i=i+1)begin
     if(i!=123)begin
       bridge_wr=1;bridge_addr=32'h10040000+i*4;bridge_wr_data=model_word(1,i);
       @(negedge clk);
     end
   end
   bridge_wr=1;bridge_addr=32'h10040000;bridge_wr_data=model_word(1,0);
   @(negedge clk);bridge_wr=0;target_done=1;
   wait(status==6);
   if(dut.received_count!=WORDS || dut.can_write || dut.selected_valid)
     $fatal(1,"duplicate word masked missing-address read");
   $display("PASS B007 full-size read, active write bounds, completed-boundary stop, and missing-plus-duplicate rejection");
   $finish;
 end
 initial begin #30000000;$fatal(1,"global simulation timeout status=%0d state=%0d",status,dut.state);end
endmodule
