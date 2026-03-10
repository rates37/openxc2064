import { Net, Mux, LUT } from "../types";

export class LogicCell {
    id: string;
    pos: { x: number; y: number } = { x: 0, y: 0 };

    nets: Net[] = [];

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

    constructor(id: string, config?: {nets?: Net[], muxes?: Mux[], luts?: LUT[], pos?: {x: number, y: number}}) {
        this.id = id;
        if (!config) return;

        if (config.pos) {
            this.pos = { ...config.pos };
        }
        if (config.nets) {
            this.nets = [...config.nets];
        }
        if (config.muxes) {
            this.muxes = [...config.muxes];
        }
        if (config.luts) {
            this.luts = [...config.luts];
        }
    }

    public reset(): void {
        this.nets.forEach(net => net.value = false);
        this.muxes.forEach(mux => mux.select = 0);
        this.luts.forEach(lut => lut.truthTable.fill(false));
    }

    public simulate(): void {
        this.nets.forEach(net => {
            // For demonstration, toggle the value of each net.
            if (net.id === "net_X" || net.id === "net_Y") net.value = !net.value;
        });
    }


}