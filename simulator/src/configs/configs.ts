import { Net, Pip } from "../types";
import { CELL_WIDTH, CELL_HEIGHT, MATRIX_WIDTH, MATRIX_HEIGHT } from "./Routing";


export type ConfigTypes = "logic_cell" | "bus" | "switch_matrix";


export default function getConfig(device: ConfigTypes, idx: number): any {
    switch (device) {
        case "logic_cell":
            const config = logic_cell_config.find(config => config.idxs.includes(idx));
            return config ? {
                nets: config.nets.map(net => ({ ...net, points: net.points.map(p => ({ ...p })) })),
                pips: config.pips.map(pip => ({ ...pip, pos: { ...pip.pos } }))
            } : undefined;
        case "bus":
            return bus_config.find(config => config.idxs.includes(idx))?.nets
                .map(net => ({ ...net, points: net.points.map(p => ({ ...p })) }));
        case "switch_matrix": {
            const config = switch_matrix_config.find(config => config.idxs.includes(idx));
            return config?.matrices.map(matrix => ({
                nets: matrix?.nets.map(net => ({ ...net, points: net.points.map(p => ({ ...p })) })),
                pos: matrix?.pos ? { ...matrix.pos } : undefined
            }));
        }
        default:
            throw new Error(`Unknown device type: ${device}`);
    }

}

function range(start: number, end: number): number[] {
    return Array.from({ length: end - start + 1 }, (_, i) => i + start);
}

const logic_cell_config: { idxs: number[], nets: Net[], pips: Pip[] }[] = [
    {
        idxs: [range(9, 14), range(17, 22), range(25, 30), range(33, 38), range(41, 46), range(49, 54)].flat(),
        nets: [
            { id: "net_A", value: false, points: [{ x: 60, y: -CELL_HEIGHT / 2 }, { x: 60, y: -(CELL_HEIGHT / 2 + 160) }] },
            { id: "net_B", value: false, points: [{ x: -CELL_WIDTH / 2, y: -40 }, { x: -CELL_WIDTH / 2 - 240, y: -40 }] },
            { id: "net_C", value: false, points: [{ x: -CELL_WIDTH / 2, y: 20 }, { x: -CELL_WIDTH / 2 - 240, y: 20 }] },
            { id: "net_D", value: false, points: [{ x: 0, y: CELL_HEIGHT / 2 }, { x: 0, y: CELL_HEIGHT / 2 + 180 }] },
            { id: "net_E", value: false, points: [] },
            { id: "net_F", value: false, points: [] },
            { id: "net_G", value: false, points: [] },
            { id: "net_K", value: false, points: [{ x: -CELL_WIDTH / 2, y: 80 }, { x: -CELL_WIDTH / 2 - 80, y: 80 }] },
            { id: "net_Q", value: false, points: [] },
            { id: "net_R", value: false, points: [] },
            { id: "net_S", value: false, points: [] },
            { id: "net_X", value: false, points: [{ x: CELL_WIDTH / 2, y: 20 }, { x: CELL_WIDTH / 2 + 40, y: 20 }, { x: CELL_WIDTH / 2 + 40, y: -100 }, { x: CELL_WIDTH / 2 + 220, y: -100 }] },
            { id: "net_Y", value: false, points: [{ x: CELL_WIDTH / 2, y: 140 }, { x: CELL_WIDTH / 2 + 240, y: 140 }] },
            { id: "net_gnd", value: false, points: [] },
            { id: "net_m6_out", value: false, points: [] },
            { id: "net_m8_out", value: false, points: [] },
            { id: "net_m13_out", value: false, points: [] },
            { id: "net_m18_out", value: false, points: [] },
            { id: "net_m20_out", value: false, points: [] },
            { id: "net_m24_out", value: false, points: [] },
            { id: "net_clk_1_out", value: false, points: [] },
            { id: "net_clk_2_out", value: false, points: [] }
        ],
        pips: [
            { id: "pip_0", source: "NW_M0.net_2", destination: "net_A", enabled: false , pos: { x: 160, y: -160 }, bidirectional: false},
            { id: "pip_1", source: "NW_M0.net_3", destination: "net_A", enabled: false , pos: { x: 160, y: -140 }, bidirectional: false},
            { id: "pip_2", source: "NW_M1.net_2", destination: "net_A", enabled: false , pos: { x: 160, y: -120 }, bidirectional: false},
            { id: "pip_2", source: "NW_M1.net_3", destination: "net_A", enabled: false , pos: { x: 160, y: -100 }, bidirectional: false},
            { id: "pip_2", source: "W_M0.net_0", destination: "net_B", enabled: false , pos: { x: -240, y: 120 }, bidirectional: false},
            { id: "pip_2", source: "W_M0.net_1", destination: "net_B", enabled: false , pos: { x: -220, y: 120 }, bidirectional: false},
            { id: "pip_2", source: "W_M1.net_0", destination: "net_B", enabled: false , pos: { x: -200, y: 120 }, bidirectional: false},
            { id: "pip_2", source: "W_M1.net_1", destination: "net_B", enabled: false , pos: { x: -180, y: 120 }, bidirectional: false},
            { id: "pip_2", source: "W_M0.net_0", destination: "net_C", enabled: false , pos: { x: -240, y: 180 }, bidirectional: false},
            { id: "pip_2", source: "W_M0.net_1", destination: "net_C", enabled: false , pos: { x: -220, y: 180 }, bidirectional: false},
            { id: "pip_2", source: "W_M1.net_0", destination: "net_C", enabled: false , pos: { x: -200, y: 180 }, bidirectional: false},
            { id: "pip_2", source: "W_M1.net_1", destination: "net_C", enabled: false , pos: { x: -180, y: 180 }, bidirectional: false},
            { id: "pip_2", source: "W_M0.net_2", destination: "net_D", enabled: false , pos: { x: CELL_WIDTH / 2, y: CELL_HEIGHT + 80}, bidirectional: false},
            { id: "pip_2", source: "W_M0.net_3", destination: "net_D", enabled: false , pos: { x: CELL_WIDTH / 2, y: CELL_HEIGHT + 100}, bidirectional: false},
            { id: "pip_2", source: "W_M1.net_2", destination: "net_D", enabled: false , pos: { x: CELL_WIDTH / 2, y: CELL_HEIGHT + 120}, bidirectional: false},
            { id: "pip_2", source: "W_M1.net_3", destination: "net_D", enabled: false , pos: { x: CELL_WIDTH / 2, y: CELL_HEIGHT + 140}, bidirectional: false},
            { id: "pip_3", source: "net_X", destination: "T_M0.net_1", enabled: false , pos: { x: 300, y: 60 }, bidirectional: false},
            { id: "pip_3", source: "net_X", destination: "T_M1.net_1", enabled: false , pos: { x: 340, y: 60 }, bidirectional: false},
            { id: "pip_3", source: "net_Y", destination: "T_M0.net_0", enabled: false , pos: { x: 280, y: 300 }, bidirectional: false},
            { id: "pip_3", source: "net_Y", destination: "T_M1.net_0", enabled: false , pos: { x: 320, y: 300 }, bidirectional: false},
        ]
    }
]

const switch_matrix_config: { idxs: number[], matrices: { nets: Net[], pos: { x: number, y: number } }[] }[] = [
    {
        idxs: [range(0, 6), range(8, 14), range(16, 22), range(24, 30), range(32, 38), range(40, 46), range(48, 54)].flat(),
        matrices: [
            {
                pos: { x: CELL_WIDTH / 2 + 90, y: 250 },
                nets: [
                    { id: "net_0", value: false, points: [{ x: -10, y: -MATRIX_HEIGHT / 2 }, { x: -10, y: -MATRIX_HEIGHT / 2 - 520 }] },
                    { id: "net_1", value: false, points: [{ x: 10, y: -MATRIX_HEIGHT / 2 }, { x: 10, y: -MATRIX_HEIGHT / 2 - 520 }] },
                    { id: "net_2", value: false, points: [{ x: MATRIX_WIDTH / 2, y: -10 }, { x: MATRIX_WIDTH / 2 + 520, y: -10 }] },
                    { id: "net_3", value: false, points: [{ x: MATRIX_WIDTH / 2, y: 10 }, { x: MATRIX_WIDTH / 2 + 520, y: 10 }] }
                ]
            },
            {
                pos: { x: CELL_WIDTH / 2 + 90 + MATRIX_WIDTH, y: 250 + MATRIX_HEIGHT },
                nets: [
                    { id: "net_0", value: false, points: [{ x: -10, y: -MATRIX_HEIGHT / 2 }, { x: -10, y: -MATRIX_HEIGHT / 2 - 520 }] },
                    { id: "net_1", value: false, points: [{ x: 10, y: -MATRIX_HEIGHT / 2 }, { x: 10, y: -MATRIX_HEIGHT / 2 - 520 }] },
                    { id: "net_2", value: false, points: [{ x: MATRIX_WIDTH / 2, y: -10 }, { x: MATRIX_WIDTH / 2 + 520, y: -10 }] },
                    { id: "net_3", value: false, points: [{ x: MATRIX_WIDTH / 2, y: 10 }, { x: MATRIX_WIDTH / 2 + 520, y: 10 }] }
                ]
            }
        ]

    }
]

const bus_config: { idxs: number[], nets: Net[] }[] = [
    // TODO: define bus configurations
]





