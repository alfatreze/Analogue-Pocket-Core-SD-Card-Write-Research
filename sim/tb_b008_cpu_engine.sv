`timescale 1ns/1ps
module tb_b008_cpu_engine;
 parameter FILE_BYTES=1024;
 reg clk=0,eclk=0,rst=1; integer half_ps=8333,phase_ps=0,profile=0;
 initial begin void'($value$plusargs("half_ps=%d",half_ps));forever #(half_ps/1000.0)clk=~clk;end
 initial begin void'($value$plusargs("phase_ps=%d",phase_ps));#(phase_ps/1000.0);forever #6.734 eclk=~eclk;end
 initial void'($value$plusargs("profile=%d",profile));
 wire ic,ist,iw,dc,ds,dw;wire [29:0] ia,da;wire[31:0] idout,ddout;wire[3:0] isel,dsel;wire[2:0] ict,dct;wire[1:0] ibt,dbt;
 reg iack=0,ramack=0;reg[31:0] idin=0,ramdin=0;
 wire mm=(da==30'h20004000 || (da>=30'h20004001 && da<=30'h20004009));
 wire mack;wire[31:0] mdin;
 VexRiscv cpu(.externalResetVector(32'd0),.timerInterrupt(1'b0),.softwareInterrupt(1'b0),.externalInterruptArray(32'd0),
 .iBusWishbone_CYC(ic),.iBusWishbone_STB(ist),.iBusWishbone_ACK(iack),.iBusWishbone_WE(iw),.iBusWishbone_ADR(ia),.iBusWishbone_DAT_MISO(idin),.iBusWishbone_DAT_MOSI(idout),.iBusWishbone_SEL(isel),.iBusWishbone_ERR(1'b0),.iBusWishbone_CTI(ict),.iBusWishbone_BTE(ibt),
 .dBusWishbone_CYC(dc),.dBusWishbone_STB(ds),.dBusWishbone_ACK(mm?mack:ramack),.dBusWishbone_WE(dw),.dBusWishbone_ADR(da),.dBusWishbone_DAT_MISO(mm?mdin:ramdin),.dBusWishbone_DAT_MOSI(ddout),.dBusWishbone_SEL(dsel),.dBusWishbone_ERR(1'b0),.dBusWishbone_CTI(dct),.dBusWishbone_BTE(dbt),.clk(clk),.reset(rst));
 reg[31:0] mem[0:4095];integer i,lane;reg marker=0,finished=0;
 wire wp,rp;wire[3:0] status;wire[2:0] error;wire[31:0] completed,tag;
 b008_mailbox mb(.cpu_clk(clk),.engine_clk(eclk),.cpu_reset(rst),.cyc(dc&&mm),.stb(ds),.we(dw),.addr({da[3:0],2'b0}),.wdata(ddout),.sel(dsel),.ack(mack),.rdata(mdin),.engine_status(status),.engine_error(error),.engine_completed(completed),.engine_tag(tag),.write_pulse(wp),.read_pulse(rp));
 reg[31:0] ba=0,bwd=0;reg br=0,bw=0;wire[31:0] brd;
 wire tr,tw;reg ta=0,td=1;reg[2:0] te=0;
 wire[15:0] slot;wire[31:0] offset,source,length;
 lab_powercut #(.FILE_BYTES(FILE_BYTES),.TIMEOUT_CYCLES(200000)) engine(.clk(eclk),.reset_n(1'b1),.write_button(wp),.read_button(rp),.bridge_addr(ba),.bridge_rd(br),.bridge_wr(bw),.bridge_wr_data(bwd),.bridge_rd_data(brd),.target_read(tr),.target_write(tw),.target_ack(ta),.slot_id(slot),.slot_offset(offset),.source_addr(source),.transfer_length(length),.target_done(td),.target_err(te),.status(status),.generation(),.loaded_generation(tag),.completed(completed),.last_error(error),.elapsed_cycles(),.debug_source(32'd0),.debug_probe());
 localparam WORDS=FILE_BYTES/4;
 reg[31:0] card[0:WORDS-1];
 function automatic[31:0] pattern(input bit t,input integer n);
  case(n)0:pattern=32'h41504357;1:pattern=32'h30303700;2:pattern=t;3:pattern=FILE_BYTES;default:pattern=(32'(n)*32'h9e3779b1)^(t?32'h85ebca6b:0)^32'hb007c0de;endcase
 endfunction
 integer state=0,index=0,delay=0,reads=0,writes=0,real_done=0;reg iswrite=0;reg[31:0] heldsource;reg reset_used=0;
 always @(negedge eclk)begin
  br=0;bw=0;
  if(state!=0 && source!==heldsource)$fatal(1,"Owner changed before DONE");
  case(state)
   0:if(tr||tw)begin
    if(slot!=39 || offset!=0 || length!=FILE_BYTES || source!=(tw?32'h10000000:32'h10040000))$fatal(1,"Transfer bounds");
    if(tr&&tw)$fatal(1,"Two target owners");
    iswrite=tw;heldsource=source;reads+=tr;writes+=tw;delay=0;state=1;te=0;
   end
   1:begin // preserve stale high DONE before acknowledgement
    delay++;if(delay==12)begin td=0;ta=1;delay=0;state=2;end
   end
   2:begin
    delay++;
    if((profile==3 || profile==10)&&iswrite)begin
     if(status==7 && delay>200100)begin td=1;ta=0;state=5;end
    end else if(delay==(profile==8?1000:20))begin
     if((profile==1&&!iswrite)||(profile==2&&iswrite))begin te=3;td=1;ta=0;state=0;real_done++;end
     else begin index=0;state=iswrite?4:3;if(iswrite)begin ba=32'h10000000;br=1;end end
    end
   end
   3:begin
    ba=32'h10040000+4*((profile==9&&index==WORDS-1)?WORDS-2:index);bw=1;bwd=card[(profile==9&&index==WORDS-1)?WORDS-2:index];index++;
    if(index==WORDS)state=6;
   end
   4:begin
    card[index]=brd;index++;
    if(index==WORDS)begin td=1;ta=0;state=0;real_done++;end
    else begin ba=32'h10000000+index*4;br=1;end
   end
   5:begin // late completion cannot rearm a timed-out engine
    if(tr||tw)$fatal(1,"Retry after timeout");
   end
   6:begin td=1;ta=0;state=0;real_done++;end
  endcase
  if(state!=0 && (tr||tw) && state!=1)$fatal(1,"New request while owned");
 end
 // One CPU-only reset per selected profile. Engine remains running.
 initial begin
  for(i=0;i<4096;i++)mem[i]=0;$readmemh("firmware.hex",mem);
  for(i=0;i<WORDS;i++)card[i]=pattern(0,i);
  if(profile==4)card[10]=pattern(1,10);
  repeat(30)@(negedge clk);rst=0;
  if(profile==5)wait(marker);
  else if(profile==6||profile==10)wait(state==2&&iswrite&&delay>=2);
  else if(profile==7)wait(state==2&&!iswrite&&delay>=2);
  else wait(finished);
  if(profile==5||profile==6||profile==7||profile==10)begin
   @(negedge clk);rst=1;reset_used=1;repeat(30)@(negedge clk);rst=0;
  end
 end
 always @(posedge clk)begin
  iack<=0;ramack<=0;
  if(!rst)begin
   if(ic&&ist&&!iack)begin if(ia>=4096||iw)$fatal(1,"Instruction range");idin<=mem[ia];iack<=1;end
   if(dc&&ds&&!mm&&!ramack)begin
    ramack<=1;
    if(da[28:0]<4096)begin ramdin<=mem[da[11:0]];if(dw)for(lane=0;lane<4;lane++)if(dsel[lane])mem[da[11:0]][lane*8+:8]<=ddout[lane*8+:8];end
    else if(da==30'h20008001&&dw)marker<=1;
    else if(da==30'h20008000&&dw)begin
     if(ddout!=0)$fatal(1,"Firmware code %0d status %0d reads %0d writes %0d",ddout,status,reads,writes);
     finished<=1;
    end else $fatal(1,"Data range %h",{da,2'b0});
   end
  end
 end
 initial begin
  wait(finished);repeat(1000)@(negedge eclk);
  if(profile==3||profile==10)begin
   wait(state==5);repeat(100)@(negedge eclk);
   if(status!=7 || writes!=1 || completed!=0 || !engine.active)$fatal(1,"Timeout ownership");
  end
  if(profile==0||profile==5||profile==6||profile==7||profile==8)begin
   if(status!=5 || writes!=((profile==5||profile==7)?0:1))$fatal(1,"Final counts");
  end else if(profile!=3&&profile!=10)begin
   if(status!=6 || completed!=0)$fatal(1,"Expected fault");
  end
  $writememh("final-card.hex",card);
  $display("PASS B008 CPU engine profile=%0d reads=%0d writes=%0d completed=%0d reset=%0d actions=%0d",profile,reads,writes,completed,reset_used,mb.action_count);$finish;
 end
 initial begin #30000000;$display("BUS dc=%0b ds=%0b da=%h ack=%0b seen=%0b cookie=%h rejected=%0d",dc,ds,da,mm?mack:ramack,mb.seen,mem[4092],mb.rejected);$fatal(1,"Simulation budget pc=%h status=%0d pending=%0d locked=%0d",{ia,2'b0},status,mb.pending,mb.locked);end
endmodule
