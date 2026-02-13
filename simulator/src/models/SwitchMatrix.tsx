import React from "react";
import { SimulatorContextType } from "../context/SimulatorContext";


export class SwitchMatrix {
    id: string;

    x: number;
    y: number;

    connections: (0 | 1)[][] = [[0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0]];

    possibleConnections: (0 | 1)[][] = [[0, 0, 1, 0, 1, 1, 1, 1],
    [0, 0, 1, 1, 1, 1, 0, 1],
    [1, 1, 0, 0, 1, 0, 1, 1],
    [0, 1, 0, 0, 1, 1, 1, 1],
    [1, 1, 1, 1, 0, 0, 1, 0],
    [1, 1, 0, 1, 0, 0, 1, 1],
    [1, 0, 1, 1, 1, 1, 0, 0],
    [1, 1, 1, 1, 0, 1, 0, 0]];

    points: { key: string, x: number, y: number }[] = [
        { key: "1", x: 2, y: -4 },
        { key: "2", x: 12, y: -4 },
        { key: "3", x: 19, y: 2 },
        { key: "4", x: 19, y: 12 },
        { key: "5", x: 12, y: 19 },
        { key: "6", x: 2, y: 19 },
        { key: "7", x: -4, y: 12 },
        { key: "8", x: -4, y: 2 },
    ];

    nets: { [key: string]: string } = {
        "net_1": "",
        "net_2": "",
        "net_3": "",
        "net_4": "",
        "net_5": "",
        "net_6": "",
        "net_7": "",
        "net_8": "",
    };

    constructor(id?: string, downSwitch?: string, leftSwitch?: string) {
        this.id = id || "";
    }

    public initializeNets(context: SimulatorContextType, downSwitch?: string, leftSwitch?: string) {
        const idx = parseInt(this.id.charAt(this.id.length - 1));

        context.setNet(this.id + "_" + "net_1", 0);
        context.setNet(this.id + "_" + "net_2", 0);
        context.setNet(this.id + "_" + "net_3", 0);
        context.setNet(this.id + "_" + "net_4", 0);

        if (downSwitch) {
            context.setNet(downSwitch + idx + "_" + "net_2", 0);
            context.setNet(downSwitch + idx + "_" + "net_1", 0);
        }

        if (leftSwitch) {
            context.setNet(leftSwitch + idx + "_" + "net_4", 0);
            context.setNet(leftSwitch + idx + "_" + "net_3", 0);
        }

        this.nets["net_1"] = this.id + "_" + "net_1";
        this.nets["net_2"] = this.id + "_" + "net_2";
        this.nets["net_3"] = this.id + "_" + "net_3";
        this.nets["net_4"] = this.id + "_" + "net_4";

        this.nets["net_5"] = downSwitch ? downSwitch + idx + "_" + "net_1" : "";
        this.nets["net_6"] = downSwitch ? downSwitch + idx + "_" + "net_2" : "";
        this.nets["net_7"] = leftSwitch ? leftSwitch + idx + "_" + "net_3" : "";
        this.nets["net_8"] = leftSwitch ? leftSwitch + idx + "_" + "net_4" : "";
    }


    public updateConnections(newConnections: (0 | 1)[][]) {
        // Validate the new connections matrix
        if (newConnections.length !== 8 || newConnections[0].length !== 8) {
            throw new Error("Invalid connections matrix. Must be 8x8.");
        }

        const changes: { row: number; col: number; value: 0 | 1 }[] = [];

        // Set all mirror connections to 1
        for (let i = 0; i < 8; i++) {
            for (let j = 0; j < 8; j++) {
                if (newConnections[i][j] !== this.connections[i][j]) {
                    changes.push({ row: i, col: j, value: newConnections[i][j] });
                }
            }
        }

        // Set all mirror connections to 1
        for (let i = 0; i < changes.length; i++) {
            const { row, col, value } = changes[i];

            newConnections[col][row] = value; // Mirror connection
        }


        this.connections = newConnections;
    }

    public simulate(context: SimulatorContextType): void {
        // Update nets based on connections
        for (let i = 0; i < 8; i++) {
            const netId = this.nets[`net_${i + 1}`];
            if (!netId) continue;
            
            // context.setNet(netId, 0); // Reset net
            for (let j = 0; j < 8; j++) {
                // console.log(this.nets);
                if (this.connections[i][j] === 1) {
                    const connectedNetId = this.nets[`net_${j + 1}`];
                    if (connectedNetId) {
                        
                        const val = context.getNet(connectedNetId);
                        console.log(`SwitchMatrix ${this.id} connecting net ${netId} to net ${connectedNetId} with value ${val}`);
                        if (val !== undefined) {
                            context.setNet(netId, val);
                        }
                    }
                }
            }
        }
    }

}