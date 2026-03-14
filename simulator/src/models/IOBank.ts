import { Net, Mux, LUT } from "../types";

export class IOBank {
    id: string;

    nets: Net[] = [];

    pos = { x: 0, y: 0 };
    size = { width: 100, height: 50 };

    constructor(id: string, pos: { x: number, y: number }, size: { width: number, height: number }) {
        this.id = id;
        this.pos = pos;
        this.size = size;
    }

    public reset(): void {
        this.nets.forEach(net => net.value = false);
    }

    public simulate(): void {
        console.log(`Unimplemented simulate() for IOBank ${this.id}`);
    }


}