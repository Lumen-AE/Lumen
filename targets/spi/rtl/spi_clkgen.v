/*
 * SPI Clock Generator
 *
 * Divides system clock to produce SPI serial clock (SCLK).
 * Output frequency = clk / (2 * (DIVIDER + 1))
 *
 * The enable signal gates clock generation; when disabled, sclk_out is idle
 * (level depends on CPOL).
 */
module spi_clkgen #(
    parameter DIV_WIDTH = 8
)(
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 enable,
    input  wire [DIV_WIDTH-1:0] divider,   // clock divider value
    input  wire                 cpol,      // clock polarity
    output reg                  sclk_out,  // generated SPI clock
    output reg                  sclk_edge  // pulse on each SCLK edge (for shift logic)
);

reg [DIV_WIDTH-1:0] counter;
reg                 running;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        counter   <= {DIV_WIDTH{1'b0}};
        sclk_out  <= 1'b0;
        sclk_edge <= 1'b0;
        running   <= 1'b0;
    end else if (!enable) begin
        counter   <= {DIV_WIDTH{1'b0}};
        sclk_out  <= cpol;   // idle level
        sclk_edge <= 1'b0;
        running   <= 1'b0;
    end else begin
        sclk_edge <= 1'b0;
        if (counter == divider) begin
            counter   <= {DIV_WIDTH{1'b0}};
            sclk_out  <= ~sclk_out;
            sclk_edge <= 1'b1;
            running   <= 1'b1;
        end else begin
            counter <= counter + 1'b1;
        end
    end
end

endmodule
