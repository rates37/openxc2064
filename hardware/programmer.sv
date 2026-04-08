module programmer(
    // XC2064 CCLK input
    input clk,

    // Active low reset
    input rst_n,

    // Chip HDC and ~LDC Signals (not sure why it is ~LDC, instead of LDC)
    input chip_hdc,
    input chip_ldc,

    // Chips M0, M1 and M2 pins
    output [2:0] mode,

    // DONE / ~PROG
    input chip_done,

    // ~RESET
    output chip_rst_n

    // Chip progamming data/addr
    output [7:0] chip_din,
    input [15:0] chip_addr,


    // Rom programming data/addr
    input [7:0] rom_data,
    output [15:0] rom_addr,
);


    assign rom_addr = chip_addr;
    assign chip_din = rom_data;



    always @(posedge clk or negedge rst_n) begin
        if (rst_n == 0) chip_rst_n <= 0;



    end



endmodule
