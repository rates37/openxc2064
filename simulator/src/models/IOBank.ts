import { Net, Mux, LUT } from '../types';

export class IOBank {
	id: string;
    index: number = 0;

	nets: Net[] = [];

	muxes: Mux[] = [
		{ id: `mts`, select: 0 },
		{ id: `min`, select: 0 },
	];

	pos = { x: 0, y: 0 };
	size = { width: 100, height: 50 };

	pad: IOPad | null = null;

	constructor(id: string, pos: { x: number; y: number }, size: { width: number; height: number }) {
		this.id = id;
		this.pos = pos;
		this.size = size;
		
	}

	public reset(): void {
		this.nets.forEach((net) => (net.value = false));
	}

	private getNet(id: string): boolean {
        const netId = `${this.id}.${id}`;
		return this.nets.find((n) => netId === n.id)?.value ?? false;
	}

	private setNet(id: string, value: boolean): void {
        const netId = `${this.id}.${id}`;
		const net = this.nets.find((n) => n.id === netId);
		if (net) net.value = value;
	}

	private getMux(id: string): number {
		return this.muxes.find((m) => m.id === id)?.select ?? 0;
	}

	public simulate(): void {
		let prev_nets: { [key: string]: boolean } = {};
		do {
			// Save the previous state to allow for propagation
			prev_nets = { ...this.nets.reduce((acc, net) => ({ ...acc, [net.id]: net.value }), {}) };

			// Save previous clock state for edge detection
			const prevClk = this.getNet('net_io_clk');

            // Tristate mux selects which output source drives the pad
            // Case 0: always enabled, Case 1: enabled if net_T is high, Case 2: always disabled
            this.setNet("net_ts_mux", this.getMux("mts") === 0 ? true : this.getMux("mts") === 1 ? this.getNet("net_T") : false);

            // If tristate buffer is enabled, it drives the pad with the output value
            // If disabled, the pad value is kept as-is (allowing user toggles or input to persist)
            if (!this.getNet("net_ts_mux")) { 
                this.setNet("net_pad", this.getNet("net_O"));
            }

            // Rising edge detection for input register
            if (prevClk === false && this.getNet("net_io_clk") === true) {
                // Rising edge detected, sample input
                this.setNet("net_in_q", this.getNet("net_pad"));
            }

            // Input mux selects between pad and registered input
            this.setNet("net_I", this.getMux("min") === 0 ? this.getNet("net_pad") : this.getNet("net_in_q"));

		} while (JSON.stringify(this.nets.reduce((acc, net) => ({ ...acc, [net.id]: net.value }), {})) !== JSON.stringify(prev_nets));
	}
}

export class IOPad {
	pos = { x: 0, y: 0 };
	size = { width: 20, height: 20 };

	constructor(pos: { x: number; y: number }, size: { width: number; height: number }) {
		this.pos = pos;
		this.size = size;
	}
}
