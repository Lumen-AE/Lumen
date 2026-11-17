`include "UartStates.vh"

/*
 * 8-bit UART Transmitter (simplified for verification)
 *
 * Simplified from TimRudy/uart-verilog Uart8Transmitter:
 *   - Removed TURBO_FRAMES parameter (always non-turbo / forgiving mode)
 *   - Removed default branch (4 used states out of 3-bit encoding)
 *
 * Retained:
 *   - Full RESET → IDLE → START_BIT → DATA_BITS → STOP_BIT state machine
 *   - Back-to-back frame support (start held during STOP_BIT)
 *   - en/disable support
 *   - busy/done signaling
 *
 * Source: https://github.com/TimRudy/uart-verilog (simplified)
 */
module Uart8Transmitter (
    input wire clk,      // baud rate clock
    input wire en,
    input wire start,    // start transmission
    input wire [7:0] in, // parallel data to transmit
    output reg busy,     // transmit is in progress
    output reg done,     // end of transmission
    output reg out       // tx line for serial data
);

reg [2:0] state     = `RESET;
reg [7:0] in_data   = 8'b0; // shift reg for the data to transmit serially
reg [2:0] bit_index = 3'b0; // index for 8-bit data

/*
 * Disable at any time in the flow
 */
always @(posedge clk) begin
    if (!en) begin
        state <= `RESET;
    end
end

/*
 * State machine
 */
always @(posedge clk) begin
    case (state)
        `RESET: begin
            bit_index <= 3'b0;
            busy      <= 1'b0;
            done      <= 1'b0;
            out       <= 1'b1; // drive the line high for IDLE state
            if (en) begin
                state <= `IDLE;
            end
        end

        `IDLE: begin
            done <= 1'b0;
            busy <= 1'b0;
            if (start) begin
                in_data <= in; // register the input data
                state   <= `START_BIT;
            end
        end

        `START_BIT: begin
            bit_index <= 3'b0;
            busy      <= 1'b1;
            done      <= 1'b0;
            out       <= 1'b0; // send start bit (low)
            state     <= `DATA_BITS;
        end

        `DATA_BITS: begin // 8 clock cycles for data bits
            in_data   <= { 1'b0, in_data[7:1] };
            out       <= in_data[0];
            bit_index <= bit_index + 3'b1;
            if (&bit_index) begin
                state <= `STOP_BIT;
            end
        end

        `STOP_BIT: begin
            done              <= 1'b1; // signal transmission complete
            out               <= 1'b1; // stop bit (high)
            if (start) begin
                if (done == 1'b0) begin // first sub-state of STOP_BIT
                    in_data   <= in;    // register new input data
                    state     <= `STOP_BIT; // keep mark state one extra cycle
                end else begin          // second sub-state
                    in_data   <= in;    // register new input data
                    done      <= 1'b0;
                    state     <= `START_BIT; // go to next frame
                end
            end else begin
                if (done == 1'b0) begin // first sub-state: hold stop bit
                    state     <= `STOP_BIT;
                end else begin          // second sub-state: done held for 2 txClk
                    state     <= `IDLE;
                end
            end
        end
    endcase
end

endmodule
