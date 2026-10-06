//
// User core top-level
//
// Instantiated by the real top-level: apf_top
//

`default_nettype none

module core_top (

//
// physical connections
//

///////////////////////////////////////////////////
// clock inputs 74.25mhz. not phase aligned, so treat these domains as asynchronous

input   wire            clk_74a, // mainclk1
input   wire            clk_74b, // mainclk1 

///////////////////////////////////////////////////
// cartridge interface
// switches between 3.3v and 5v mechanically
// output enable for multibit translators controlled by pic32

// GBA AD[15:8]
inout   wire    [7:0]   cart_tran_bank2,
output  wire            cart_tran_bank2_dir,

// GBA AD[7:0]
inout   wire    [7:0]   cart_tran_bank3,
output  wire            cart_tran_bank3_dir,

// GBA A[23:16]
inout   wire    [7:0]   cart_tran_bank1,
output  wire            cart_tran_bank1_dir,

// GBA [7] PHI#
// GBA [6] WR#
// GBA [5] RD#
// GBA [4] CS1#/CS#
//     [3:0] unwired
inout   wire    [7:4]   cart_tran_bank0,
output  wire            cart_tran_bank0_dir,

// GBA CS2#/RES#
inout   wire            cart_tran_pin30,
output  wire            cart_tran_pin30_dir,
// when GBC cart is inserted, this signal when low or weak will pull GBC /RES low with a special circuit
// the goal is that when unconfigured, the FPGA weak pullups won't interfere.
// thus, if GBC cart is inserted, FPGA must drive this high in order to let the level translators
// and general IO drive this pin.
output  wire            cart_pin30_pwroff_reset,

// GBA IRQ/DRQ
inout   wire            cart_tran_pin31,
output  wire            cart_tran_pin31_dir,

// infrared
input   wire            port_ir_rx,
output  wire            port_ir_tx,
output  wire            port_ir_rx_disable, 

// GBA link port
inout   wire            port_tran_si,
output  wire            port_tran_si_dir,
inout   wire            port_tran_so,
output  wire            port_tran_so_dir,
inout   wire            port_tran_sck,
output  wire            port_tran_sck_dir,
inout   wire            port_tran_sd,
output  wire            port_tran_sd_dir,
 
///////////////////////////////////////////////////
// cellular psram 0 and 1, two chips (64mbit x2 dual die per chip)

output  wire    [21:16] cram0_a,
inout   wire    [15:0]  cram0_dq,
input   wire            cram0_wait,
output  wire            cram0_clk,
output  wire            cram0_adv_n,
output  wire            cram0_cre,
output  wire            cram0_ce0_n,
output  wire            cram0_ce1_n,
output  wire            cram0_oe_n,
output  wire            cram0_we_n,
output  wire            cram0_ub_n,
output  wire            cram0_lb_n,

output  wire    [21:16] cram1_a,
inout   wire    [15:0]  cram1_dq,
input   wire            cram1_wait,
output  wire            cram1_clk,
output  wire            cram1_adv_n,
output  wire            cram1_cre,
output  wire            cram1_ce0_n,
output  wire            cram1_ce1_n,
output  wire            cram1_oe_n,
output  wire            cram1_we_n,
output  wire            cram1_ub_n,
output  wire            cram1_lb_n,

///////////////////////////////////////////////////
// sdram, 512mbit 16bit

output  wire    [12:0]  dram_a,
output  wire    [1:0]   dram_ba,
inout   wire    [15:0]  dram_dq,
output  wire    [1:0]   dram_dqm,
output  wire            dram_clk,
output  wire            dram_cke,
output  wire            dram_ras_n,
output  wire            dram_cas_n,
output  wire            dram_we_n,

///////////////////////////////////////////////////
// sram, 1mbit 16bit

output  wire    [16:0]  sram_a,
inout   wire    [15:0]  sram_dq,
output  wire            sram_oe_n,
output  wire            sram_we_n,
output  wire            sram_ub_n,
output  wire            sram_lb_n,

///////////////////////////////////////////////////
// vblank driven by dock for sync in a certain mode

input   wire            vblank,

///////////////////////////////////////////////////
// i/o to 6515D breakout usb uart

output  wire            dbg_tx,
input   wire            dbg_rx,

///////////////////////////////////////////////////
// i/o pads near jtag connector user can solder to

output  wire            user1,
input   wire            user2,

///////////////////////////////////////////////////
// RFU internal i2c bus 

inout   wire            aux_sda,
output  wire            aux_scl,

///////////////////////////////////////////////////
// RFU, do not use
output  wire            vpll_feed,


//
// logical connections
//

///////////////////////////////////////////////////
// video, audio output to scaler
output  wire    [23:0]  video_rgb,
output  wire            video_rgb_clock,
output  wire            video_rgb_clock_90,
output  wire            video_de,
output  wire            video_skip,
output  wire            video_vs,
output  wire            video_hs,
    
output  wire            audio_mclk,
input   wire            audio_adc,
output  wire            audio_dac,
output  wire            audio_lrck,

///////////////////////////////////////////////////
// bridge bus connection
// synchronous to clk_74a
output  wire            bridge_endian_little,
input   wire    [31:0]  bridge_addr,
input   wire            bridge_rd,
output  reg     [31:0]  bridge_rd_data,
input   wire            bridge_wr,
input   wire    [31:0]  bridge_wr_data,

///////////////////////////////////////////////////
// controller data
// 
// key bitmap:
//   [0]    dpad_up
//   [1]    dpad_down
//   [2]    dpad_left
//   [3]    dpad_right
//   [4]    face_a
//   [5]    face_b
//   [6]    face_x
//   [7]    face_y
//   [8]    trig_l1
//   [9]    trig_r1
//   [10]   trig_l2
//   [11]   trig_r2
//   [12]   trig_l3
//   [13]   trig_r3
//   [14]   face_select
//   [15]   face_start
//   [31:28] type
// joy values - unsigned
//   [ 7: 0] lstick_x
//   [15: 8] lstick_y
//   [23:16] rstick_x
//   [31:24] rstick_y
// trigger values - unsigned
//   [ 7: 0] ltrig
//   [15: 8] rtrig
//
input   wire    [31:0]  cont1_key,
input   wire    [31:0]  cont2_key,
input   wire    [31:0]  cont3_key,
input   wire    [31:0]  cont4_key,
input   wire    [31:0]  cont1_joy,
input   wire    [31:0]  cont2_joy,
input   wire    [31:0]  cont3_joy,
input   wire    [31:0]  cont4_joy,
input   wire    [15:0]  cont1_trig,
input   wire    [15:0]  cont2_trig,
input   wire    [15:0]  cont3_trig,
input   wire    [15:0]  cont4_trig
    
);

// not using the IR port, so turn off both the LED, and
// disable the receive circuit to save power
assign port_ir_tx = 0;
assign port_ir_rx_disable = 1;

// bridge endianness
assign bridge_endian_little = 0;

// cart is unused, so set all level translators accordingly
// directions are 0:IN, 1:OUT
assign cart_tran_bank3 = 8'hzz;
assign cart_tran_bank3_dir = 1'b0;
assign cart_tran_bank2 = 8'hzz;
assign cart_tran_bank2_dir = 1'b0;
assign cart_tran_bank1 = 8'hzz;
assign cart_tran_bank1_dir = 1'b0;
assign cart_tran_bank0 = 4'hf;
assign cart_tran_bank0_dir = 1'b1;
assign cart_tran_pin30 = 1'b0;      // reset or cs2, we let the hw control it by itself
assign cart_tran_pin30_dir = 1'bz;
assign cart_pin30_pwroff_reset = 1'b0;  // hardware can control this
assign cart_tran_pin31 = 1'bz;      // input
assign cart_tran_pin31_dir = 1'b0;  // input

// link port is unused, set to input only to be safe
// each bit may be bidirectional in some applications
assign port_tran_so = 1'bz;
assign port_tran_so_dir = 1'b0;     // SO is output only
assign port_tran_si = 1'bz;
assign port_tran_si_dir = 1'b0;     // SI is input only
assign port_tran_sck = 1'bz;
assign port_tran_sck_dir = 1'b0;    // clock direction can change
assign port_tran_sd = 1'bz;
assign port_tran_sd_dir = 1'b0;     // SD is input and not used

// tie off the rest of the pins we are not using
assign cram0_a = 'h0;
assign cram0_dq = {16{1'bZ}};
assign cram0_clk = 0;
assign cram0_adv_n = 1;
assign cram0_cre = 0;
assign cram0_ce0_n = 1;
assign cram0_ce1_n = 1;
assign cram0_oe_n = 1;
assign cram0_we_n = 1;
assign cram0_ub_n = 1;
assign cram0_lb_n = 1;

assign cram1_a = 'h0;
assign cram1_dq = {16{1'bZ}};
assign cram1_clk = 0;
assign cram1_adv_n = 1;
assign cram1_cre = 0;
assign cram1_ce0_n = 1;
assign cram1_ce1_n = 1;
assign cram1_oe_n = 1;
assign cram1_we_n = 1;
assign cram1_ub_n = 1;
assign cram1_lb_n = 1;

assign dram_a = 'h0;
assign dram_ba = 'h0;
assign dram_dq = {16{1'bZ}};
assign dram_dqm = 'h0;
assign dram_clk = 'h0;
assign dram_cke = 'h0;
assign dram_ras_n = 'h1;
assign dram_cas_n = 'h1;
assign dram_we_n = 'h1;

assign sram_a = 'h0;
assign sram_dq = {16{1'bZ}};
assign sram_oe_n  = 1;
assign sram_we_n  = 1;
assign sram_ub_n  = 1;
assign sram_lb_n  = 1;

assign dbg_tx = 1'bZ;
assign user1 = 1'bZ;
assign aux_scl = 1'bZ;
assign vpll_feed = 1'bZ;

// Interface and unused IO tie-offs above are retained from open-fpga/core-template.
// B008 CPU supervises the unchanged B007 engine; only the engine owns APF.
wire clk_pixel, clk_pixel_90, pll_locked, pll_ready;
synch_3 lock_sync(pll_locked, pll_ready, clk_74a);
mf_pllbase mp1(.refclk(clk_74a), .rst(1'b0), .outclk_0(clk_pixel),
    .outclk_1(clk_pixel_90), .locked(pll_locked));
wire reset_n;
wire [31:0] command_read_data, payload_read_data;
wire request_read, request_write;
wire [15:0] request_read_id, request_write_id;
wire [31:0] request_write_size;
wire target_read, target_write, target_ack, target_done;
wire [2:0] target_err;
wire [15:0] target_id;
wire [31:0] target_offset, target_address, target_length;
wire [3:0] probe_status;
wire [31:0] generation, loaded_generation, completed, elapsed;
wire [2:0] last_error;
localparam LAB_SLOT=16'h27;
localparam LAB_MAX_FILE=262144;
wire cpu_clk,cpu_pll_locked,cpu_ready_engine;
synch_3 cpu_lock_sync(cpu_pll_locked,cpu_ready_engine,clk_74a);
b008_cpu_pll mp_cpu(.refclk(clk_74a),.cpu_clk(cpu_clk),.locked(cpu_pll_locked));
// Assert reset asynchronously; release only after two stable CPU clock edges.
(* async_reg="true" *) reg[1:0] cpu_release=0;
always @(posedge cpu_clk or negedge cpu_pll_locked or negedge reset_n)begin
 if(!cpu_pll_locked || !reset_n)cpu_release<=0;
 else if(cont1_key[6])cpu_release<=0;
 else cpu_release<={cpu_release[0],1'b1};
end
wire cpu_reset=!cpu_release[1];
wire cpu_write,cpu_read,cpu_fault;
wire[31:0]firmware_ready;
wire[31:0]power_source,cpu_source;
wire[511:0]power_snapshot;wire[255:0]cpu_snapshot;
altsource_probe #(.sld_auto_instance_index("YES"),.sld_instance_index(0),.instance_id("SDW8"),
 .probe_width(511),.source_width(32),.source_initial_value("0"),.enable_metastability("NO")) engine_debug(
 .source_clk(clk_74a),.source_ena(1'b1),.source(power_source),.probe(power_snapshot[510:0]));
altsource_probe #(.sld_auto_instance_index("YES"),.sld_instance_index(1),.instance_id("CPU8"),
 .probe_width(256),.source_width(32),.source_initial_value("0"),.enable_metastability("NO")) cpu_debug(
 .source_clk(clk_74a),.source_ena(1'b1),.source(cpu_source),.probe(cpu_snapshot));
b008_soc cpu_soc(.cpu_clk(cpu_clk),.engine_clk(clk_74a),.cpu_reset(cpu_reset),.buttons(cont1_key),
 .engine_status(probe_status),.engine_error(last_error),.engine_completed(completed),.engine_tag(loaded_generation),
 .write_pulse(cpu_write),.read_pulse(cpu_read),.debug_source(cpu_source),.debug_snapshot(cpu_snapshot),
 .cpu_fault(cpu_fault),.firmware_ready(firmware_ready),.sim_finished(),.sim_code(),.sim_marker());
always @(*) begin
    bridge_rd_data = 0;
    if (bridge_addr[31:24] == 8'hF8) bridge_rd_data = command_read_data;
    else bridge_rd_data = payload_read_data;
end

core_bridge_cmd commands(
    .clk(clk_74a), .reset_n(reset_n),
    .bridge_endian_little(bridge_endian_little), .bridge_addr(bridge_addr),
    .bridge_rd(bridge_rd), .bridge_rd_data(command_read_data),
    .bridge_wr(bridge_wr), .bridge_wr_data(bridge_wr_data),
    .status_boot_done(pll_ready&&cpu_ready_engine), .status_setup_done(pll_ready&&cpu_ready_engine), .status_running(reset_n),
    .dataslot_requestread(request_read), .dataslot_requestread_id(request_read_id),
    .dataslot_requestread_ack(1'b1), .dataslot_requestread_ok((request_read_id == LAB_SLOT
 )),
    .dataslot_requestwrite(request_write), .dataslot_requestwrite_id(request_write_id),
    .dataslot_requestwrite_size(request_write_size), .dataslot_requestwrite_ack(1'b1),
    .dataslot_requestwrite_ok((request_write_id == LAB_SLOT
 ) && request_write_size <= LAB_MAX_FILE),
    .dataslot_update(), .dataslot_update_id(), .dataslot_update_size(),
    .dataslot_allcomplete(), .rtc_epoch_seconds(), .rtc_date_bcd(), .rtc_time_bcd(), .rtc_valid(),
    .savestate_supported(1'b0), .savestate_addr(32'd0), .savestate_size(32'd0),
    .savestate_maxloadsize(32'd0), .osnotify_inmenu(),
    .savestate_start(), .savestate_start_ack(1'b0), .savestate_start_busy(1'b0),
    .savestate_start_ok(1'b0), .savestate_start_err(1'b0),
    .savestate_load(), .savestate_load_ack(1'b0), .savestate_load_busy(1'b0),
    .savestate_load_ok(1'b0), .savestate_load_err(1'b0),
    .target_dataslot_read(target_read), .target_dataslot_write(target_write),
    .target_dataslot_getfile(1'b0), .target_dataslot_openfile(1'b0),
    .target_dataslot_ack(target_ack), .target_dataslot_done(target_done), .target_dataslot_err(target_err),
    .target_dataslot_id(target_id), .target_dataslot_slotoffset(target_offset),
    .target_dataslot_bridgeaddr(target_address), .target_dataslot_length(target_length),
    .target_buffer_param_struct(32'd0), .target_buffer_resp_struct(32'd0),
    .datatable_addr(10'd0), .datatable_wren(1'b0), .datatable_data(32'd0), .datatable_q());

lab_powercut probe(.debug_source(power_source),.debug_probe(power_snapshot),.target_ack(target_ack),
 .clk(clk_74a),.reset_n(1'b1),.write_button(cpu_write),.read_button(cpu_read),
 .bridge_addr(bridge_addr),.bridge_rd(bridge_rd),.bridge_wr(bridge_wr),.bridge_wr_data(bridge_wr_data),.bridge_rd_data(payload_read_data),
 .target_read(target_read),.target_write(target_write),.slot_id(target_id),.slot_offset(target_offset),
 .source_addr(target_address),.transfer_length(target_length),.target_done(target_done),.target_err(target_err),
 .status(probe_status),.generation(generation),.loaded_generation(loaded_generation),.completed(completed),.last_error(last_error),.elapsed_cycles(elapsed));
// Display only. The engine data and reset/fault telemetry may tear during
// transitions; they are never used to authorize a transfer.
wire[136:0]display_data;
synch_3 #(.WIDTH(137)) display_sync({cpu_fault,cpu_reset,probe_status,generation,loaded_generation,completed,last_error,elapsed},display_data,clk_pixel);
assign video_rgb_clock=clk_pixel;assign video_rgb_clock_90=clk_pixel_90;assign video_skip=0;
wire[3:0]display_status=display_data[136]?9:((display_data[135] && (display_data[134:131]==0 || display_data[134:131]==4 || display_data[134:131]==5))?10:display_data[134:131]);
b008_video screen(.clk(clk_pixel),.reset_n(pll_ready),.status(display_status),.generation(display_data[130:99]),
 .loaded_generation(display_data[98:67]),.completed(display_data[66:35]),.error(display_data[34:32]),.elapsed(display_data[31:0]),
 .rgb(video_rgb),.de(video_de),.hs(video_hs),.vs(video_vs));
reg[7:0]audio_divider=0;always @(posedge clk_pixel)audio_divider<=audio_divider+1;
assign audio_mclk=clk_pixel;assign audio_lrck=audio_divider[7];assign audio_dac=0;
endmodule
`default_nettype wire
