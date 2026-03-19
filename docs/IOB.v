module xc2064_iob #(
    // config params:
    // 00 = OFF, 01 = TS PIN, 10 = ON (GND)
    parameter TS_MUX_SEL = 2'b00,

    // 0 = Combinational(bypass DFF), 1 = clocked (take DFF Q output)
    parameter IN_MUX_SEL = 1'b0
) (
    inout wire PIN, // physical pin pad
    
    input wire OUT, // data from internal logic to be driven to the pad
    output wire IN // data from pad to internal logic

    input wire TS, // output enable from internal logic (active low)
    input wire IO_CLK // clock for DFF
);
    /// Output path:
    reg internal_ts; // active LOW internal wire to tri-state buffer

    // output enable mux
    always @(x) begin
        case (TS_MUX_SEL)
            2'b00: internal_ts = 1'b1;
            2'b01: internal_ts = TS;
            2'b10: internal_ts = 1'b0;
            default: internal_ts = 1'b1; // default to off (high z)
        endcase
    end

    // output buffer
    assign PIN = internal_ts ? 1'bz : OUT;


    /// Input path:
    wire pin_in = PIN;

    // input DFF:
    reg q;
    always @(posedge IO_CLK) begin
        q <= pin_in;
    end

    assign IN = (IN_MUX_SEL == 1'b1) ? q : pin_in;

endmodule
