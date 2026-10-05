`default_nettype none
// B003: bounded existing-file batch, one command owner, retained results.
// Reconfiguration is the only timeout recovery and the next-session boundary.
module lab_batch #(parameter integer TIMEOUT_CYCLES = 742500000)(
 input wire clk, reset_n, write_button, read_button,
 input wire [31:0] bridge_addr, input wire bridge_rd, bridge_wr,
 input wire [31:0] bridge_wr_data, output wire [31:0] bridge_rd_data,
 output reg target_read = 0, target_write = 0,
 output wire [15:0] slot_id, output wire [31:0] slot_offset, source_addr, transfer_length,
 input wire target_done, input wire [2:0] target_err,
 output reg [3:0] status = 1,
 output wire [31:0] generation, loaded_generation,
 output reg [31:0] completed = 0,
 output reg [2:0] last_error = 0,
 output reg [31:0] elapsed_cycles = 0,
 input wire [31:0] debug_source, output reg [255:0] debug_probe = 0
);
 localparam [31:0] TX_BASE=32'h10000000, RX_BASE=32'h10002000;
 localparam [3:0] BOOT=0, IDLE=1, PREPARE=2, ISSUE=3, CLEAR_DONE=4,
  WAIT_DONE=5, FETCH=6, COMPARE=7, RECORD=8, NEXT=9, FINISHED=10, FAULT=11;
 reg [3:0] state=BOOT;
 reg [6:0] boot_index=0;
 reg [4:0] case_index=0;
 reg [1:0] ordinal=1;
 reg [9:0] word_index=0;
 reg cold=0, is_read=0, case_bad=0, mismatch=0;
 reg wr_previous=0, rd_previous=0;
 reg [7:0] passed=0, failed=0, command_count=0;
 reg [31:0] flags=0, write_cycles=0;
 reg [31:0] tx_mem[0:1023], rx_mem[0:1023];
 reg [1023:0] received=0;
 reg [31:0] response_q=0, rx_q=0;
 reg [31:0] log_flags[0:95], log_write[0:95], log_read[0:95];
 reg [31:0] debug_s1=0, debug_s2=0, debug_s3=0;
 reg snap_previous=0, start_previous=0, cold_previous=0;
 `include "batch_cases.vh"
 wire [12:0] max_length=case_max_length(case_index);
 wire [12:0] write_length=case_length(case_index,ordinal);
 wire [10:0] word_count=({1'b0,max_length}+3)>>2;
 wire [6:0] log_index=case_index*3+ordinal-1;
 wire [4:0] selected_case=debug_s3[4:0];
 wire [1:0] selected_ordinal=debug_s3[6:5]+1'b1;
 wire [6:0] selected_log=selected_case*3+selected_ordinal-1;
 wire terminal=(state==FINISHED || state==FAULT || state==IDLE);
 function automatic [7:0] pattern_byte(input [4:0] c,input [1:0] p,input [12:0] n);
 begin case(case_pattern(c))
  0: pattern_byte=0;
  1: pattern_byte=8'hff;
  2: pattern_byte=n[0]?8'h55:8'haa;
  3: pattern_byte=n+c+p;
  default: pattern_byte=n[7:0] ^ {3'b0,n[12:8]} ^ (c*8'd17) ^ (p*8'd73) ^ 8'h3d;
 endcase end endfunction
 function automatic [31:0] pattern_word(input [4:0] c,input [1:0] p,input [9:0] w);
 integer b;
 begin for(b=0;b<4;b=b+1)
  pattern_word[31-b*8 -: 8]=pattern_byte(c,p,{1'b0,w,2'b0}+b);
 end endfunction
 // After a shrinking overwrite, bytes beyond the new length belong to pass 1.
 function automatic [31:0] expected_word(input [4:0] c,input [1:0] p,input [9:0] w);
 integer b;
 reg [12:0] n;
 begin for(b=0;b<4;b=b+1)begin
  n={1'b0,w,2'b0}+b;
  expected_word[31-b*8 -: 8]=pattern_byte(c,
   n<case_length(c,p)?p:2'd1,n);
 end end endfunction
 function automatic [31:0] byte_mask(input [12:0] length,input [9:0] w);
 integer b;
 begin for(b=0;b<4;b=b+1)
  byte_mask[31-b*8 -: 8]=({1'b0,w,2'b0}+b<length)?8'hff:8'h00;
 end endfunction
 assign generation={27'd0,case_index}+1;
 assign loaded_generation={24'd0,passed};
 assign slot_id=16'h23;
 assign slot_offset=case_offset(case_index);
 assign source_addr=is_read?RX_BASE:TX_BASE;
 assign transfer_length=is_read?{19'd0,max_length}:{19'd0,write_length};
 assign bridge_rd_data=response_q;
 always @(posedge clk)begin
  // Synchronous single-clock RAM ports preserve the proven held APF response.
  if(bridge_rd)begin
   if(bridge_addr>=TX_BASE && bridge_addr<TX_BASE+4096 && bridge_addr[1:0]==0)
    response_q<=tx_mem[bridge_addr[11:2]];
   else response_q<=0;
  end
  if(bridge_wr && bridge_addr>=RX_BASE && bridge_addr<RX_BASE+4096 &&
   bridge_addr[1:0]==0 && is_read && (state==CLEAR_DONE || state==WAIT_DONE))begin
   rx_mem[bridge_addr[11:2]]<=bridge_wr_data;
   received[bridge_addr[11:2]]<=1;
  end
  rx_q<=rx_mem[word_index];
  target_read<=0;target_write<=0;
  wr_previous<=write_button;rd_previous<=read_button;
  debug_s1<=debug_source;debug_s2<=debug_s1;debug_s3<=debug_s2;
  snap_previous<=debug_s3[31];start_previous<=debug_s3[30];cold_previous<=debug_s3[29];
  // Index is held by the host before toggling snapshot. Packet then stays fixed.
  // Retained result reads are accepted only at terminal states, not mid-update.
  if(debug_s3[31]!=snap_previous)begin
   debug_probe<={32'h53445703,
    debug_s3[31],cold,terminal,selected_case,selected_ordinal,18'd0,status,
    {command_count,failed,passed,completed[7:0]},case_offset(selected_case),
    {3'd0,case_max_length(selected_case),3'd0,case_length(selected_case,selected_ordinal)},
    terminal && selected_ordinal!=0 && selected_ordinal<=case_passes(selected_case)?log_flags[selected_log]:32'h80000000,
    terminal && selected_ordinal!=0 && selected_ordinal<=case_passes(selected_case)?log_write[selected_log]:32'd0,
    terminal && selected_ordinal!=0 && selected_ordinal<=case_passes(selected_case)?log_read[selected_log]:32'd0};
  end
  case(state)
   BOOT: begin
    log_flags[boot_index]<=0;log_write[boot_index]<=0;log_read[boot_index]<=0;
    if(boot_index==95)begin state<=IDLE;status<=0;end
    else boot_index<=boot_index+1'b1;
   end
   IDLE: if(reset_n && ((write_button&&!wr_previous)||(read_button&&!rd_previous)||
    debug_s3[30]!=start_previous||debug_s3[29]!=cold_previous))begin
    cold<=!((write_button&&!wr_previous)||debug_s3[30]!=start_previous);
    is_read<=!((write_button&&!wr_previous)||debug_s3[30]!=start_previous);
    ordinal<=!((write_button&&!wr_previous)||debug_s3[30]!=start_previous)?case_passes(0):2'd1;
    case_index<=0;word_index<=0;received<=0;case_bad<=0;mismatch<=0;
    flags<=0;write_cycles<=0;state<=PREPARE;status<=1;
   end
   PREPARE: begin
    tx_mem[word_index]<=pattern_word(case_index,ordinal,word_index);
    if({1'b0,word_index}==word_count-1)begin state<=ISSUE;end
    else word_index<=word_index+1'b1;
   end
   ISSUE: begin
    elapsed_cycles<=0;received<=0;mismatch<=0;
    target_read<=is_read;target_write<=!is_read;
    status<=2;state<=CLEAR_DONE;
   end
   CLEAR_DONE,WAIT_DONE: begin
    elapsed_cycles<=elapsed_cycles+1'b1;
    if(elapsed_cycles>=TIMEOUT_CYCLES-1)begin
     state<=FAULT;status<=7;
     log_flags[log_index]<=flags|32'h00008000|(is_read?32'h2000:32'h1000);
     log_write[log_index]<=is_read?write_cycles:elapsed_cycles;
     log_read[log_index]<=is_read?elapsed_cycles:32'd0;
    end else if(state==CLEAR_DONE)begin
     if(!target_done)state<=WAIT_DONE;
    end else if(target_done)begin
     command_count<=command_count+1'b1;last_error<=target_err;
     if(target_err!=0)begin
      flags<=flags|(is_read?32'h200:32'h100)|({29'd0,target_err}<<(is_read?20:16));
      case_bad<=1;
      if(!is_read)write_cycles<=elapsed_cycles;
      state<=RECORD;
     end else if(is_read)begin
      flags<=flags|32'h2;word_index<=0;state<=FETCH;
     end else begin
      flags<=flags|32'h1;write_cycles<=elapsed_cycles;
      is_read<=1;state<=ISSUE;
     end
    end
   end
   FETCH: state<=COMPARE;
   COMPARE: begin
    if(!received[word_index] ||
     ((rx_q^expected_word(case_index,ordinal,word_index)) & byte_mask(max_length,word_index))!=0)
     mismatch<=1;
    if({1'b0,word_index}==word_count-1)begin
     if(mismatch || !received[word_index] ||
      ((rx_q^expected_word(case_index,ordinal,word_index)) & byte_mask(max_length,word_index))!=0)begin
      flags<=flags|32'h400;case_bad<=1;
     end else flags<=flags|32'h4;
     state<=RECORD;
    end else begin word_index<=word_index+1'b1;state<=FETCH;end
   end
   RECORD: begin
    log_flags[log_index]<=flags|32'h80000000;
    log_write[log_index]<=write_cycles;
    log_read[log_index]<=is_read?elapsed_cycles:32'd0;
    state<=NEXT;
   end
   NEXT: begin
    if(!cold && ordinal<case_passes(case_index) && flags[9:8]==0)begin
     ordinal<=ordinal+1'b1;is_read<=0;flags<=0;write_cycles<=0;
     word_index<=0;state<=PREPARE;status<=1;
    end else begin
     completed<=completed+1'b1;
     if(case_bad)failed<=failed+1'b1;else passed<=passed+1'b1;
     if(case_index==31)begin
      state<=FINISHED;status<=case_bad||failed!=0?5:4;
     end else begin
      case_index<=case_index+1'b1;ordinal<=cold?case_passes(case_index+1'b1):2'd1;
      word_index<=0;flags<=0;write_cycles<=0;case_bad<=0;
      is_read<=cold;state<=PREPARE;status<=1;
     end
    end
   end
   FINISHED: begin end // Prevent accidental repeated writes to collected regions.
   FAULT: begin end // Never release ownership on timeout, reset or late DONE.
   default: begin state<=FAULT;status<=7;end
  endcase
 end
endmodule
`default_nettype wire
