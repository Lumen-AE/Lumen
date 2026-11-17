// uart_top.v — Thin wrapper around TimRudy/uart-verilog Uart8 core
//
// Purpose: Provide a single top-level file for cocotb/Verilator verification.
// The wrapper simply re-exports the Uart8 interface with parameter overrides
// suitable for simulation (fast baud rate to keep sim time short).
//
// Source: https://github.com/TimRudy/uart-verilog (MIT-compatible)
//
// Interface signals (directly driven by cocotb TB):
//   clk           — system clock
//   rxEn, rx      — RX enable, serial RX input
//   txEn, txStart — TX enable, TX start pulse
//   in[7:0]       — parallel TX data
//   out[7:0]      — parallel RX data
//   tx            — serial TX output
//   txBusy, txDone, rxBusy, rxDone, rxErr — status

`include "BaudRateGenerator.v"
`include "Uart8Receiver.v"
`include "Uart8Transmitter.v"

module uart_top #(
    parameter CLOCK_RATE   = 50000000,  // 50 MHz sim clock
    parameter BAUD_RATE    = 115200
)(
    input  wire       clk,

    // RX interface
    input  wire       rxEn,
    input  wire       rx,
    output wire       rxBusy,
    output wire       rxDone,
    output wire       rxErr,
    output wire [7:0] out,

    // TX interface
    input  wire       txEn,
    input  wire       txStart,
    input  wire [7:0] in,
    output wire       txBusy,
    output wire       txDone,
    output wire       tx
);

localparam RX_OVERSAMPLE_RATE = 16;

wire rxClk;
wire txClk;

BaudRateGenerator #(
    .CLOCK_RATE(CLOCK_RATE),
    .BAUD_RATE(BAUD_RATE),
    .RX_OVERSAMPLE_RATE(RX_OVERSAMPLE_RATE)
) u_baudgen (
    .clk(clk),
    .rxClk(rxClk),
    .txClk(txClk)
);

Uart8Receiver u_rx (
    .clk(rxClk),
    .en(rxEn),
    .in(rx),
    .busy(rxBusy),
    .done(rxDone),
    .err(rxErr),
    .out(out)
);

Uart8Transmitter u_tx (
    .clk(txClk),
    .en(txEn),
    .start(txStart),
    .in(in),
    .busy(txBusy),
    .done(txDone),
    .out(tx)
);

endmodule
