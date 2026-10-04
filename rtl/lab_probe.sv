`default_nettype none
// One command owner, clk_74a only. Timeout is a latched fault, not cancellation.
module lab_probe #(
    parameter integer TIMEOUT_CYCLES = 742500000 // 10 seconds
)(
    input wire clk, input wire reset_n,
    input wire write_button, input wire read_button,
    input wire [31:0] bridge_addr, input wire bridge_rd, input wire bridge_wr,
    input wire [31:0] bridge_wr_data, output reg [31:0] bridge_rd_data,
    output reg target_read = 0, output reg target_write = 0,
    output wire [15:0] slot_id, output wire [31:0] slot_offset,
    output wire [31:0] source_addr, output wire [31:0] transfer_length,
    input wire target_done, input wire [2:0] target_err,
    output reg [3:0] status = 0,
    output reg [31:0] generation = 1,
    output reg [31:0] loaded_generation = 0,
    output reg [31:0] completed = 0,
    output reg [2:0] last_error = 0,
    output reg [31:0] elapsed_cycles = 0
);
    localparam [31:0] TX_BASE = 32'h10000000, RX_BASE = 32'h10000100;
    localparam [3:0] PREPARE = 1, CLEAR_DONE = 2, WAIT_DONE = 3,
        CHECK_READ = 4, IDLE = 0, FAULT = 5;
    reg [3:0] state = IDLE;
    reg [3:0] word_index = 0;
    reg is_read = 0, wr_previous = 0, rd_previous = 0, mismatch = 0, first_write = 1;
    reg [31:0] checksum = 0;
    reg [31:0] tx_mem[0:15];
    reg [31:0] rx_mem[0:15];
    // Async host read addresses are clocked into the RAM output once per clk_74a.
    // The next read strobe can therefore observe the preceding address (APF timing).
    reg [31:0] tx_q = 0, rx_q = 0;
    reg [15:0] received = 0;
    integer initial_index;
    reg [31:0] initial_checksum;
    `include "record_word.vh"
    initial begin
        initial_checksum = 0;
        for (initial_index = 0; initial_index < 16; initial_index = initial_index + 1) begin
            if (initial_index == 15) tx_mem[initial_index] = initial_checksum;
            else begin
                tx_mem[initial_index] = record_word(initial_index[3:0], 1);
                initial_checksum = initial_checksum ^ record_word(initial_index[3:0], 1);
            end
            rx_mem[initial_index] = 0;
        end
    end
    assign slot_id = 16'h22;
    assign slot_offset = 0;
    assign transfer_length = 64;
    assign source_addr = is_read ? RX_BASE : TX_BASE;
    always @(*) begin
        bridge_rd_data = 0;
        if (bridge_addr >= TX_BASE && bridge_addr < TX_BASE + 64)
            bridge_rd_data = tx_q;
        else if (bridge_addr >= RX_BASE && bridge_addr < RX_BASE + 64)
            bridge_rd_data = rx_q;
    end
    always @(posedge clk) begin
        tx_q <= tx_mem[bridge_addr[5:2]];
        rx_q <= rx_mem[bridge_addr[5:2]];
        // Only APF readback can write the RX region. TX never accepts host writes.
        if (bridge_wr && bridge_addr >= RX_BASE && bridge_addr < RX_BASE + 64 &&
            bridge_addr[1:0] == 0 && is_read &&
            (state == CLEAR_DONE || state == WAIT_DONE)) begin
            rx_mem[bridge_addr[5:2]] <= bridge_wr_data;
            received[bridge_addr[5:2]] <= 1'b1;
        end
        target_read <= 0;
        target_write <= 0;
        wr_previous <= write_button;
        rd_previous <= read_button;
        // Reset Enter does not release an outstanding command or alter its payload.
        // Only FPGA reconfiguration is the fault recovery boundary.
        case (state)
            IDLE: if (reset_n) begin
                if ((write_button && !wr_previous) || (read_button && !rd_previous)) begin
                    is_read <= !(write_button && !wr_previous);
                    if (write_button && !wr_previous) begin
                        if (!first_write) generation <= generation + 1'b1;
                        first_write <= 0;
                    end
                    word_index <= 0;
                    checksum <= 0;
                    received <= 0;
                    mismatch <= 0;
                    last_error <= 0;
                    elapsed_cycles <= 0;
                    status <= 1; // PREPARING
                    state <= PREPARE;
                end
            end
            PREPARE: begin
                if (is_read) rx_mem[word_index] <= 32'hdeadc0de;
                else begin
                    if (word_index == 15) tx_mem[word_index] <= checksum;
                    else begin
                        tx_mem[word_index] <= record_word(word_index, generation);
                        checksum <= checksum ^ record_word(word_index, generation);
                    end
                end
                if (word_index == 15) begin
                    target_read <= is_read;
                    target_write <= !is_read;
                    state <= CLEAR_DONE;
                    status <= 2; // WAITING
                end else word_index <= word_index + 1'b1;
            end
            CLEAR_DONE, WAIT_DONE: begin
                elapsed_cycles <= elapsed_cycles + 1'b1;
                if (elapsed_cycles >= TIMEOUT_CYCLES - 1) begin
                    state <= FAULT;
                    status <= 7; // TIMEOUT; never reopen local busy
                end else if (state == CLEAR_DONE) begin
                    if (!target_done) state <= WAIT_DONE;
                end else if (target_done) begin
                    completed <= completed + 1'b1;
                    last_error <= target_err;
                    if (target_err != 0) begin
                        status <= 6; // COMMAND ERROR
                        state <= IDLE;
                    end else if (is_read) begin
                        word_index <= 0;
                        loaded_generation <= rx_mem[3];
                        state <= CHECK_READ;
                    end else begin
                        status <= 3; // WRITE COMMAND OK (not durability)
                        state <= IDLE;
                    end
                end
            end
            CHECK_READ: begin
                if (rx_mem[word_index] != tx_mem[word_index] || received != 16'hffff)
                    mismatch <= 1;
                if (word_index == 15) begin
                    status <= (mismatch || rx_mem[15] != tx_mem[15] || received != 16'hffff) ? 5 : 4;
                    state <= IDLE;
                end else word_index <= word_index + 1'b1;
            end
            FAULT: begin end // late completions never authorize a second operation
            default: begin state <= FAULT; status <= 7; end
        endcase
    end
endmodule
`default_nettype wire
