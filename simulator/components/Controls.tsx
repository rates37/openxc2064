import React, { useState } from 'react';
import { SimulationMode, BoxEntity } from '../types';
import { Play, Pause, RotateCcw, Plus, Wand2, Settings2 } from 'lucide-react';
import { generateScenario } from '../services/geminiService';
import { generateInitialBoxes } from '../services/simulationEngine';

interface ControlsProps {
  mode: SimulationMode;
  setMode: (mode: SimulationMode) => void;
  onReset: () => void;
  onAddBox: () => void;
  setEntities: React.Dispatch<React.SetStateAction<BoxEntity[]>>;
  canvasWidth: number;
  canvasHeight: number;
  toggleGrid: () => void;
  toggleConnections: () => void;
  showGrid: boolean;
  showConnections: boolean;
}

const Controls: React.FC<ControlsProps> = ({
  mode,
  setMode,
  onReset,
  onAddBox,
  setEntities,
  canvasWidth,
  canvasHeight,
  toggleGrid,
  toggleConnections,
  showGrid,
  showConnections
}) => {
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    if (!process.env.API_KEY) {
        setError("No API Key found in environment.");
        return;
    }
    
    setIsGenerating(true);
    setError(null);
    try {
      // Pause while generating
      const prevMode = mode;
      setMode(SimulationMode.PAUSED);
      
      const newEntities = await generateScenario(prompt, { width: canvasWidth, height: canvasHeight });
      setEntities(newEntities);
      
      // Optional: Resume or stay paused? Let's stay paused to let user see setup.
    } catch (e) {
      setError('Failed to generate scenario. Check console.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="w-80 bg-sim-panel border-l border-gray-700 flex flex-col h-full text-sm shadow-xl z-10">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 bg-gray-900/50">
        <h2 className="text-lg font-bold text-sim-accent flex items-center gap-2">
          <Settings2 size={20} />
          SimuFrame Control
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        
        {/* Playback Controls */}
        <div className="space-y-2">
          <label className="text-gray-400 font-semibold text-xs uppercase tracking-wider">Playback</label>
          <div className="flex gap-2">
            {mode === SimulationMode.RUNNING ? (
              <button
                onClick={() => setMode(SimulationMode.PAUSED)}
                className="flex-1 bg-amber-600 hover:bg-amber-500 text-white py-2 rounded flex items-center justify-center gap-2 transition-colors"
              >
                <Pause size={16} /> Pause
              </button>
            ) : (
              <button
                onClick={() => setMode(SimulationMode.RUNNING)}
                className="flex-1 bg-green-600 hover:bg-green-500 text-white py-2 rounded flex items-center justify-center gap-2 transition-colors"
              >
                <Play size={16} /> Run
              </button>
            )}
            <button
              onClick={onReset}
              className="px-3 bg-gray-700 hover:bg-gray-600 text-white rounded flex items-center justify-center transition-colors"
              title="Reset Scene"
            >
              <RotateCcw size={16} />
            </button>
          </div>
        </div>

        {/* Visual Toggles */}
        <div className="space-y-2">
             <label className="text-gray-400 font-semibold text-xs uppercase tracking-wider">View Options</label>
             <div className="flex flex-col gap-2">
                <label className="flex items-center gap-2 cursor-pointer hover:text-white text-gray-300">
                    <input type="checkbox" checked={showGrid} onChange={toggleGrid} className="rounded border-gray-600 bg-gray-800 text-sim-accent focus:ring-offset-gray-900" />
                    Show Grid
                </label>
                <label className="flex items-center gap-2 cursor-pointer hover:text-white text-gray-300">
                    <input type="checkbox" checked={showConnections} onChange={toggleConnections} className="rounded border-gray-600 bg-gray-800 text-sim-accent focus:ring-offset-gray-900" />
                    Show Network Lines
                </label>
             </div>
        </div>

        {/* Manual Tools */}
        <div className="space-y-2">
          <label className="text-gray-400 font-semibold text-xs uppercase tracking-wider">Tools</label>
          <button
            onClick={onAddBox}
            className="w-full bg-gray-700 hover:bg-gray-600 py-2 rounded flex items-center justify-center gap-2 transition-colors"
          >
            <Plus size={16} /> Add Random Box
          </button>
        </div>

        {/* AI Generation */}
        <div className="space-y-3 pt-4 border-t border-gray-700">
          <label className="text-sim-accent font-semibold text-xs uppercase tracking-wider flex items-center gap-2">
            <Wand2 size={14} /> AI Generator
          </label>
          <div className="space-y-2">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe a scenario (e.g., '20 red boxes moving fast left', 'A solar system pattern')"
              className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-gray-200 text-xs focus:border-sim-accent focus:outline-none resize-none h-20"
            />
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className={`w-full py-2 rounded text-white text-xs font-medium transition-all ${
                isGenerating 
                  ? 'bg-purple-900 cursor-wait opacity-75' 
                  : 'bg-purple-600 hover:bg-purple-500 shadow-lg shadow-purple-900/20'
              }`}
            >
              {isGenerating ? 'Generating...' : 'Generate Scenario'}
            </button>
            {error && (
                <p className="text-red-400 text-xs mt-1">{error}</p>
            )}
          </div>
        </div>
      </div>
      
      <div className="p-4 border-t border-gray-700 text-gray-500 text-xs text-center">
        SimuFrame v1.0
      </div>
    </div>
  );
};

export default Controls;
