// Diagnostic only: CPU-side reset is not APF command cancellation.
`timescale 1ns/1ps
module tb_tau_card_reset;
 reg sys=0,apf=0,rst=1,go=0;
 always #8.333 sys=~sys;
 always #6.734 apf=~apf;
 wire busy,done;wire[7:0] seq;wire[2:0] err;wire tr,to,tg,tw,tf;
 reg td=0;reg accepted=0;integer countdown=0;
 tgt_cmd dut(.clk_sys(sys),.rst_sys(rst),.clk_74a(apf),.go(go),.cmd_sel(3'd3),.busy(busy),.done(done),.seq(seq),.err(err),.t_read(tr),.t_openfile(to),.t_getfile(tg),.t_write(tw),.t_flush(tf),.t_ack(1'b0),.t_done(td),.t_err(3'd0));
 always @(posedge apf)begin
  if(tw)begin accepted<=1;countdown<=200;td<=0;end
  else if(countdown>0)begin countdown<=countdown-1;if(countdown==1)td<=1;end
 end
 initial begin
  repeat(10)@(negedge sys);rst=0;
  repeat(10)@(negedge sys);go=1;
  @(negedge sys);go=0;
  wait(accepted);
  @(negedge sys);rst=1;
  repeat(2)@(negedge sys);
  if(busy!==0||td!==0||countdown==0)$fatal(1,"Expected reset diagnostic state absent");
  $display("OBSERVED CPU busy cleared while accepted APF write remains outstanding");
  rst=0;wait(done);@(negedge sys);
  if(seq!==1)$fatal(1,"Delayed completion observation absent");
  $display("OBSERVED delayed pre-reset APF completion increments post-reset sequence");
  $display("DIAGNOSTIC COMPLETE: independent CPU-side reset cannot cancel command ownership");$finish;
 end
 initial begin #200000;$fatal(1,"Reset diagnostic timeout");end
endmodule
