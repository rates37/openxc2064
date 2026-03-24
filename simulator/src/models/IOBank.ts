import { Net, Mux, LUT } from "../types";

export class IOBank {
    id: string;

    nets: Net[] = [];

    pos = { x: 0, y: 0 };
    size = { width: 100, height: 50 };

    pad: IOPad | null = null;

    used = false;

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


export class IOPad {
    pos = { x: 0, y: 0 };
    size = { width: 20, height: 20 };

    constructor(pos: { x: number, y: number }, size: { width: number, height: number }) {
        this.pos = pos;
        this.size = size;
    }
}