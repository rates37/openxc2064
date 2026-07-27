import React from 'react';
import { LogicCell } from './models/LogicCell';
import { SwitchMatrix } from './models/SwitchMatrix';
import { IOBank } from './models/IOBank';
import { Pip } from './types';

/**
 * Export the current simulation state to a JSON file
 */
export const createExportStateFunction = (
	logicCells: LogicCell[],
	switchMatrices: SwitchMatrix[],
	pips: Pip[],
	ioBanks: IOBank[],
	drivers: { source: string; destination: string }[]
) => {
	return () => {
		const state = {
			logicCells: logicCells.map((cell) => ({
				id: cell.id,
				muxes: cell.muxes.map((m) => ({ id: m.id, select: m.select })),
				luts: cell.luts.map((l) => ({ id: l.id, truthTable: [...l.truthTable] })),
			})),
			switchMatrices: switchMatrices.map((matrix) => ({
				id: matrix.id,
				connections: matrix.connections.map((row) => [...row]),
				pos: matrix.pos,
			})),
			pips: pips.map((pip) => ({
				id: pip.id,
				source: pip.source,
				destination: pip.destination,
				enabled: pip.enabled,
				pos: pip.pos,
			})),
			ioBanks: ioBanks.map((bank) => ({
				id: bank.id,
				muxes: bank.muxes.map((m) => ({ id: m.id, select: m.select })),
			})),
			drivers: drivers,
		};
		const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = 'xc2064-config.json';
		a.click();
		URL.revokeObjectURL(url);
	};
};

/**
 * Import a previously exported simulation state from a JSON file
 */
export const createImportStateFunction = (
	logicCells: LogicCell[],
	switchMatrices: SwitchMatrix[],
	ioBanks: IOBank[],
	setPips: React.Dispatch<React.SetStateAction<Pip[]>>,
	setDrivers: React.Dispatch<React.SetStateAction<{ source: string; destination: string }[]>>,
	bumpTick: () => void
) => {
	return () => {
		const input = document.createElement('input');
		input.type = 'file';
		input.accept = '.json';
		input.onchange = () => {
			const file = input.files?.[0];
			if (!file) return;
			const reader = new FileReader();
			reader.onload = () => {
				try {
					const state = JSON.parse(reader.result as string);
					// Clear all state first
					setPips((prev) => prev.map((p) => ({ ...p, enabled: false })));
					setDrivers([]);
					if (state.logicCells) {
						for (const saved of state.logicCells) {
							const cell = logicCells.find((c) => c.id === saved.id);
							if (!cell) continue;
							if (saved.muxes) {
								for (const sm of saved.muxes) {
									const mux = cell.muxes.find((m) => m.id === sm.id);
									if (mux) mux.select = sm.select;
								}
							}
							if (saved.luts) {
								for (const sl of saved.luts) {
									const lut = cell.luts.find((l) => l.id === sl.id);
									if (lut && Array.isArray(sl.truthTable)) {
										lut.truthTable = sl.truthTable;
									}
								}
							}
						}
					}
					if (state.switchMatrices) {
						for (const saved of state.switchMatrices) {
							const matrix = switchMatrices.find((m) => m.id === saved.id);
							if (matrix && saved.connections) {
								matrix.connections = saved.connections;
							}
						}
					}
					if (state.pips) {
						setPips((prev) =>
							prev.map((pip) => {
								const saved = state.pips.find((s: any) => s.source === pip.source && s.destination === pip.destination);
								return saved ? { ...pip, enabled: saved.enabled } : pip;
							}),
						);
					}
					if (state.ioBanks) {
						for (const saved of state.ioBanks) {
							const bank = ioBanks.find((b) => b.id === saved.id);
							if (bank && saved.muxes) {
								for (const sm of saved.muxes) {
									const mux = bank.muxes.find((m) => m.id === sm.id);
									if (mux) mux.select = sm.select;
								}
							}
						}
					}
					if (state.drivers && Array.isArray(state.drivers)) {
						setDrivers(state.drivers);
					}
					bumpTick();
				} catch (e) {
					console.error('Failed to import state:', e);
				}
			};
			reader.readAsText(file);
		};
		input.click();
	};
};
