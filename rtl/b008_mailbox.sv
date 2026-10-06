`default_nettype none
// Isolated B008 supervisor. FPGA configuration initializes the mailbox;
// cpu_reset deliberately does NOT cancel a pending request or reset the engine.
// Bundled data is held through a toggle handshake with two synchronizer stages
// and an additional settling cycle. ACK means command delivery, not APF DONE.
module b008_mailbox(
 input wire cpu_clk, engine_clk, cpu_reset,
 input wire cyc, stb, we, input wire [5:0] addr,
 input wire [31:0] wdata, input wire [3:0] sel,
 output reg ack=0, output reg [31:0] rdata=0,
 input wire [3:0] engine_status, input wire [2:0] engine_error,
 input wire [31:0] engine_completed, engine_tag,
 output reg write_pulse=0, read_pulse=0
);
 reg seen=0, pending=0, locked=1;
 reg [5:0] beat_addr=0; reg beat_we=0; reg [31:0] beat_data=0; reg [3:0] beat_sel=0;
 reg [31:0] sequence_count=0, rejected=0, local_error=0;
 reg [2:0] command=0;
 reg request_toggle=0, response_toggle=0;
 (* async_reg="true" *) reg ack1=0, ack2=0, req1=0, req2=0, rst1=1, rst2=1;
 reg settle_cpu=0, settle_engine=0, request_seen=0;
 reg [31:0] response_code=0, snapshot_flags=0, snapshot_completed=0, snapshot_tag=0, snapshot_actions=0;
 reg [31:0] held_code=0, held_flags=0, held_completed=0, held_tag=0, action_count=0;
 reg reset_stopped=0;
 wire idle=(engine_status==0 || engine_status==4 || engine_status==5);
 wire valid_image=(engine_status==4 || engine_status==5);
 wire fault=(engine_status==6 || engine_status==7);
 wire writing=(engine_status==8 || engine_status==2);
 always @(posedge cpu_clk) begin
  ack1<=response_toggle; ack2<=ack1; ack<=0;
  if(pending && ack2==request_toggle) begin
   if(!settle_cpu) settle_cpu<=1;
   else begin
    settle_cpu<=0; pending<=0; sequence_count<=sequence_count+1;
    response_code<=held_code; snapshot_flags<=held_flags;
    snapshot_completed<=held_completed; snapshot_tag<=held_tag; snapshot_actions<=action_count;
    if(command==5 && held_code==0) locked<=0;
   end
  end
  if(cpu_reset) begin locked<=1; seen<=0; ack<=0; end
  else begin
   if(!cyc || !stb) seen<=0;
   if(cyc && stb && !ack && (!seen || addr!=beat_addr || we!=beat_we ||
       (we && (wdata!=beat_data || sel!=beat_sel)))) begin
    seen<=1; ack<=1; beat_addr<=addr; beat_we<=we; beat_data<=wdata; beat_sel<=sel;
    case(addr)
     6'h04:rdata<={29'd0,(local_error!=0),locked,pending};
     6'h08:rdata<=sequence_count;
     6'h0c:rdata<=response_code;
     6'h10:rdata<=snapshot_flags;
     6'h14:rdata<=snapshot_completed;
     6'h18:rdata<=snapshot_tag;
     6'h1c:rdata<=rejected;
     6'h20:rdata<=snapshot_actions;
     6'h24:rdata<=local_error;
     default:rdata<=0;
    endcase
    if(we && addr==0) begin
     if(pending || (locked && wdata!=4 && wdata!=5) || sel!=4'hf || wdata>7) begin
      rejected<=rejected+1; local_error<=pending?1:(locked?2:3);
     end else begin
      command<=wdata[2:0]; request_toggle<=!request_toggle; pending<=1;
      settle_cpu<=0; local_error<=0;
     end
    end
   end
  end
 end
 always @(posedge engine_clk) begin
  req1<=request_toggle; req2<=req1; rst1<=cpu_reset; rst2<=rst1;
  write_pulse<=0; read_pulse<=0;
  if(!rst2) reset_stopped<=0;
  // Reset asks B007 to stop after real completion. It never releases ownership.
  if(rst2 && writing && !reset_stopped) begin read_pulse<=1; reset_stopped<=1; end
  if(req2!=request_seen) begin
   if(!settle_engine) settle_engine<=1;
   else begin
    settle_engine<=0; request_seen<=req2;
    held_flags<={20'd0,rst2,fault,valid_image,idle,1'b0,engine_error,engine_status};
    held_completed<=engine_completed; held_tag<=engine_tag;
    action_count<=action_count+1; held_code<=0;
    case(command)
     1:if(rst2)held_code<=4;else if(fault)held_code<=5;else if(!idle)held_code<=2;else read_pulse<=1;
     2:if(rst2)held_code<=4;else if(fault)held_code<=5;else if(!idle)held_code<=2;else if(!valid_image)held_code<=3;else write_pulse<=1;
     3:if(writing)read_pulse<=1;else held_code<=fault?5:2;
     4:begin end // coherent observation, always safe
     5:if(rst2 || !idle || fault)held_code<=fault?5:4;
     default:held_code<=1;
    endcase
    response_toggle<=req2;
   end
  end
 end
endmodule
`default_nettype wire
