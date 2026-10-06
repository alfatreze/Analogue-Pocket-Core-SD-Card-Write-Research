`default_nettype none
// B007: isolated active APF data-slot write interruption probe.
// No auto-initialization, retry, repair, or write before a successful cold read.
module lab_powercut #(
    parameter integer FILE_BYTES = 262144,
    parameter integer TIMEOUT_CYCLES = 742500000
)(
    input wire clk, reset_n, write_button, read_button,
    input wire [31:0] bridge_addr, input wire bridge_rd, bridge_wr,
    input wire [31:0] bridge_wr_data, output wire [31:0] bridge_rd_data,
    output reg target_read = 0, target_write = 0,
    input wire target_ack,
    output wire [15:0] slot_id, output wire [31:0] slot_offset, source_addr, transfer_length,
    input wire target_done, input wire [2:0] target_err,
    output reg [3:0] status = 1,
    output reg [31:0] generation = 0, output reg [31:0] loaded_generation = 0,
    output reg [31:0] completed = 0, output reg [2:0] last_error = 0,
    output reg [31:0] elapsed_cycles = 0,
    input wire [31:0] debug_source, output reg [511:0] debug_probe = 0
);
 localparam [31:0] TX_BASE=32'h10000000, RX_BASE=32'h10040000;
 localparam [16:0] WORDS=FILE_BYTES/4;
 localparam [4:0] BOOT_CLEAR=0, READY=1, ISSUE_WRITE=2, ISSUE_READ=3,
   CLEAR_DONE=4, WAIT_DONE=5, CLEAR_MASK=6, SCAN_MASK=7,
   SCAN_CHECK=8, PASS=9, FAULT=10;
 reg [4:0] state=BOOT_CLEAR;
 reg [16:0] clear_index=0, scan_index=0, received_count=0;
 reg [31:0] operation=0, commands=0, read_tag=0, rx_first=0, rx_last=0;
 reg write_tag=0, stop_pending=0;
 reg [31:0] response_q=0, ds1=0, ds2=0, ds3=0;
 // Direct-address, one-bit coverage RAM.  A vector with variable bit writes
 // becomes a huge decoder/mux network on Cyclone V; this maps to M10K RAM.
 (* ramstyle = "M10K" *) reg received [0:65535];
 reg received_scan_bit=0;
 reg [31:0] elapsed=0;
 reg missing_seen=0;
 reg wr_prev=0, rd_prev=0, snap_prev=0;
 reg selected_valid=0, candidate0=1, candidate1=1;
 reg can_write=0, is_read=0, active=0;
 reg [31:0] last_bridge_address=0;
 wire [31:0] rx_word_index=(bridge_addr-RX_BASE)>>2;
 wire [31:0] tx_word_index=(bridge_addr-TX_BASE)>>2;
 wire stop_now=stop_pending || (read_button&&!rd_prev);
 wire receive_word=bridge_wr && bridge_addr>=RX_BASE &&
   bridge_addr<RX_BASE+FILE_BYTES && bridge_addr[1:0]==0 &&
   (state==CLEAR_DONE || state==WAIT_DONE) && is_read;

 // Single simple-dual-port RAM: the write port records incoming address or
 // clears the bitmap, while the synchronous read port scans after target DONE.
 always @(posedge clk) begin
   if(receive_word) received[rx_word_index[15:0]]<=1'b1;
   else if(state==BOOT_CLEAR || state==CLEAR_MASK)
     received[clear_index[15:0]]<=1'b0;
   if(state==SCAN_MASK) received_scan_bit<=received[scan_index[15:0]];
 end

 function automatic [31:0] image_word(input image_tag, input [31:0] index);
   reg [31:0] value;
   begin
     case(index)
       0: value=32'h41504357; // "APCW"
       1: value=32'h30303700; // "007\0"
       2: value=image_tag?32'd1:32'd0;
       3: value=FILE_BYTES;
       default: value=(index*32'h9e3779b1) ^ ({31'd0,image_tag}*32'h85ebca6b) ^ 32'hb007c0de;
     endcase
     image_word=value;
   end
 endfunction
 function automatic [31:0] image_byte(input image_tag, input [31:0] index);
   reg [31:0] word_index;
   reg [1:0] lane;
   reg [31:0] word_value;
   begin
     word_index=index>>2; lane=index[1:0]; word_value=image_word(image_tag,word_index);
     image_byte=word_value[31-lane*8 -: 8];
   end
 endfunction

 assign slot_id=16'h27;
 assign slot_offset=0;
 assign transfer_length=FILE_BYTES;
 assign source_addr=is_read?RX_BASE:TX_BASE;
 assign bridge_rd_data=response_q;
 always @(posedge clk) begin
   ds1<=debug_source; ds2<=ds1; ds3<=ds2;
   rd_prev<=read_button; wr_prev<=write_button;
   snap_prev<=ds3[31];
   if(!is_read && read_button && !rd_prev &&
      (state==ISSUE_WRITE || state==CLEAR_DONE || state==WAIT_DONE))stop_pending<=1;
   if(bridge_rd) begin
     if(bridge_addr>=TX_BASE && bridge_addr<TX_BASE+FILE_BYTES && bridge_addr[1:0]==0)
       response_q<=image_word(write_tag,tx_word_index);
     else response_q<=0;
   end
   if(receive_word) begin
     received_count<=received_count+1'b1;
     last_bridge_address<=bridge_addr;
     if(received_count==0)rx_first<=bridge_addr;
     rx_last<=bridge_addr;
     if(bridge_wr_data!=image_word(1'b0,rx_word_index))candidate0<=0;
     if(bridge_wr_data!=image_word(1'b1,rx_word_index))candidate1<=0;
     if(rx_word_index==2)read_tag<=bridge_wr_data;
   end
   target_read<=0; target_write<=0;
   if(ds3[31]!=snap_prev) begin
     debug_probe<={32'h53445707,
       ds3[31],active,is_read,selected_valid,can_write,3'd0,status,state,last_error,12'd0,
       operation,completed,commands,elapsed,{15'd0,received_count},read_tag,last_bridge_address,
       rx_first,rx_last,source_addr,transfer_length,
       target_done,target_ack,target_read,target_write,target_err,candidate1,candidate0,23'd0,
       {15'd0,WORDS},32'd0};
   end
   case(state)
     BOOT_CLEAR: begin
       if(clear_index==WORDS-1) begin clear_index<=0;state<=READY;status<=0; end
       else clear_index<=clear_index+1'b1;
     end
     READY: begin
       active<=0;is_read<=0;
       if(reset_n && (read_button&&!rd_prev)) begin
         is_read<=1;status<=1;missing_seen<=0;state<=CLEAR_MASK;
       end else if(reset_n && (write_button&&!wr_prev) && can_write) begin
         operation<=operation+1'b1;generation<=operation+1'b1;
         write_tag<=!loaded_generation[0];stop_pending<=0;
         is_read<=0;status<=8;state<=ISSUE_WRITE;
       end
     end
     CLEAR_MASK: begin
       if(clear_index==WORDS-1) begin
         clear_index<=0;received_count<=0;candidate0<=1;candidate1<=1;
         read_tag<=0;rx_first<=0;rx_last<=0;state<=ISSUE_READ;
       end else clear_index<=clear_index+1'b1;
     end
     ISSUE_WRITE,ISSUE_READ: begin
       elapsed<=0;elapsed_cycles<=0;active<=1;
       target_read<=state==ISSUE_READ;target_write<=state==ISSUE_WRITE;
       is_read<=state==ISSUE_READ;state<=CLEAR_DONE;
     end
     CLEAR_DONE,WAIT_DONE: begin
       elapsed<=elapsed+1'b1;elapsed_cycles<=elapsed+1'b1;
       if(!is_read && target_ack && !target_done)status<=2;
       if(elapsed>=TIMEOUT_CYCLES-1) begin
         state<=FAULT;status<=7;active<=1;last_error<=3'd7;
       end else if(state==CLEAR_DONE) begin
         if(!target_done)state<=WAIT_DONE;
       end else begin
         if(target_done) begin
         commands<=commands+1'b1;last_error<=target_err;active<=0;
         if(target_err!=0) begin state<=FAULT;status<=6;last_error<=target_err;end
         else if(is_read) begin scan_index<=0;state<=SCAN_MASK;status<=3;end
         else begin
           completed<=completed+1'b1;loaded_generation<=write_tag;selected_valid<=1;
           if(stop_now) begin status<=4;state<=READY;stop_pending<=0;end
           else begin operation<=operation+1'b1;generation<=operation+1'b1;write_tag<=~write_tag;status<=8;state<=ISSUE_WRITE;end
         end
         end
       end
     end
     SCAN_MASK: begin
       state<=SCAN_CHECK;
     end
     SCAN_CHECK: begin
       if(!received_scan_bit)missing_seen<=1;
       if(scan_index==WORDS-1) begin
         if(received_count==WORDS && !missing_seen && received_scan_bit && (candidate0||candidate1)) begin
           selected_valid<=1;loaded_generation<=candidate1?1:0;
           can_write<=1;status<=5;state<=READY;
         end else begin
           selected_valid<=0;can_write<=0;status<=6;state<=FAULT;last_error<=3'd4;
         end
       end else begin scan_index<=scan_index+1'b1;state<=SCAN_MASK;end
     end
     PASS: begin end
     FAULT: begin active<=active;can_write<=0;end
     default: begin state<=FAULT;status<=7;can_write<=0;end
   endcase
 end
endmodule
`default_nettype wire
