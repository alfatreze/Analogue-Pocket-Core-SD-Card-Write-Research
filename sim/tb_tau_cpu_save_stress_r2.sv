// Exact pinned Tau CPU + crossing; simple isolated buses and modeled APF.
`timescale 1ns/1ps
module tb_tau_cpu_save_stress;
 parameter CPU_HALF_NS=8.333;
 parameter APF_DELAY=100;
 parameter BUS_DELAY=0;
 reg clk=0,apfclk=0,rst=1;
 always #(CPU_HALF_NS) clk=~clk;
 always #6.734 apfclk=~apfclk;
 wire ic,ist,iw,dc,ds,dw;wire [29:0] ia,da;wire[31:0] idout,ddout;wire[3:0] isel,dsel;wire[2:0] ict,dct;wire[1:0] ibt,dbt;
 reg iack=0,dack=0;reg[31:0] idin=0,ddin=0;
 reg[31:0] mem[0:4095];integer i;
 VexRiscv cpu(.externalResetVector(32'd0),.timerInterrupt(1'b0),.softwareInterrupt(1'b0),.externalInterruptArray(32'd0),
 .iBusWishbone_CYC(ic),.iBusWishbone_STB(ist),.iBusWishbone_ACK(iack),.iBusWishbone_WE(iw),.iBusWishbone_ADR(ia),.iBusWishbone_DAT_MISO(idin),.iBusWishbone_DAT_MOSI(idout),.iBusWishbone_SEL(isel),.iBusWishbone_ERR(1'b0),.iBusWishbone_CTI(ict),.iBusWishbone_BTE(ibt),
 .dBusWishbone_CYC(dc),.dBusWishbone_STB(ds),.dBusWishbone_ACK(dack),.dBusWishbone_WE(dw),.dBusWishbone_ADR(da),.dBusWishbone_DAT_MISO(ddin),.dBusWishbone_DAT_MOSI(ddout),.dBusWishbone_SEL(dsel),.dBusWishbone_ERR(1'b0),.dBusWishbone_CTI(dct),.dBusWishbone_BTE(dbt),.clk(clk),.reset(rst));
 reg go=0;reg[2:0] selection=0;
 reg[31:0] slot=0,offset=0,bridge=0,length=0;
 reg[31:0] tx[0:127],rx[0:2047],card[0:4095];
 integer reads=0,writes=0,n,destination;
 parameter EXPECT_EXIT=0;
 parameter EXPECT_COMMANDS=22;
 parameter EXPECT_REQUESTS=EXPECT_COMMANDS;
 parameter ERROR_ON=0;
 parameter TIMEOUT_ON=0;
 parameter OMIT_GUARD_ON=0;
 parameter BAD_GUARD_ON=0;
 integer omitted=0;
 reg[2047:0] received=0;wire busy,done;wire[7:0] seq;wire[2:0] err;
 wire tr,to,tg,tw,tf;reg td=0;reg[2:0] te=0;
 tgt_cmd crossing(.clk_sys(clk),.rst_sys(rst),.clk_74a(apfclk),.go(go),.cmd_sel(selection),.busy(busy),.done(done),.seq(seq),.err(err),.t_read(tr),.t_openfile(to),.t_getfile(tg),.t_write(tw),.t_flush(tf),.t_ack(1'b0),.t_done(td),.t_err(te));
 integer requests=0,transfers=0,extra_go=0,bstate=0,delay=0;
 reg queued=0;
 always @(posedge apfclk) begin
  if(tr||to||tg||tw||tf) begin
   if(bstate!=0||queued)$fatal(1,"Overlapping APF request");
   if(to||tg||tf||slot<37||slot>38)$fatal(1,"Command/slot out of bounds");
   if(tr && (bridge!=32'h21000000||offset!=0||length!=8192))$fatal(1,"Read range invalid");
   if(tw && (length!=128||offset<512||offset>896||offset[6:0]!=0||bridge!=32'h20000000+offset-512))$fatal(1,"Write range invalid");
   queued<=1;requests<=requests+1;
  end
  case(bstate)
   0:if(queued)begin queued<=0;bstate<=1;end
   1:begin td<=0;delay<=0;bstate<=2;end
   2:begin delay<=delay+1;if(delay==APF_DELAY && requests!=TIMEOUT_ON)begin
    destination=slot-37;
    if(selection==0)begin
     for(n=0;n<2048;n=n+1)begin
      if(requests==OMIT_GUARD_ON && n==0)omitted<=omitted+1;
      else begin rx[n]<=requests==BAD_GUARD_ON && n==0?32'hdeadbeef:card[destination*2048+n];received[n]<=1;end
     end
     reads<=reads+1;
    end else if(selection==3)begin
     for(n=0;n<32;n=n+1)card[destination*2048+offset/4+n]<=tx[(bridge-32'h20000000)/4+n];writes<=writes+1;
    end else $fatal(1,"Unexpected command");
    transfers<=transfers+1;te<=requests==ERROR_ON?3'd1:3'd0;td<=1;bstate<=0;
   end end
  endcase
 end
 integer lane,iwait=0,dwait=0;
 always @(posedge clk) begin
  iack<=0;dack<=0;go<=0;
  if(!rst)begin
   if(ic&&ist&&!iack)begin
    if(iwait<BUS_DELAY)iwait<=iwait+1;else begin
    iwait<=0;
    if(ia>=4096||iw)$fatal(1,"Instruction bus out of range");
    idin<=mem[ia];iack<=1;
    end
   end
   if(dc&&ds&&!dack)begin
    if(dwait<BUS_DELAY)dwait<=dwait+1;else begin
    dwait<=0;
    dack<=1;
    if(da<4096)begin
     ddin<=mem[da];
     if(dw)for(lane=0;lane<4;lane=lane+1)if(dsel[lane])mem[da][lane*8+:8]<=ddout[lane*8+:8];
    end else if(da>=30'h20004000&&da<30'h20004080)begin
     ddin<=tx[da-30'h20004000];
     if(dw)begin
      if(dsel!=15||busy)$fatal(1,"Staging TX requires full words while unowned");
      tx[da-30'h20004000]<=ddout;
     end
    end else if(da>=30'h20006000&&da<30'h20006800)begin
     if(dw)$fatal(1,"CPU wrote receive buffer");
     ddin<=rx[da-30'h20006000];
    end else if(da>=30'h20000008&&da<=30'h2000000b)begin
     if(busy)$fatal(1,"Parameters changed while APF owns them");
     if(dw)case(da[3:0])8:slot<=ddout;9:offset<=ddout;10:bridge<=ddout;11:length<=ddout;endcase
    end else if(da==30'h2000000d)begin
     ddin<=$countones(received);
     if(dw)begin if(busy)$fatal(1,"Receive lease cleared while busy");received<=0;end
    end else if(da==30'h2000000c)begin
     ddin<={16'd0,seq,3'd0,err,done,busy};
     if(dw)begin go<=1;selection<=ddout[2:0];if(busy)extra_go<=extra_go+1;end
    end else if(da==30'h20000001&&dw)begin
     if(ddout!=EXPECT_EXIT)$fatal(1,"CPU save exit %h expected %h",ddout,EXPECT_EXIT);
     if(transfers!=EXPECT_COMMANDS||requests!=EXPECT_REQUESTS||extra_go!=0)$fatal(1,"Wrong command counts");
     for(n=0;n<4096;n=n+1)begin mem[n]=card[n];end
     $writememh("final-card.hex",mem);
     $display("PASS actual Tau CPU save prototype: commands=%0d reads=%0d writes=%0d exit=%h omitted=%0d",transfers,reads,writes,ddout,omitted);$finish;
    end else $fatal(1,"Unknown data bus address %h",{da,2'b0});
    end
   end
  end
 end
 initial begin
  for(i=0;i<4096;i=i+1)mem[i]=0;
  $readmemh("firmware.hex",mem);
  $readmemh("initial-card.hex",card);
  for(i=0;i<2048;i=i+1)rx[i]=32'ha5a5a5a5;
  repeat(30)@(posedge clk);rst<=0;
 end
 initial begin #300000000;$fatal(1,"CPU timeout transfers %0d pc %h",transfers,{ia,2'b0});end
endmodule
