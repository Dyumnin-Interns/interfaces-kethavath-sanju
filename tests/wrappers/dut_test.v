module dut_test;

  // Declare signals for DUT
  reg CLK;
  reg RST_N;
  reg [2:0] write_address;
  reg write_data;
  reg write_en;
  wire write_rdy;

  reg [2:0] read_address;
  reg read_en;
  wire read_data;
  wire read_rdy;

  // Instantiate the DUT
  dut uut(
    .CLK(CLK),
    .RST_N(RST_N),
    .write_address(write_address),
    .write_data(write_data),
    .write_en(write_en),
    .write_rdy(write_rdy),
    .read_address(read_address),
    .read_en(read_en),
    .read_data(read_data),
    .read_rdy(read_rdy)
  );

  initial begin
	$dumpfile("interface.vcd");
	$dumpvars;
  end


endmodule



