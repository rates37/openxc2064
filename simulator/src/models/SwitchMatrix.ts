import { Net, Mux, LUT } from "../types";

export class SwitchMatrix {
    id: string;

    nets: (Net | null)[] = [null, null, null, null, null, null, null, null];

    possibleConnections: number[][] = [
        [0, 0, 1, 0, 1, 1, 1, 1],
        [0, 0, 1, 1, 1, 1, 0, 1],
        [1, 1, 0, 0, 1, 0, 1, 1],
        [0, 1, 0, 0, 1, 1, 1, 1],
        [1, 1, 1, 1, 0, 0, 1, 0],
        [1, 1, 0, 1, 0, 0, 1, 1],
        [1, 0, 1, 1, 1, 1, 0, 0],
        [1, 1, 1, 1, 0, 1, 0, 0]
    ]

    connections: number[][] = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0]

    ];

    pos = { x: 0, y: 0 };

    constructor(id: string, pos: { x: number, y: number }) {
        this.id = id;
        this.pos = pos;
    }

    public reset(): void {
        this.connections = this.connections.map(row => row.map(() => 0));
    }

    public simulate(): void {
        this.connections.map ((row, i) => row.map((connected, j) => {
            if (connected) {
                if (this.nets[i] && this.nets[j]) {
                    this.nets[j]!.value = this.nets[i]!.value;
                }
            }
        }));
    }


}