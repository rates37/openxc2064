import React, { useState, useCallback } from 'react';
import '../styles/Modal.css';
import { useSimulator } from '../SimulatorContext';

interface OscillatorModalProps {
	isOpen: boolean;
	onClose: () => void;
}

const OscillatorModal: React.FC<OscillatorModalProps> = ({ isOpen, onClose }) => {
	const { oscillator, setOscillator, simulate } = useSimulator();
	const [localFrequency, setLocalFrequency] = useState(oscillator.frequency);

	// Handle toggling oscillator on/off
	const handleToggle = useCallback(() => {
		const newState = { ...oscillator, enabled: !oscillator.enabled };
		setOscillator(newState);
		simulate();
	}, [oscillator, setOscillator, simulate]);

	// Handle frequency change
	const handleFrequencyChange = useCallback(
		(e: React.ChangeEvent<HTMLInputElement>) => {
			const value = parseFloat(e.target.value);
			if (!isNaN(value) && value >= 0 && value <= 10) {
				setLocalFrequency(value);
				setOscillator({ ...oscillator, frequency: value });
				simulate();
			}
		},
		[oscillator, setOscillator, simulate]
	);

	// Handle slider change
	const handleSliderChange = useCallback(
		(e: React.ChangeEvent<HTMLInputElement>) => {
			const value = parseFloat(e.target.value);
			setLocalFrequency(value);
			setOscillator({ ...oscillator, frequency: value });
			simulate();
		},
		[oscillator, setOscillator, simulate]
	);

	if (!isOpen) return null;

	return (
		<div className="modal-overlay" onClick={onClose}>
			<div className="modal-content" onClick={(e) => e.stopPropagation()}>
				<div className="modal-header">
					<h2>Oscillator Control</h2>
					<button className="modal-close-btn" onClick={onClose}>
						&times;
					</button>
				</div>
				<div className="modal-body" style={{ padding: '24px', minWidth: '400px' }}>
					{/* Enable/Disable Toggle */}
					<div style={{ marginBottom: '24px' }}>
						<label style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer', fontSize: '16px' }}>
							<input
								type="checkbox"
								checked={oscillator.enabled}
								onChange={handleToggle}
								style={{ width: '20px', height: '20px', cursor: 'pointer' }}
							/>
							<span style={{ fontWeight: 'bold' }}>
								Oscillator {oscillator.enabled ? 'ON' : 'OFF'}
							</span>
						</label>
						<p style={{ margin: '8px 0 0 0', fontSize: '13px', color: '#666' }}>
							When enabled, drives the global.net_osc_in net with a square wave
						</p>
					</div>

					{/* Frequency Control */}
					<div style={{ marginBottom: '24px' }}>
						<label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', fontSize: '14px' }}>
							Frequency: <span style={{ fontFamily: 'monospace', color: '#0066cc' }}>{localFrequency.toFixed(1)} Hz</span>
						</label>
						<div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
							<input
								type="range"
								min="0"
								max="10"
								step="0.1"
								value={localFrequency}
								onChange={handleSliderChange}
								disabled={!oscillator.enabled}
								style={{ flex: 1, cursor: oscillator.enabled ? 'pointer' : 'not-allowed' }}
							/>
							<input
								type="number"
								min="0"
								max="10"
								step="0.1"
								value={localFrequency}
								onChange={handleFrequencyChange}
								disabled={!oscillator.enabled}
								style={{
									width: '80px',
									padding: '6px',
									border: '1px solid #ccc',
									borderRadius: '4px',
									cursor: oscillator.enabled ? 'text' : 'not-allowed',
								}}
							/>
						</div>
						<p style={{ margin: '8px 0 0 0', fontSize: '12px', color: '#999' }}>
							Range: 0 - 10 Hz
						</p>
					</div>

					{/* Info box */}
					<div
						style={{
							backgroundColor: '#f0f7ff',
							border: '1px solid #b3d9ff',
							borderRadius: '6px',
							padding: '12px',
							fontSize: '13px',
							color: '#333',
							marginTop: '24px',
						}}
					>
						<p style={{ margin: '0 0 8px 0', fontWeight: '500' }}>ℹ️ How it works:</p>
						<ul style={{ margin: '0', paddingLeft: '20px', lineHeight: '1.6' }}>
							<li>Generates a square wave on the <code style={{ fontFamily: 'monospace', backgroundColor: '#e8f0ff', padding: '2px 4px' }}>global.net_osc_in</code> net</li>
							<li>Frequency range: 0 - 10 Hz</li>
							<li>Can be used as a clock or test signal for your design</li>
							<li>Automatically triggers simulation when frequency changes</li>
						</ul>
					</div>
				</div>
			</div>
		</div>
	);
};

export default OscillatorModal;
