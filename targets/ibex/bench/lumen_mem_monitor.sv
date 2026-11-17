// Source-derived official bus latency monitor.
interface lumen_mem_monitor_if (
  input clk_i,
  input rst_ni,

  input req_i,
  input gnt_i,
  input rvalid_i,

  output int   outstanding_requests_o,
  output logic single_cycle_response_o
);

  int outstanding_requests;
  logic outstanding_requests_inc, outstanding_requests_dec;
  logic no_outstanding_requests_last_cycle;

  assign outstanding_requests_inc = req_i & gnt_i;
  assign outstanding_requests_dec = rvalid_i;

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (~rst_ni) begin
      outstanding_requests               <= 0;
      no_outstanding_requests_last_cycle <= 1'b0;
    end else begin
      if (outstanding_requests_inc && !outstanding_requests_dec) begin
        outstanding_requests <= outstanding_requests + 1;
      end else if (!outstanding_requests_inc && outstanding_requests_dec) begin
        outstanding_requests <= outstanding_requests - 1;
      end

      no_outstanding_requests_last_cycle <= (outstanding_requests == 0) ||
        ((outstanding_requests == 1) && outstanding_requests_dec);
    end
  end

  assign outstanding_requests_o = outstanding_requests;
  assign single_cycle_response_o = no_outstanding_requests_last_cycle & rvalid_i;
endinterface
