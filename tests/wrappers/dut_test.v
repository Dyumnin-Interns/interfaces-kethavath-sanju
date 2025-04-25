module dut_test(
      input  CLK,
  input  RST_N,

  // action method write
  input  [2 : 0] write_address,
  input  write_data,
  input  write_en,
  output write_rdy,

  // actionvalue method read
  input  [2 : 0] read_address,
  input  read_en,
  output read_data,
  output read_rdy
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




/*
module dut_test;

    // Clock and reset
    reg CLK;
    reg RST_N;
    
    // Read Interface
    reg [2:0] read_address;
    wire read_data;
    wire read_rdy;
    reg read_en;
    
    // Write Interface
    wire write_rdy;
    reg [2:0] write_address;
    reg write_data;
    reg write_en;
    
    // Instantiate DUT
    dut dut_inst (
        .CLK(CLK),
        .RST_N(RST_N),
        
        // Write Interface
        .write_address(write_address),
        .write_data(write_data),
        .write_en(write_en),
        .write_rdy(write_rdy),
        
        // Read Interface
        .read_address(read_address),
        .read_en(read_en),
        .read_data(read_data),
        .read_rdy(read_rdy)
    );
    
    // Clock generation
    initial begin
        CLK = 0;
        forever #5 CLK = ~CLK;
    end
    
    // Reset generation
    initial begin
        RST_N = 0;
        #20 RST_N = 1;
    end
    
    // Test stimulus
    initial begin
        // Initialize inputs
        read_address = 0;
        read_en = 0;
        write_address = 0;
        write_data = 0;
        write_en = 0;
        
        // Wait for reset to complete
        #30;
        
        // Test FIFO status registers
        read_address = 0; // A_Status
        read_en = 1;
        #10;
       // $display("A_Status: %b", read_data);
        
        read_address = 1; // B_Status
        #10;
       // $display("B_Status: %b", read_data);
        
        read_address = 2; // Y_Status
        #10;
        //$display("Y_Status: %b", read_data);
        
        read_en = 0;
        
        // Write to A and B FIFOs
        write_address = 4; // A_Data
        write_data = 1;
        write_en = 1;
        #10;
        write_en = 0;
        
        write_address = 5; // B_Data
        write_data = 0;
        write_en = 1;
        #10;
        write_en = 0;
        
        // Check Y output
        #20;
        read_address = 3; // y_output
        read_en = 1;
        #10;
       // $display("Y output: %b", read_data);
        read_en = 0;
        
        // End simulation
        #100;
        $finish;
    end
    
endmodule  */