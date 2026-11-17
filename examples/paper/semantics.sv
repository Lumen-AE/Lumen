// Small independent semantic regression fixture for the optional RTL frontend.
module semantics(
  input logic clk, rst_n, enable, sync_reset, select,
  input logic signed [3:0] a, b,
  output logic [3:0] q, q_sync, sum, selected,
  output logic signed_less, unsigned_less
);
  assign sum = a + b;
  assign selected = select ? a : b;
  assign signed_less = a < b;
  assign unsigned_less = $unsigned(a) < $unsigned(b);
  always_ff @(posedge clk or negedge rst_n)
    if (!rst_n) q <= 4'ha;
    else if (enable) q <= selected;
  always_ff @(posedge clk)
    if (sync_reset) q_sync <= 4'h3;
    else if (enable) q_sync <= selected;
endmodule
