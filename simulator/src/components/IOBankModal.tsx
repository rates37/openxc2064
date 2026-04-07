import React from 'react';
import '../styles/Modal.css';
import { useSimulator } from '../SimulatorContext';
import { LineSegment } from './LineSegment';

// Visual style constants (top-level to avoid recreating each render)
const BASE_STROKE = '#333';
const ACTIVE_STROKE = '#f00';
const BASE_FILL = '#fff';
const ACTIVE_FILL = 'rgb(255, 112, 112)';

const getStroke = (value: boolean) => (value ? ACTIVE_STROKE : BASE_STROKE);
const getFill = (value: boolean) => (value ? ACTIVE_FILL : BASE_FILL);

type Point = { x: number; y: number; continuous?: boolean };

// Small presentational subcomponents to reduce inline JSX noise
const ToggleRect = React.memo(({ x, y, width, height, value, onToggle }: { x: number; y: number; width: number; height: number; value: boolean; onToggle: () => void }) => (
	<g onClick={onToggle}>
		<rect x={x} y={y} width={width} height={height} fill={getFill(value)} stroke={getStroke(value)} strokeWidth={3} pointer="cursor" />
	</g>
));

const MuxGroup = React.memo(({ onClick, polygonPoints, lineBase, linePoints, value }: { onClick: () => void; polygonPoints: string; lineBase: { x: number; y: number }; linePoints: Point[]; value: boolean }) => (
	<g pointer="cursor" onClick={onClick}>
		<polygon points={polygonPoints} fill={BASE_FILL} stroke={BASE_STROKE} strokeWidth={3} />
		<LineSegment baseX={lineBase.x} baseY={lineBase.y} points={linePoints} value={value} strokeWidth={3} />
	</g>
));

// Pure helper to get a net by ID from an IOBank
const getNet = (selectedIOBank: any, net_id: string) => {
	return selectedIOBank.nets.find((net: any) => net.id === `${selectedIOBank.id}.${net_id}`) || { id: net_id, value: false };
};

const IOBankModal = React.memo(() => {
	const { selectedIOBank, selectIOBank, updateIOBank, toggleIONet, simulate } = useSimulator();

	const [muxes, setMuxes] = React.useState<{ id: string; select: number }[]>([]);
	const [mtsMuxPoints, setMtsMuxPoints] = React.useState<Point[]>([
		{ x: 0, y: 0 },
		{ x: 30, y: -40 },
	]);
	const [inMuxPoints, setInMuxPoints] = React.useState<Point[]>([
		{ x: 0, y: 0 },
		{ x: -30, y: -40 },
	]);

	// Sync local mux state whenever selectedIOBank changes
	React.useEffect(() => {
		if (selectedIOBank) {
			setMuxes([...selectedIOBank.muxes]);
			
			// Reset mux line positions based on the new bank's mux selections
			const mtsMux = selectedIOBank.muxes.find((m) => m.id === 'mts');
			if (mtsMux) {
				switch (mtsMux.select) {
					case 0:
						setMtsMuxPoints([{ x: 0, y: 0 }, { x: 30, y: -40 }]);
						break;
					case 1:
						setMtsMuxPoints([{ x: 0, y: 0 }, { x: 30, y: 0 }]);
						break;
					case 2:
						setMtsMuxPoints([{ x: 0, y: 0 }, { x: 30, y: 40 }]);
						break;
				}
			}

			const minMux = selectedIOBank.muxes.find((m) => m.id === 'min');
			if (minMux) {
				switch (minMux.select) {
					case 0:
						setInMuxPoints([{ x: 0, y: 0 }, { x: -30, y: -40 }]);
						break;
					case 1:
						setInMuxPoints([{ x: 0, y: 0 }, { x: -30, y: 40 }]);
						break;
				}
			}
		}
	}, [selectedIOBank]);

	// Helper to increment mux select value (wraps around)
	const handleMuxClick = React.useCallback((muxId: string, numInputs: number) => {
		if (!selectedIOBank) return;
		const mux = selectedIOBank.muxes.find((m) => m.id === muxId);
		if (!mux) return;

		mux.select = (mux.select + 1) % numInputs;
		// Mutate in place and trigger rerender by re-calling simulate/update
		simulate();
		setMuxes([...selectedIOBank.muxes]);
		updateIOBank(selectedIOBank);

		if (muxId === 'mts') {
			switch (mux.select) {
				case 0:
					setMtsMuxPoints([{ x: 0, y: 0 }, { x: 30, y: -40 }]);
					break;
				case 1:
					setMtsMuxPoints([{ x: 0, y: 0 }, { x: 30, y: 0 }]);
					break;
				case 2:
					setMtsMuxPoints([{ x: 0, y: 0 }, { x: 30, y: 40 }]);
					break;
			}
		}

		if (muxId === 'min') {
			switch (mux.select) {
				case 0:
					setInMuxPoints([{ x: 0, y: 0 }, { x: -30, y: -40 }]);
					break;
				case 1:
					setInMuxPoints([{ x: 0, y: 0 }, { x: -30, y: 40 }]);
					break;
			}
		}
	}, [selectedIOBank, updateIOBank]);

	const handleClose = React.useCallback(() => selectIOBank(null), [selectIOBank]);

	const handleTogglePad = React.useCallback(() => {
		if (!selectedIOBank) return;
		toggleIONet(selectedIOBank.index);
	}, [selectedIOBank, toggleIONet]);

	if (!selectedIOBank) return null;

	return (
		<div className="modal-overlay" onClick={handleClose}>
			<div className="modal-content" onClick={(e) => e.stopPropagation()}>
				<div className="modal-header">
					<h2>{selectedIOBank.id} &mdash; IO Bank</h2>
					<button className="modal-close-btn" onClick={handleClose}>
						&times;
					</button>
				</div>
				<div className="modal-body">
					{/* Blank SVG canvas for user editing */}
					<svg className="le-diagram modal-logic" viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">
						<rect fill="#fff" width="100%" height="100%" rx={8} />

						{/* Output Pad net */}
						<LineSegment
							baseX={30}
							baseY={280}
							points={[
								{ x: 0, y: 0 },
								{ x: 100, y: 0 },
								{ x: 100, y: 80 },
								{ x: 200, y: 80 },
								{ x: 100, y: 0, continuous: false },
								{ x: 100, y: -80 },
								{ x: 200, y: -80 },
							]}
							value={getNet(selectedIOBank, 'net_pad').value}
							strokeWidth={3}
						/>

						<ToggleRect x={20} y={260} width={40} height={40} value={getNet(selectedIOBank, 'net_pad').value} onToggle={handleTogglePad} />

						{/* Tristate buffer display */}
						<polygon points={`230,200 290,240, 290,160`} fill={BASE_FILL} stroke={BASE_STROKE} strokeWidth={3} />
						<LineSegment
							baseX={260}
							baseY={175}
							points={[{ x: 0, y: 0 }, { x: 0, y: -80 }, { x: 80, y: -80 }]}
							value={getNet(selectedIOBank, 'net_ts_mux').value}
							strokeWidth={3}
						/>
						<circle cx={260} cy={175} r={5} fill={BASE_FILL} stroke={BASE_STROKE} strokeWidth={3} />
						<LineSegment baseX={290} baseY={200} points={[{ x: 0, y: 0 }, { x: 410, y: 0 }]} value={getNet(selectedIOBank, 'net_O').value} strokeWidth={3} />

						<MuxGroup onClick={() => handleMuxClick('mts', 3)} polygonPoints={`340,135 340,55 370,35, 370,155`} lineBase={{ x: 340, y: 95 }} linePoints={mtsMuxPoints} value={getNet(selectedIOBank, 'net_ts_mux').value} />

						<LineSegment baseX={340} baseY={95} points={[{ x: 30, y: -40 }, { x: 80, y: -40 }, { x: 80, y: -70 }, { x: 70, y: -70 }, { x: 90, y: -70 }]} value={true} strokeWidth={3} />

						<LineSegment
							baseX={340}
							baseY={95}
							points={[
								{ x: 30, y: 40 },
								{ x: 80, y: 40 },
								{ x: 80, y: 70 },
								{ x: 70, y: 70 },
								{ x: 90, y: 70 },
								{ x: 88, y: 75, continuous: false },
								{ x: 72, y: 75 },
								{ x: 85, y: 80, continuous: false },
								{ x: 75, y: 80 },
							]}
							value={false}
							strokeWidth={3}
						/>
						<LineSegment baseX={340} baseY={95} points={[{ x: 30, y: 0 }, { x: 362, y: 0 }]} value={getNet(selectedIOBank, 'net_T').value} strokeWidth={3} />

						{/* Input Buffer Display */}
						<polygon points={`270,360 230,380, 230,340`} fill={BASE_FILL} stroke={BASE_STROKE} strokeWidth={3} />
						<LineSegment baseX={270} baseY={360} points={[{ x: 0, y: 0 }, { x: 300, y: 0 }, { x: 60, y: 0, continuous: false }, { x: 60, y: 80 }, { x: 140, y: 80 }]} value={getNet(selectedIOBank, 'net_pad').value} strokeWidth={3} />

						{/* Input DFF Display */}
						<rect x={400} y={400} width={80} height={120} fill={BASE_FILL} stroke={BASE_STROKE} strokeWidth={3} />
						<polygon points={`420,490 400,500, 400,480`} fill={BASE_FILL} stroke={BASE_STROKE} strokeWidth={3} />
						<text x={405} y={450} fontSize={24} fill={BASE_STROKE}>D</text>
						<text x={455} y={450} fontSize={24} fill={BASE_STROKE}>Q</text>

						{/* I/O Clock Net */}
						<LineSegment baseX={400} baseY={490} points={[{ x: 0, y: 0 }, { x: -70, y: 0 }, { x: -70, y: 80 }, { x: 300, y: 80 }]} value={getNet(selectedIOBank, 'net_io_clk').value} strokeWidth={3} />

						{/* DFF Output Net */}
						<LineSegment baseX={480} baseY={440} points={[{ x: 0, y: 0 }, { x: 89, y: 0 }]} value={getNet(selectedIOBank, 'net_in_q').value} strokeWidth={3} />

						<MuxGroup onClick={() => handleMuxClick('min', 2)} polygonPoints={`600,440 600,360 570,340, 570,460`} lineBase={{ x: 600, y: 400 }} linePoints={inMuxPoints} value={getNet(selectedIOBank, 'net_in_mux').value} />

						<LineSegment baseX={600} baseY={400} points={[{ x: 0, y: 0 }, { x: 100, y: 0 }]} value={getNet(selectedIOBank, 'net_I').value} strokeWidth={3} />
					
						<text x={710} y={104} fontSize={30} fill={BASE_STROKE}>TS_n</text>
						<text x={710} y={210} fontSize={30} fill={BASE_STROKE}>Out</text>
						<text x={710} y={410} fontSize={30} fill={BASE_STROKE}>In</text>
						<text x={710} y={580} fontSize={30} fill={BASE_STROKE}>Clk</text>


					</svg>
				</div>
			</div>
		</div>
	);
});

export default IOBankModal;
