`timescale 1ns/1ps
module tb_b008_mailbox;
 reg c=0,e=0,rst=0,cyc=0,stb=0,we=0;reg[5:0]addr=0;reg[31:0]wd=0;reg[3:0]sel=15;wire ack;wire[31:0]rd;wire wp,rp;
 reg[3:0]status=0;reg[31:0]count=0;wire[31:0]tag=~count;
 always #5 c=~c;always #137 e=~e;
 b008_mailbox dut(.cpu_clk(c),.engine_clk(e),.cpu_reset(rst),.cyc(cyc),.stb(stb),.we(we),.addr(addr),.wdata(wd),.sel(sel),.ack(ack),.rdata(rd),.engine_status(status),.engine_error(3'd0),.engine_completed(count),.engine_tag(tag),.write_pulse(wp),.read_pulse(rp));
 integer pulses=0,acks=0;always @(posedge e)begin count<=count+1;if(rp||wp)pulses<=pulses+1;end
 task write(input[31:0]command,input integer hold);
  begin @(negedge c);cyc=1;stb=1;we=1;addr=0;wd=command;acks=0;
   repeat(hold)begin @(negedge c);if(ack)acks++;end
   if(acks!=1)$fatal(1,"Held beat ACK repeated %0d",acks);
   cyc=0;stb=0;we=0;@(negedge c);
  end
 endtask
 task finish_request;
  begin wait(!dut.pending);repeat(2)@(negedge c);end
 endtask
 integer before_seq,j;reg toggle;
 initial begin
  repeat(5)@(negedge e);
  write(5,8);finish_request();if(dut.locked)$fatal(1,"Recovery");
  before_seq=dut.sequence_count;write(1,16);toggle=dut.request_toggle;
  write(2,8);
  if(dut.request_toggle!=toggle || dut.command!=1 || dut.rejected!=1 || dut.local_error!=1)$fatal(1,"Pending request was replaced");
  finish_request();repeat(2)@(negedge e);if(dut.sequence_count!=before_seq+1||pulses!=1)$fatal(1,"Duplicate action seq=%0d before=%0d pulses=%0d code=%0d",dut.sequence_count,before_seq,pulses,dut.response_code);
  for(j=0;j<32;j++)begin write(4,8);finish_request();if(dut.snapshot_tag!==~dut.snapshot_completed)$fatal(1,"Incoherent response");end
  // Consecutive different registers may keep CYC/STB asserted (actual CPU case).
  @(negedge c);cyc=1;stb=1;we=0;addr=6'h1c;
  wait(ack);@(negedge c);if(rd!=1)$fatal(1,"Rejected counter read");
  addr=6'h08;@(negedge c);wait(ack);@(negedge c);
  if(rd!=dut.sequence_count)$fatal(1,"Next address beat was not acknowledged");
  cyc=0;stb=0;@(negedge c);
  // Incomplete CPU byte store must never issue an engine action.
  before_seq=dut.sequence_count;sel=1;write(1,8);sel=15;
  repeat(5)@(negedge e);if(dut.sequence_count!=before_seq||pulses!=1)$fatal(1,"Byte strobe published command");
  // Reset while a mailbox message is in transit keeps the toggle/ack alive.
  write(4,8);toggle=dut.request_toggle;
  @(negedge c);rst=1;repeat(10)@(negedge c);rst=0;finish_request();
  if(!dut.locked || dut.request_toggle!=toggle || dut.sequence_count!=before_seq+1)$fatal(1,"Reset lost pending delivery");
  write(2,8);if(dut.local_error!=2 || pulses!=1)$fatal(1,"Reset lock bypass");
  write(5,8);finish_request();if(dut.locked)$fatal(1,"Reset recovery");
  // A START still in transit when CPU reset arrives must not begin a write.
  status=5;before_seq=dut.sequence_count;write(2,8);
  @(negedge c);rst=1;repeat(4)@(negedge e);rst=0;finish_request();
  if(dut.sequence_count!=before_seq+1 || dut.response_code!=4 || pulses!=1 || !dut.locked)$fatal(1,"START escaped reset guard");
  write(5,8);finish_request();
  $display("PASS B008 mailbox held beat, pending rejection, coherent snapshots, byte strobes, reset in transit");$finish;
 end
 initial begin #1000000;$fatal(1,"Mailbox budget");end
endmodule
