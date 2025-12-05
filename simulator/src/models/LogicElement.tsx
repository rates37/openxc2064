
export class LogicElement {
    id: string;

    muxConfig: { [key: string]: number } = {
        "m6": 0,
        "m8": 0,
        "m13": 0,
        "m18": 0,
        "m20": 0,
        "m24": 0,
        "m46": 0,
        "m51": 0,
        "m56": 0,
        "m59": 0,
        "m61": 0,
        "m100": 0,
    };

    lutConfig: { [key: string]: number[] } = {
        "LUT 1": [0, 0, 0, 0, 0, 0, 0, 0],
        "LUT 2": [0, 0, 0, 0, 0, 0, 0, 0],
    };

    inputs: { [key: string]: 0 | 1 } = {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
        "K": 0,
    };

    outputs: { [key: string]: 0 | 1 } = {
        "X": 0,
        "Y": 0,
    };

    nets: { [key: string]: 0 | 1 } = {
        "net_A": 0,
        "net_B": 0,
        "net_C": 0,
        "net_D": 0,
        "net_F": 0,
        "net_G": 0,
        "net_K": 0,
        "net_Q": 0,
        "net_R": 0,
        "net_S": 0,
        "net_X": 0,
        "net_Y": 0,
        "net_GND": 0,
        "net_m6_out": 0,
        "net_m8_out": 0,
        "net_m13_out": 0,
        "net_m18_out": 0,
        "net_m20_out": 0,
        "net_m24_out": 0,
        "clk_net": 0,
        "clk_net2": 0,
    };



    public simulate(): void {
        let prev_nets = { ...this.nets };
        let prev_clk_net2 = this.nets["clk_net2"];

        this.nets["net_A"] = this.inputs["A"];
        this.nets["net_B"] = this.inputs["B"];
        this.nets["net_C"] = this.inputs["C"];
        this.nets["net_D"] = this.inputs["D"];
        this.nets["net_K"] = this.inputs["K"];
    
        do {
            prev_nets = { ...this.nets };
            prev_clk_net2 = this.nets["clk_net2"];

            // LUT 1
            const L1I2 = this.nets["net_m6_out"];
            const L1I1 = this.nets["net_m8_out"];
            const L1I0 = this.nets["net_m13_out"];
            const lut1Index = (L1I2 << 2) | (L1I1 << 1) | L1I0;
            this.nets["net_G"] = this.lutConfig["LUT 1"][lut1Index] ? 1 : 0;


            // LUT 2
            const L2I2 = this.nets["net_m18_out"];
            const L2I1 = this.nets["net_m20_out"];
            const L2I0 = this.nets["net_m24_out"];
            const lut2Index = (L2I2 << 2) | (L2I1 << 1) | L2I0;
            this.nets["net_F"] = this.lutConfig["LUT 2"][lut2Index] ? 1 : 0;

            // Mux M6
            this.nets["net_m6_out"] = this.muxConfig["m6"] === 0 ? this.nets["net_A"] : this.nets["net_B"];

            // Mux M8
            this.nets["net_m8_out"] = this.muxConfig["m8"] === 0 ? this.nets["net_B"] : this.nets["net_C"];

            // Mux M13
            this.nets["net_m13_out"] = this.muxConfig["m13"] === 0 ? this.nets["net_C"] : this.muxConfig["m13"] === 1 ? this.nets["net_D"] : this.nets["net_Q"];

            // Mux M18
            this.nets["net_m18_out"] = this.muxConfig["m18"] === 0 ? this.nets["net_A"] : this.nets["net_B"];

            // Mux M20
            this.nets["net_m20_out"] = this.muxConfig["m20"] === 0 ? this.nets["net_B"] : this.nets["net_C"];

            // Mux M24
            this.nets["net_m24_out"] = this.muxConfig["m24"] === 0 ? this.nets["net_C"] : this.muxConfig["m24"] === 1 ? this.nets["net_D"] : this.nets["net_R"];

            // First clock mux
            this.nets["clk_net"] = this.muxConfig["m51"] === 0 ? this.nets["net_G"] : this.muxConfig["m51"] === 1 ? this.nets["net_C"] : this.nets["net_K"];

            // Second clock mux
            this.nets["clk_net2"] = this.muxConfig["m100"] === 0 ? this.nets["clk_net"] ? 0 : 1 : this.muxConfig["m100"] === 1 ? this.nets["clk_net"] : 0; 

            // Mux M56
            this.nets["net_S"] = this.muxConfig["m56"] === 0 ? this.nets["net_A"] : this.muxConfig["m56"] === 1 ? this.nets["net_F"] : 0;

            // Mux M46
            this.nets["net_R"] = this.muxConfig["m46"] === 0 ? this.nets["net_G"] : this.muxConfig["m46"] === 1 ? this.nets["net_D"] : 0;

            // Mux M59
            this.nets["net_X"] = this.muxConfig["m59"] === 0 ? this.nets["net_G"] : this.muxConfig["m59"] === 1 ? this.nets["net_Q"] : this.nets["net_F"];
            this.outputs["X"] = this.nets["net_X"];

            // Mux M59
            this.nets["net_Y"] = this.muxConfig["m61"] === 0 ? this.nets["net_G"] : this.muxConfig["m61"] === 1 ? this.nets["net_Q"] : this.nets["net_F"];
            this.outputs["Y"] = this.nets["net_Y"];

            // D Flip-Flop
            if (this.nets["clk_net2"] === 1 && prev_clk_net2 === 0) {
                this.nets["net_Q"] = this.nets["net_F"];
            }

            if (this.nets["net_S"] === 1) {
                this.nets["net_Q"] = 1;
            }

            if (this.nets["net_R"] === 1) {
                this.nets["net_Q"] = 0;
            }

            console.log(".");

        } while (JSON.stringify(prev_nets) !== JSON.stringify(this.nets));
    } 
}