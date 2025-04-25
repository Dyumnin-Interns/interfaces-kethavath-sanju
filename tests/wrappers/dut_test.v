module dut_test(
  input  wire        CLK,
  input  wire        RST_N,

  // action method write
  input  wire [2:0]  write_address,
  input  wire        write_data,
  input  wire        write_en,
  output wire        write_rdy,

  // actionvalue method read
  input  wire [2:0]  read_address,
  input  wire        read_en,
  output wire        read_data,
  output wire        read_rdy
);

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


