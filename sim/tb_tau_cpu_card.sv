// Exact pinned Tau CPU + crossing; simple isolated buses and modeled APF.
`timescale 1ns/1ps
module tb_tau_cpu_card;
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
 reg go=0;reg[2:0] selection=0;wire busy,done;wire[7:0] seq;wire[2:0] err;
 wire tr,to,tg,tw,tf;reg td=0;reg[2:0] te=0;
 tgt_cmd crossing(.clk_sys(clk),.rst_sys(rst),.clk_74a(apfclk),.go(go),.cmd_sel(selection),.busy(busy),.done(done),.seq(seq),.err(err),.t_read(tr),.t_openfile(to),.t_getfile(tg),.t_write(tw),.t_flush(tf),.t_ack(1'b0),.t_done(td),.t_err(te));
 integer requests=0,transfers=0,extra_go=0,bstate=0,delay=0;
 reg queued=0;
 always @(posedge apfclk) begin
  if(tr||to||tg||tw||tf) begin
   if ({tf,tw,tg,to,tr} !== (5'b1<<(requests%5))) $fatal(1,"Incorrect command selection");
   queued<=1;requests<=requests+1;
  end
  case(bstate)
   0:if(queued)begin queued<=0;bstate<=1;end
   1:begin td<=0;delay<=0;bstate<=2;end
   2:begin delay<=delay+1;if(delay==APF_DELAY)begin transfers<=transfers+1;te<=transfers%8;td<=1;bstate<=0;end end
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
    end else if(da==30'h2000000c)begin
     ddin<={16'd0,seq,3'd0,err,done,busy};
     if(dw)begin go<=1;selection<=ddout[2:0];if(busy)extra_go<=extra_go+1;end
    end else if(da==30'h20000001&&dw)begin
     if(ddout!=0)$fatal(1,"CPU firmware failure code %0d transfers %0d",ddout,transfers);
     if(transfers!=300||requests!=300||extra_go!=300||seq!=44)$fatal(1,"Counts/sequence wrong %0d %0d %0d %0d",transfers,requests,extra_go,seq);
     $display("PASS actual Tau CPU: 300 commands, 300 busy GO ignored, sequence wrap and all errors/selections");$finish;
    end else $fatal(1,"Unknown data bus address %h",{da,2'b0});
    end
   end
  end
 end
 initial begin
  for(i=0;i<4096;i=i+1)mem[i]=0;
  $readmemh("firmware.hex",mem);
  repeat(30)@(posedge clk);rst<=0;
 end
 initial begin #20000000;$fatal(1,"CPU timeout transfers %0d pc %h",transfers,{ia,2'b0});end
endmodule
