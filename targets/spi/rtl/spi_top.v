// spi_top.v — SPI Master Controller (8-bit, Mode 0/1/2/3)
//
// Purpose: Provide a single top-level file for cocotb/Verilator verification.
// Implements a simple 8-bit SPI Master with configurable clock polarity (CPOL),
// clock phase (CPHA), bit order (MSB/LSB first), and programmable clock divider.
//
// Interface signals (directly driven by cocotb TB):
//   clk          — system clock
//   rst_n        — active-low reset
//   start        — start SPI transfer
//   tx_data[7:0] — parallel data to transmit on MOSI
//   cpol         — clock polarity (0: idle low, 1: idle high)
//   cpha         — clock phase (0: sample on leading edge, 1: sample on trailing edge)
//   lsb_first    — bit order (0: MSB first, 1: LSB first)
//   divider[7:0] — clock divider value: SCLK freq = clk / (2*(divider+1))
//   miso         — serial data input from slave
//   rx_data[7:0] — parallel received data
//   mosi         — serial data output to slave
//   sclk         — SPI serial clock output
//   cs_n         — chip select (active low)
//   busy         — transfer in progress
//   done         — transfer complete (single-cycle pulse)

`include "spi_clkgen.v"
`include "spi_shift.v"

module spi_top #(
    parameter DATA_WIDTH = 8,
    parameter DIV_WIDTH  = 8
)(
    input  wire                   clk,
    input  wire                   rst_n,

    // Control
    input  wire                   start,
    input  wire [DATA_WIDTH-1:0]  tx_data,
    input  wire                   cpol,
    input  wire                   cpha,
    input  wire                   lsb_first,
    input  wire [DIV_WIDTH-1:0]   divider,

    // SPI bus
    input  wire                   miso,
    output wire                   mosi,
    output wire                   sclk,
    output wire                   cs_n,

    // Status
    output wire [DATA_WIDTH-1:0]  rx_data,
    output wire                   busy,
    output wire                   done
);

wire sclk_edge;
wire sclk_internal;
wire shift_busy;

// Clock generator
spi_clkgen #(
    .DIV_WIDTH(DIV_WIDTH)
) u_clkgen (
    .clk       (clk),
    .rst_n     (rst_n),
    .enable    (shift_busy),     // enable clock only during transfer
    .divider   (divider),
    .cpol      (cpol),
    .sclk_out  (sclk_internal),
    .sclk_edge (sclk_edge)
);

// Shift register / state machine
spi_shift #(
    .DATA_WIDTH(DATA_WIDTH)
) u_shift (
    .clk       (clk),
    .rst_n     (rst_n),
    .start     (start),
    .tx_data   (tx_data),
    .miso      (miso),
    .sclk_edge (sclk_edge),
    .cpol      (cpol),
    .cpha      (cpha),
    .sclk_out  (sclk_internal),
    .lsb_first (lsb_first),
    .mosi      (mosi),
    .rx_data   (rx_data),
    .busy      (shift_busy),
    .done      (done),
    .cs_n      (cs_n)
);

assign sclk = sclk_internal;
assign busy = shift_busy;

endmodule
