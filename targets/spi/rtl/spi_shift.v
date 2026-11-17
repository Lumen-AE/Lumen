`include "spi_defines.vh"

/*
 * SPI Shift Register (Master mode)
 *
 * Handles the 8-bit shift register for SPI data transfer:
 * - MOSI: shifts out MSB-first (configurable via LSB_FIRST)
 * - MISO: shifts in at each sampling edge
 *
 * State machine: IDLE → LOAD → SHIFT (8 bits) → DONE → CS_DEASSERT → IDLE
 */
module spi_shift #(
    parameter DATA_WIDTH = 8
)(
    input  wire                   clk,
    input  wire                   rst_n,
    input  wire                   start,        // start transfer
    input  wire [DATA_WIDTH-1:0]  tx_data,      // parallel data to send
    input  wire                   miso,         // serial input from slave
    input  wire                   sclk_edge,    // edge pulse from clkgen
    input  wire                   cpol,         // clock polarity
    input  wire                   cpha,         // clock phase
    input  wire                   sclk_out,     // current SCLK level
    input  wire                   lsb_first,    // 0=MSB first, 1=LSB first
    output reg                    mosi,         // serial output to slave
    output reg  [DATA_WIDTH-1:0]  rx_data,      // parallel received data
    output reg                    busy,         // transfer in progress
    output reg                    done,         // transfer complete pulse
    output reg                    cs_n          // chip select (active low)
);

reg [2:0]              state;
reg [3:0]              bit_cnt;     // 4 bits to count 0..8
reg [DATA_WIDTH-1:0]   shift_out;
reg [DATA_WIDTH-1:0]   shift_in;

/*
 * Determine sampling and shifting edges based on CPOL and CPHA:
 *   Mode 0 (CPOL=0, CPHA=0): shift on falling, sample on rising
 *   Mode 1 (CPOL=0, CPHA=1): shift on rising,  sample on falling
 *   Mode 2 (CPOL=1, CPHA=0): shift on rising,  sample on falling
 *   Mode 3 (CPOL=1, CPHA=1): shift on falling, sample on rising
 */
wire is_sample_edge = sclk_edge & (sclk_out == (cpol ^ cpha ? 1'b0 : 1'b1));
wire is_shift_edge  = sclk_edge & (sclk_out == (cpol ^ cpha ? 1'b1 : 1'b0));

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state        <= `SPI_IDLE;
        shift_out    <= {DATA_WIDTH{1'b0}};
        shift_in     <= {DATA_WIDTH{1'b0}};
        rx_data      <= {DATA_WIDTH{1'b0}};
        mosi         <= 1'b0;
        busy         <= 1'b0;
        done         <= 1'b0;
        cs_n         <= 1'b1;
        bit_cnt      <= 4'b0;
    end else begin
        done <= 1'b0; // default: done is a single-cycle pulse

        case (state)
            `SPI_IDLE: begin
                busy         <= 1'b0;
                cs_n         <= 1'b1;
                mosi         <= 1'b0;
                if (start) begin
                    shift_out <= tx_data;
                    shift_in  <= {DATA_WIDTH{1'b0}};
                    bit_cnt   <= 4'b0;
                    busy      <= 1'b1;
                    cs_n      <= 1'b0; // assert chip select
                    state     <= `SPI_LOAD;
                end
            end

            `SPI_LOAD: begin
                // Drive first bit on MOSI immediately after CS assertion
                if (lsb_first)
                    mosi <= shift_out[0];
                else
                    mosi <= shift_out[DATA_WIDTH-1];
                state <= `SPI_SHIFT;
            end

            `SPI_SHIFT: begin
                // Sample MISO on appropriate edge
                if (is_sample_edge) begin
                    if (lsb_first)
                        shift_in <= {miso, shift_in[DATA_WIDTH-1:1]};
                    else
                        shift_in <= {shift_in[DATA_WIDTH-2:0], miso};
                    bit_cnt <= bit_cnt + 4'b1;
                end

                // Shift MOSI on appropriate edge
                if (is_shift_edge) begin
                    if (lsb_first) begin
                        shift_out <= {1'b0, shift_out[DATA_WIDTH-1:1]};
                        mosi      <= shift_out[1]; // next bit
                    end else begin
                        shift_out <= {shift_out[DATA_WIDTH-2:0], 1'b0};
                        mosi      <= shift_out[DATA_WIDTH-2]; // next bit
                    end
                end

                // Transition to DONE after all 8 bits sampled
                if (bit_cnt == 4'd7 && is_sample_edge) begin
                    state <= `SPI_DONE;
                end
            end

            `SPI_DONE: begin
                // shift_in now contains all 8 sampled bits (updated last cycle)
                rx_data <= shift_in;
                done    <= 1'b1;
                state   <= `SPI_CS_DEASSERT;
            end

            `SPI_CS_DEASSERT: begin
                // Hold CS for one extra cycle, then deassert
                cs_n  <= 1'b1;
                busy  <= 1'b0;
                mosi  <= 1'b0;
                state <= `SPI_IDLE;
            end

            // verilator coverage_off
            default: begin
                state <= `SPI_IDLE;
            end
            // verilator coverage_on
        endcase
    end
end

endmodule
