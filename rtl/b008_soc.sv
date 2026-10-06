`default_nettype none
// B008 small synthesizable CPU bus. Configuration loads firmware into M10K;
// CPU reset never clears memory, mailbox toggles or the B007 engine.
module b008_soc #(parameter FIRMWARE_FILE="core/b008_firmware.hex", parameter SIMULATION=0)(
 input wire cpu_clk, engine_clk, cpu_reset, input wire [31:0] buttons,
 input wire [3:0] engine_status,input wire [2:0] engine_error,
 input wire [31:0] engine_completed,engine_tag,
 output wire write_pulse,read_pulse,
 input wire [31:0] debug_source,output reg [255:0] debug_snapshot=0,
 output reg cpu_fault=0, output reg [31:0] firmware_ready=0,
 output reg sim_finished=0, output reg [31:0] sim_code=0,output reg sim_marker=0
);
 wire reset=cpu_reset||cpu_fault;
 wire ic,ist,iw,dc,ds,dw;wire[29:0]ia,da;wire[31:0]ido,ddo;wire[3:0]isel,dsel;wire[2:0]ict,dct;wire[1:0]ibt,dbt;
 reg iack=0,dack=0;reg[31:0]idi=0,ddi=0;
 wire mm=da>=30'h20004000 && da<=30'h20004009;
 wire mack;wire[31:0]mdi;
 VexRiscv cpu(.externalResetVector(32'd0),.timerInterrupt(1'b0),.softwareInterrupt(1'b0),.externalInterruptArray(32'd0),
 .iBusWishbone_CYC(ic),.iBusWishbone_STB(ist),.iBusWishbone_ACK(iack),.iBusWishbone_WE(iw),.iBusWishbone_ADR(ia),.iBusWishbone_DAT_MISO(idi),.iBusWishbone_DAT_MOSI(ido),.iBusWishbone_SEL(isel),.iBusWishbone_ERR(1'b0),.iBusWishbone_CTI(ict),.iBusWishbone_BTE(ibt),
 .dBusWishbone_CYC(dc),.dBusWishbone_STB(ds),.dBusWishbone_ACK(mm?mack:dack),.dBusWishbone_WE(dw),.dBusWishbone_ADR(da),.dBusWishbone_DAT_MISO(mm?mdi:ddi),.dBusWishbone_DAT_MOSI(ddo),.dBusWishbone_SEL(dsel),.dBusWishbone_ERR(1'b0),.dBusWishbone_CTI(dct),.dBusWishbone_BTE(dbt),.clk(cpu_clk),.reset(reset));
 b008_mailbox mailbox(.cpu_clk(cpu_clk),.engine_clk(engine_clk),.cpu_reset(reset),.cyc(dc&&mm),.stb(ds),.we(dw),.addr({da[3:0],2'b0}),.wdata(ddo),.sel(dsel),.ack(mack),.rdata(mdi),.engine_status(engine_status),.engine_error(engine_error),.engine_completed(engine_completed),.engine_tag(engine_tag),.write_pulse(write_pulse),.read_pulse(read_pulse));
 (* ramstyle="M10K" *) reg [31:0] memory[0:4095];
 initial $readmemh(FIRMWARE_FILE,memory);
 (* async_reg="true" *) reg[31:0]keys1=0,keys2=0;
 (* async_reg="true" *) reg snap1=0,snap2=0;
 reg snap_seen=0;reg[31:0]heartbeat=0,last_response=0,last_flags=0,last_pc=0,fault_code=0;
 integer lane;
 always @(posedge cpu_clk)begin
  keys1<=buttons;keys2<=keys1;snap1<=debug_source[31];snap2<=snap1;
  if(snap2!=snap_seen)begin
   snap_seen<=snap2;
   debug_snapshot<={32'h43505508,heartbeat,last_response,last_flags,last_pc,firmware_ready,fault_code,{30'd0,cpu_fault,reset}};
  end
  iack<=0;dack<=0;
  if(!reset)begin
   if(ic&&ist&&!iack)begin
    iack<=1;last_pc<={ia,2'b0};
    if(ia<4096&&!iw)idi<=memory[ia[11:0]];
    else begin idi<=0;cpu_fault<=1;fault_code<=4;end
   end
   if(dc&&ds&&!mm&&!dack)begin
    dack<=1;ddi<=0;
    // High byte-address bit 31 is the CPU's uncached alias; all other
    // upper RAM address bits must be zero. MMIO is exclusively uncached.
    if(da[28:0]<4096)begin
     ddi<=memory[da[11:0]];
     if(dw)for(lane=0;lane<4;lane=lane+1)if(dsel[lane])memory[da[11:0]][lane*8+:8]<=ddo[lane*8+:8];
    end else if(da==30'h2000400c)ddi<=keys2;
    else if(da>=30'h20004010&&da<=30'h20004017)begin
     case(da[4:0])
      5'h10:begin ddi<=heartbeat;if(dw&&dsel==15)heartbeat<=ddo;end
      5'h11:begin ddi<=last_response;if(dw&&dsel==15)last_response<=ddo;end
      5'h12:begin ddi<=last_flags;if(dw&&dsel==15)last_flags<=ddo;end
      5'h13:ddi<=last_pc;
      5'h14:begin ddi<=firmware_ready;if(dw&&dsel==15)firmware_ready<=ddo;end
      5'h17:begin ddi<=fault_code;if(dw&&dsel==15)begin fault_code<=ddo;cpu_fault<=1;end end
      default:begin cpu_fault<=1;fault_code<=5;end
     endcase
    end else if(SIMULATION && da==30'h20008000&&dw)begin sim_finished<=1;sim_code<=ddo;end
    else if(SIMULATION && da==30'h20008001&&dw)sim_marker<=1;
    else begin cpu_fault<=1;fault_code<=6;end
   end
  end
 end
endmodule
`default_nettype wire
