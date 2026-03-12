import { Net, Mux, LUT } from "../types";

export class IOBank {
    id: string;

    nets: Net[] = [];

    pos = { x: 0, y: 0 };

    constructor(id: string, pos: { x: number, y: number }) {
        this.id = id;
        this.pos = pos;
    }

    public reset(): void {
        this.nets.forEach(net => net.value = false);
    }

    public simulate(): void {
        console.log(`Unimplemented simulate() for IOBank ${this.id}`);
    }


}