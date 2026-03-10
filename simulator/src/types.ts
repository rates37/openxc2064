export interface Net {
    id: string,
    value: boolean,
    points: {x: number, y: number, continuous?: boolean}[],
    
}

export interface Mux {
    id: string,
    select: number
}


export interface LUT {
    id: string,
    truthTable: boolean[]
}

export interface Pip {
    id: string,
    bidirectional: boolean,
    source: string,
    destination: string,
    enabled: boolean,
    pos: {x: number, y: number}
}

export type NetResolver = (globalNetId: string) => Net | undefined;