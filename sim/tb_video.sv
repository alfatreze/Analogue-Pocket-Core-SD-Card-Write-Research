`timescale 1ns/1ps
module tb_video;
reg clk=0;
always #5 clk=~clk;
wire [23:0] rgb;
wire de,hs,vs;
reg [3:0] status=0;
reg [31:0] completed=0,loaded=0;
lab_video display(.clk(clk),.reset_n(1'b1),.status(status),.generation(32'd1),
 .loaded_generation(loaded),.completed(completed),.error(3'd0),.elapsed(32'd1000),
 .rgb(rgb),.de(de),.hs(hs),.vs(vs));
integer frame,pixels,fd;
reg [255:0] name;
initial begin
 for(frame=0;frame<8;frame=frame+1)begin
  status=frame;completed=frame>2?1:0;loaded=frame==4?1:0;
  // Start at a frame boundary, then capture the actual RTL active pixels.
  @(posedge vs);
  $sformat(name,"frame-%0d.ppm",frame);
  fd=$fopen(name,"wb");$fwrite(fd,"P6\n320 240\n255\n");pixels=0;
  while(pixels<320*240)begin
   @(posedge clk);#1;
   if(de)begin $fwrite(fd,"%c%c%c",rgb[23:16],rgb[15:8],rgb[7:0]);pixels=pixels+1;end
  end
  $fclose(fd);
 end
 $display("Captured 8 actual RTL video states at native 320x240");$finish;
end
endmodule
