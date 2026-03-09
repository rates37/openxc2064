import { Net, Mux, LUT } from "../types";

export class LogicCell {
    id: string;

    nets: Net[] = [
        {id: "net_A", value: false},
        {id: "net_B", value: false},
        {id: "net_C", value: false},
        {id: "net_D", value: false},
        {id: "net_E", value: false},
        {id: "net_F", value: false},
        {id: "net_G", value: false},
        {id: "net_K", value: false},
        {id: "net_Q", value: false},
        {id: "net_R", value: false},
        {id: "net_S", value: false},
        {id: "net_X", value: false},
        {id: "net_Y", value: false},
        {id: "net_gnd", value: false},
        {id: "net_m6_out", value: false},
        {id: "net_m8_out", value: false},
        {id: "net_m13_out", value: false},
        {id: "net_m18_out", value: false},
        {id: "net_m20_out", value: false},
        {id: "net_m24_out", value: false},
        {id: "net_clk_1_out", value: false},
        {id: "net_clk_2_out", value: false}
    ];

    muxes: Mux[] = [
        {id: "m6", select: 0},
        {id: "m8", select: 0},
        {id: "m13", select: 0},
        {id: "m18", select: 0},
        {id: "m20", select: 0},
        {id: "m24", select: 0},
        {id: "m46", select: 0},
        {id: "m51", select: 0},
        {id: "m56", select: 0},
        {id: "m59", select: 0},
        {id: "m61", select: 0},
        {id: "m100", select: 0}
    ];

    luts: LUT[] = [
        {id: "lut_0", truthTable: [false, false, false, false, false, false, false, false]},
        {id: "lut_1", truthTable: [false, false, false, false, false, false, false, false]},
    ];

    constructor(id: string) {
        this.id = id;
    }

    public reset(): void {
        this.nets.forEach(net => net.value = false);
        this.muxes.forEach(mux => mux.select = 0);
        this.luts.forEach(lut => lut.truthTable.fill(false));
    }

    public simulate(): void {
        console.log(`Simulating logic cell [${this.id}]...`);
    }


}