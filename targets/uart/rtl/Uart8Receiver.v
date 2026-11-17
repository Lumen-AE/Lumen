`include "UartStates.vh"

/*
 * 8-bit UART Receiver (simplified for verification)
 *
 * Simplified from TimRudy/uart-verilog Uart8Receiver:
 *   - Removed in_hold_reg / in_prior_hold_reg / in_current_hold_reg (signal hold checks)
 *   - Removed out_hold_count (timed output validity)
 *   - Removed READY state (STOP_BIT goes directly to IDLE)
 *   - Simplified IDLE start-bit detection (no hold-time gating)
 *   - Simplified RESET (no err persistence)
 *
 * Retained:
 *   - Double-register metastability protection (in_reg)
 *   - 16x oversampling with mid-bit sampling
 *   - IDLE → START_BIT → DATA_BITS → STOP_BIT → IDLE state machine
 *   - err output on bad stop bit
 *   - en/disable support
 *
 * Source: https://github.com/TimRudy/uart-verilog (simplified)
 */
module Uart8Receiver (
    input wire clk,      // rx data sampling rate (16x baud)
    input wire en,
    input wire in,       // rx line
    output reg busy,     // transaction is in progress
    output reg done,     // end of transaction (high for 16 clk ticks)
    output reg err,      // error while receiving data
    output reg [7:0] out // the received data assembled in parallel form
);

reg [2:0] state         = `RESET;
reg [1:0] in_reg        = 2'b0;  // double-register for metastability
reg [3:0] sample_count  = 4'b0;  // count ticks for 16x oversample
reg [2:0] bit_index     = 3'b0;  // index for 8-bit data
reg [7:0] received_data = 8'b0;  // shift reg for deserialized data
wire in_sample;

/*
 * Double-register the incoming data for metastability protection
 */
always @(posedge clk) begin
    in_reg <= { in_reg[0], in };
end

assign in_sample = in_reg[1];

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
            sample_count  <= 4'b0;
            received_data <= 8'b0;
            busy          <= 1'b0;
            done          <= 1'b0;
            err           <= 1'b0;
            out           <= 8'b0;
            if (en) begin
                state     <= `IDLE;
            end
        end

        `IDLE: begin
            done <= 1'b0;
            err  <= 1'b0;
            if (!in_sample) begin
                // Falling edge detected — potential start bit
                sample_count <= sample_count + 4'b1;
                if (sample_count == 4'b0111) begin // reached mid-bit (tick 7)
                    // Confirm start bit is still low at mid-point
                    sample_count <= 4'b0;
                    busy         <= 1'b1;
                    state        <= `START_BIT;
                end
            end else begin
                sample_count <= 4'b0;
            end
        end

        `START_BIT: begin
            /*
             * Wait one full baud interval (16 ticks) to the mid-point
             * of the first data bit
             */
            sample_count      <= sample_count + 4'b1;
            if (&sample_count) begin // reached 15
                bit_index     <= 3'b1;
                received_data <= { in_sample, 7'b0 };
                out           <= 8'b0;
                state         <= `DATA_BITS;
            end
        end

        `DATA_BITS: begin
            /*
             * Take 8 baud intervals to receive serial data
             */
            sample_count      <= sample_count + 4'b1;
            if (&sample_count) begin // reached 15 — sample at mid-bit
                received_data <= { in_sample, received_data[7:1] };
                bit_index     <= bit_index + 3'b1;
                if (&bit_index) begin
                    state     <= `STOP_BIT;
                end
            end
        end

        `STOP_BIT: begin
            /*
             * Sample stop bit at mid-point:
             *   - If high → valid frame, output data, assert done
             *   - If low  → frame error, assert err
             * Then return to IDLE
             */
            sample_count          <= sample_count + 4'b1;
            if (&sample_count) begin // reached 15 — mid-bit sample
                if (in_sample) begin
                    // Valid stop bit
                    done          <= 1'b1;
                    out           <= received_data;
                end else begin
                    // Invalid stop bit — frame error
                    err           <= 1'b1;
                end
                busy              <= 1'b0;
                received_data     <= 8'b0;
                sample_count      <= 4'b0;
                state             <= `IDLE;
            end
        end
    endcase
end

endmodule
