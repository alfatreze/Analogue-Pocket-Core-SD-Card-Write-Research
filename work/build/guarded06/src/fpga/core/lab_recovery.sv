`default_nettype none
// B005: two preallocated files, CRC-protected records, inactive-file updates.
// One session per configuration. A: 64 commits, B: recover only.
// JTAG single-save mode can hold before writing or after chunks 1/2/3.
module lab_recovery #(parameter integer TIMEOUT_CYCLES=742500000, COMMITS=64)(
 input wire clk,reset_n,write_button,read_button,
 input wire [31:0] bridge_addr, input wire bridge_rd,bridge_wr,
 input wire [31:0] bridge_wr_data, output wire [31:0] bridge_rd_data,
 output reg target_read=0,target_write=0,
 output wire [15:0] slot_id, output wire [31:0] slot_offset,source_addr,transfer_length,
 input wire target_done,input wire [2:0] target_err,
 output reg [3:0] status=1, output wire [31:0] generation,loaded_generation,
 output reg [31:0] completed=0,output reg [2:0] last_error=0,
 output reg [31:0] elapsed_cycles=0,
 input wire [31:0] debug_source,output reg [511:0] debug_probe=0
);
 localparam [31:0] TX=32'h10000000,RX=32'h10002000;
 localparam [7:0] BOOT=0,READY=1,ISSUE=2,CLEAR=3,WAIT=4,FETCH=5,SCAN=6,
  VALIDATE=7,SELECT=8,PREPARE=9,CRC_FETCH=10,CRC_SCAN=11,CRC_STORE=12,
  ARM=13,PAUSED=14,CHUNK_NEXT=15,COMMIT=16,NEXT=17,FINISHED=18,FAULT=19;
 reg [7:0] state=BOOT,reason=0;
 reg [5:0] boot_index=0,operation=0;
 reg [6:0] index=0;
 reg [1:0] mode=0,chunk=0,pause_point=0;
 reg hold_enabled=0,paused_once=0,scan_b=0,verifying=0,is_read=1,destination=0;
 reg valid_a=0,valid_b=0,same_records=1,malformed=0,missing=0,compare_bad=0;
 reg [63:0] gen_a=0,gen_b=0,selected_gen=0,new_gen=0,scan_gen=0;
 reg [31:0] crc=32'hffffffff,stored_crc=0,expected_crc=0,observed_crc=0,crc_a=0,crc_b=0;
 reg [31:0] commands=0,session_flags=0,total_cycles=0;
 reg [31:0] tx_mem[0:127],rx_mem[0:127],a_mem[0:127];
 reg [127:0] received=0;
 reg [31:0] tx_bridge_q=0,rx_q=0,a_q=0,tx_q=0,response_q=0;
 reg rd_pending=0,tx_selected=0;
 reg [31:0] log_flags[0:63],log_gen_lo[0:63],log_gen_hi[0:63],log_crc[0:63],log_cycles[0:63];
 reg [31:0] flags_q=0,gen_lo_q=0,gen_hi_q=0,crc_q=0,cycles_q=0;
 reg [31:0] ds1=0,ds2=0,ds3=0;
 reg snap_prev=0,start_prev=0,cold_prev=0,single_prev=0,resume_prev=0,wb_prev=0,rb_prev=0;
 wire terminal=state==READY||state==FINISHED||state==FAULT;
 wire [5:0] selected_index=ds3[5:0];
 function automatic [31:0] crc_word(input [31:0] previous,input [31:0] value);
 reg [31:0] c;integer b,k;
 begin c=previous;for(b=0;b<4;b=b+1)begin
 c=c^{24'd0,value[31-b*8 -: 8]};
 for(k=0;k<8;k=k+1)c=c[0]?(c>>1)^32'hedb88320:c>>1;
 end crc_word=c;end endfunction
 function automatic [31:0] record_word(input [6:0] word_no,input [63:0] g);
 integer b,n;reg [7:0] p;
 begin case(word_no)
  0:record_word=32'h53445235;1:record_word=32'h00010020;2:record_word=512;
  3:record_word=g[63:32];4:record_word=g[31:0];5:record_word=480;
  6,7:record_word=0;
  default:for(b=0;b<4;b=b+1)begin n=(word_no-8)*4+b;
   p=n^(n>>8)^g[7:0]^g[15:8]^8'h5b;record_word[31-b*8 -: 8]=p;end
 endcase end endfunction
 assign generation=selected_gen[31:0];
 assign loaded_generation={30'd0,valid_b,valid_a};
 assign slot_id=16'h25+(is_read?(verifying?destination:scan_b):destination);
 assign slot_offset=is_read?32'd512:32'd512+{23'd0,chunk,7'd0};
 assign source_addr=is_read?RX:TX+{23'd0,chunk,7'd0};
 assign transfer_length=is_read?32'd512:32'd128;
 assign bridge_rd_data=response_q;
 always @(posedge clk)begin
  tx_bridge_q<=tx_mem[bridge_addr[8:2]];rd_pending<=bridge_rd;
  tx_selected<=bridge_addr>=TX&&bridge_addr<TX+512&&bridge_addr[1:0]==0;
  if(rd_pending)response_q<=tx_selected?tx_bridge_q:32'd0;
  rx_q<=rx_mem[index];a_q<=a_mem[index];tx_q<=tx_mem[index];
  if(bridge_wr&&bridge_addr>=RX&&bridge_addr<RX+512&&bridge_addr[1:0]==0&&is_read&&(state==CLEAR||state==WAIT))begin
   rx_mem[bridge_addr[8:2]]<=bridge_wr_data;received[bridge_addr[8:2]]<=1;
  end
  flags_q<=log_flags[selected_index];gen_lo_q<=log_gen_lo[selected_index];gen_hi_q<=log_gen_hi[selected_index];crc_q<=log_crc[selected_index];cycles_q<=log_cycles[selected_index];
  ds1<=debug_source;ds2<=ds1;ds3<=ds2;
  snap_prev<=ds3[31];start_prev<=ds3[30];cold_prev<=ds3[29];single_prev<=ds3[28];resume_prev<=ds3[26];
  wb_prev<=write_button;rb_prev<=read_button;target_read<=0;target_write<=0;
  if(ds3[31]!=snap_prev)debug_probe<={32'h53445705,
   ds3[31],terminal,mode,8'd0,status,state,reason,
   {26'd0,selected_index},completed,commands,{30'd0,valid_b,valid_a},
   gen_a[31:0],gen_a[63:32],gen_b[31:0],gen_b[63:32],
   terminal&&mode!=1?gen_lo_q:selected_gen[31:0],terminal&&mode!=1?gen_hi_q:selected_gen[63:32],
   terminal&&mode!=1?flags_q:session_flags,
   terminal&&mode!=1?crc_q:expected_crc,observed_crc,
   terminal&&mode!=1?cycles_q:elapsed_cycles};
  case(state)
   BOOT:begin
    log_flags[boot_index]<=0;log_gen_lo[boot_index]<=0;log_gen_hi[boot_index]<=0;log_crc[boot_index]<=0;log_cycles[boot_index]<=0;
    if(boot_index==63)begin state<=READY;status<=0;end else boot_index<=boot_index+1'b1;
   end
   READY:if(reset_n&&((write_button&&!wb_prev)||(read_button&&!rb_prev)||ds3[30]!=start_prev||ds3[29]!=cold_prev||ds3[28]!=single_prev))begin
    mode<=ds3[28]!=single_prev?2:((read_button&&!rb_prev)||ds3[29]!=cold_prev)?1:0;
    hold_enabled<=ds3[28]!=single_prev&&ds3[27];pause_point<=ds3[9:8];
    scan_b<=0;verifying<=0;is_read<=1;state<=ISSUE;status<=1;
   end
   ISSUE:begin
    received<=0;elapsed_cycles<=0;target_read<=is_read;target_write<=!is_read;state<=CLEAR;
   end
   CLEAR,WAIT:begin
    elapsed_cycles<=elapsed_cycles+1'b1;
    if(elapsed_cycles>=TIMEOUT_CYCLES-1)begin state<=FAULT;status<=7;reason<=8'h40;session_flags<=32'h00008000;end
    else if(state==CLEAR)begin if(!target_done)state<=WAIT;end
    else if(target_done)begin
     commands<=commands+1'b1;last_error<=target_err;
     if(target_err!=0)begin state<=FAULT;status<=5;reason<=is_read?8'h21:8'h22;session_flags<=32'h00000100|{29'd0,target_err};end
     else if(is_read)begin
      index<=0;crc<=32'hffffffff;malformed<=0;missing<=0;compare_bad<=0;scan_gen<=0;
      stored_crc<=0;state<=FETCH;
      if(verifying)total_cycles<=total_cycles+elapsed_cycles;
     end else begin total_cycles<=total_cycles+elapsed_cycles;state<=CHUNK_NEXT;end
    end
   end
   FETCH:state<=SCAN;
   SCAN:begin
    if(!received[index])missing<=1;
    if(verifying&&rx_q!=tx_q)compare_bad<=1;
    if(!verifying&&!scan_b)a_mem[index]<=rx_q;
    if(!verifying&&scan_b&&rx_q!=a_q)same_records<=0;
    if(index!=7)crc<=crc_word(crc,rx_q);else stored_crc<=rx_q;
    case(index)
     0:if(rx_q!=32'h53445235)malformed<=1;
     1:if(rx_q!=32'h00010020)malformed<=1;
     2:if(rx_q!=512)malformed<=1;
     3:scan_gen[63:32]<=rx_q;
     4:scan_gen[31:0]<=rx_q;
     5:if(rx_q!=480)malformed<=1;
     6:if(rx_q!=0)malformed<=1;
    endcase
    if(index==127)state<=VALIDATE;else begin index<=index+1'b1;state<=FETCH;end
   end
   VALIDATE:begin
    observed_crc<=~crc;
    if(missing)begin state<=FAULT;status<=5;reason<=8'h23;session_flags<=32'h200;end
    else if(verifying)begin
     if(malformed||scan_gen!=new_gen||stored_crc!=~crc||compare_bad||stored_crc!=expected_crc)begin
      state<=FAULT;status<=5;reason<=8'h24;session_flags<=32'h400;
     end else state<=COMMIT;
    end else begin
     if(scan_b)begin valid_b<=!malformed&&scan_gen!=0&&stored_crc==~crc;gen_b<=scan_gen;crc_b<=stored_crc;state<=SELECT;end
     else begin valid_a<=!malformed&&scan_gen!=0&&stored_crc==~crc;gen_a<=scan_gen;crc_a<=stored_crc;scan_b<=1;state<=ISSUE;end
    end
   end
   SELECT:begin
    if(valid_a&&valid_b&&gen_a==gen_b&&!same_records)begin state<=FAULT;status<=5;reason<=8'h11;session_flags<=32'h800;end
    else begin
     selected_gen<=valid_a&&(!valid_b||gen_a>=gen_b)?gen_a:valid_b?gen_b:64'd0;
     destination<=valid_a&&(!valid_b||gen_a>=gen_b)?1:0;
     if(mode==1)begin expected_crc<=valid_a&&(!valid_b||gen_a>=gen_b)?crc_a:valid_b?crc_b:32'd0;observed_crc<=valid_a&&(!valid_b||gen_a>=gen_b)?crc_a:valid_b?crc_b:32'd0;state<=FINISHED;status<=valid_a||valid_b?4:6;reason<=valid_a||valid_b?0:8'h10;session_flags<=valid_a||valid_b?32'h80000006:32'h80000000;end
     else state<=PREPARE;
    end
   end
   PREPARE:begin
    if(selected_gen==64'hffffffffffffffff)begin state<=FAULT;status<=5;reason<=8'h12;session_flags<=32'h1000;end
    else begin new_gen<=selected_gen+1'b1;index<=0;state<=CRC_FETCH;status<=2;crc<=32'hffffffff;chunk<=0;total_cycles<=0;paused_once<=0;end
   end
   CRC_FETCH:begin tx_mem[index]<=record_word(index,new_gen);state<=CRC_SCAN;end
   CRC_SCAN:begin
    if(index!=7)crc<=crc_word(crc,record_word(index,new_gen));
    if(index==127)state<=CRC_STORE;else begin index<=index+1'b1;state<=CRC_FETCH;end
   end
   CRC_STORE:begin tx_mem[7]<=~crc;expected_crc<=~crc;is_read<=0;state<=ARM;end
   ARM:begin
    if(hold_enabled&&!paused_once&&pause_point==0)begin state<=PAUSED;status<=8;paused_once<=1;end
    else state<=ISSUE;
   end
   PAUSED:if(ds3[26]!=resume_prev&&reset_n)begin state<=ISSUE;status<=2;end
   CHUNK_NEXT:begin
    if(chunk==3)begin is_read<=1;verifying<=1;state<=ISSUE;status<=3;end
    else begin
     chunk<=chunk+1'b1;
     if(hold_enabled&&!paused_once&&pause_point==chunk+1'b1)begin state<=PAUSED;status<=8;paused_once<=1;end
     else state<=ISSUE;
    end
   end
   COMMIT:begin
    if(destination)begin valid_b<=1;gen_b<=new_gen;end else begin valid_a<=1;gen_a<=new_gen;end
    selected_gen<=new_gen;
    log_flags[operation]<=32'h80000007|(destination?32'h8:32'd0);
    log_gen_lo[operation]<=new_gen[31:0];log_gen_hi[operation]<=new_gen[63:32];log_crc[operation]<=expected_crc;log_cycles[operation]<=total_cycles;
    completed<=completed+1'b1;session_flags<=32'h80000007|(destination?32'h8:32'd0);state<=NEXT;
   end
   NEXT:begin
    if(mode==2||operation==COMMITS-1)begin state<=FINISHED;status<=4;reason<=0;end
    else begin operation<=operation+1'b1;destination<=!destination;verifying<=0;state<=PREPARE;end
   end
   FINISHED:begin end
   FAULT:begin end // Timeout or error never releases request ownership or retries.
   default:begin state<=FAULT;status<=7;reason<=8'hff;end
  endcase
 end
endmodule
`default_nettype wire
