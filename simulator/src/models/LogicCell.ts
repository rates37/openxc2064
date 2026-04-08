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
        {id: "m46", select: 2},
        {id: "m51", select: 0},
        {id: "m56", select: 2},
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

    /**
     * Tracks if any of the LUTs in the CLB are always true
     */
    public isConstant(): boolean {
        // LUT 0
        const lut0 = this.luts[0].truthTable.every(output => output === true);

        // LUT 1
        const lut1 = this.luts[1].truthTable.every(output => output === true);

        return lut0 || lut1;
    }

    private getNet(id: string): boolean {
        return this.nets.find(n => n.id === id)?.value ?? false;
    }

    private setNet(id: string, value: boolean): void {
        const net = this.nets.find(n => n.id === id);
        if (net) net.value = value;
    }

    private getMux(id: string): number {
        return this.muxes.find(m => m.id === id)?.select ?? 0;
    }

    public simulate(): void {
        let prev_nets: { [key: string]: boolean } = {};
        do {
            // Save the previous state to allow for propagation
            prev_nets = { ...this.nets.reduce((acc, net) => ({ ...acc, [net.id]: net.value }), {}) };
            
            // Save previous clock state for edge detection
            const prevClk = this.getNet("net_clk_2_out");
            
            // --- LUT1 Input Muxes ---
            // M6 (2-input): 0=A, 1=B
            this.setNet("net_m6_out", this.getMux("m6") === 0 ? this.getNet("net_A") : this.getNet("net_B"));
            
            // M8 (2-input): 0=B, 1=C
            this.setNet("net_m8_out", this.getMux("m8") === 0 ? this.getNet("net_B") : this.getNet("net_C"));
            
            // M13 (3-input): 0=C, 1=D, 2=Q
            const m13sel = this.getMux("m13");
            this.setNet("net_m13_out", m13sel === 0 ? this.getNet("net_C") : m13sel === 1 ? this.getNet("net_D") : this.getNet("net_Q"));
            
            // --- LUT2 Input Muxes ---
            // M18 (2-input): 0=A, 1=B
            this.setNet("net_m18_out", this.getMux("m18") === 0 ? this.getNet("net_A") : this.getNet("net_B"));
            
            // M20 (2-input): 0=B, 1=C
            this.setNet("net_m20_out", this.getMux("m20") === 0 ? this.getNet("net_B") : this.getNet("net_C"));
            
            // M24 (3-input): 0=C, 1=D, 2=Q
            const m24sel = this.getMux("m24");
            this.setNet("net_m24_out", m24sel === 0 ? this.getNet("net_C") : m24sel === 1 ? this.getNet("net_D") : this.getNet("net_Q"));
            
            // --- LUT Evaluation ---
            // LUT 1 -> net_G
            const l1i2 = this.getNet("net_m6_out") ? 1 : 0;
            const l1i1 = this.getNet("net_m8_out") ? 1 : 0;
            const l1i0 = this.getNet("net_m13_out") ? 1 : 0;
            const lut1Index = (l1i2 << 2) | (l1i1 << 1) | l1i0;
            this.setNet("net_G", this.luts[0].truthTable[lut1Index]);
            
            // LUT 2 -> net_F
            const l2i2 = this.getNet("net_m18_out") ? 1 : 0;
            const l2i1 = this.getNet("net_m20_out") ? 1 : 0;
            const l2i0 = this.getNet("net_m24_out") ? 1 : 0;
            const lut2Index = (l2i2 << 2) | (l2i1 << 1) | l2i0;
            this.setNet("net_F", this.luts[1].truthTable[lut2Index]);
            
            // --- Clock Muxes ---
            // M51 (3-input): 0=G, 1=C, 2=K -> clk_1_out
            const m51sel = this.getMux("m51");
            this.setNet("net_clk_1_out", m51sel === 0 ? this.getNet("net_G") : m51sel === 1 ? this.getNet("net_C") : this.getNet("net_K"));
            
            // M100 (3-input): 0=~clk_1_out, 1=clk_1_out, 2=GND -> clk_2_out
            const m100sel = this.getMux("m100");
            const clk1 = this.getNet("net_clk_1_out");
            this.setNet("net_clk_2_out", m100sel === 0 ? !clk1 : m100sel === 1 ? clk1 : false);
            
            // --- FF Set/Reset Muxes ---
            // M56 (3-input): 0=A, 1=F, 2=GND -> net_S (FF set)
            const m56sel = this.getMux("m56");
            this.setNet("net_S", m56sel === 0 ? this.getNet("net_A") : m56sel === 1 ? this.getNet("net_F") : false);
            
            // M46 (3-input): 0=G, 1=D, 2=GND -> net_R (FF reset)
            const m46sel = this.getMux("m46");
            this.setNet("net_R", m46sel === 0 ? this.getNet("net_G") : m46sel === 1 ? this.getNet("net_D") : false);
            
            // --- D Flip-Flop ---
            const clk = this.getNet("net_clk_2_out");
            const risingEdge = clk && !prevClk;
            
            if (this.getNet("net_R")) {
                this.setNet("net_Q", false);
            } else if (this.getNet("net_S")) {
                this.setNet("net_Q", true);
            } else if (risingEdge) {
                this.setNet("net_Q", this.getNet("net_F"));
            }
            
            // --- Output Muxes ---
            // M59 (3-input): 0=G, 1=Q, 2=F -> net_X
            const m59sel = this.getMux("m59");
            this.setNet("net_X", m59sel === 0 ? this.getNet("net_G") : m59sel === 1 ? this.getNet("net_Q") : this.getNet("net_F"));
            
            // M61 (3-input): 0=G, 1=Q, 2=F -> net_Y
            const m61sel = this.getMux("m61");
            this.setNet("net_Y", m61sel === 0 ? this.getNet("net_G") : m61sel === 1 ? this.getNet("net_Q") : this.getNet("net_F"));
        
        } while (JSON.stringify(this.nets.reduce((acc, net) => ({ ...acc, [net.id]: net.value }), {})) !== JSON.stringify(prev_nets));

    }


}