`timescale 1ns/1ps
module tb_b008_video;
parameter integer BUILD=8, REVISION=0, FRAMES=11;
reg clk=0;
always #5 clk=~clk;
wire [23:0] rgb;
wire de,hs,vs;
reg [3:0] status=0;
reg [31:0] completed=0,loaded=0;
reg [31:0] shown_generation=0;
b008_video #(.BUILD_NUMBER(BUILD),.BUILD_REVISION(REVISION)) display(.clk(clk),.reset_n(1'b1),.status(status),.generation(shown_generation),
 .loaded_generation(loaded),.completed(completed),.error(3'd0),.elapsed(32'd1000),
 .rgb(rgb),.de(de),.hs(hs),.vs(vs));
integer frame,pixels,fd;
reg [255:0] name;
initial begin
 for(frame=0;frame<FRAMES;frame=frame+1)begin
  status=frame;completed=frame>2?(BUILD==4?10000:BUILD==3?32:1):0;loaded=frame==4?(BUILD==4?10000:BUILD==3?32:1):0;
  shown_generation=BUILD==4?10000:BUILD==3?32:1;
  if(BUILD==5)begin
   shown_generation=frame==0?0:frame==4?64:2;
   loaded=frame==0?0:3;completed=frame==4?64:0;
  end
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
 $display("Captured %0d actual RTL video states at native 320x240",FRAMES);$finish;
end
endmodule
