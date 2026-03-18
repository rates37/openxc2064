# Diff Details

Date : 2026-03-13 21:57:24

Directory c:\\Xilinx\\Projects\\openxc2064\\simulator\\src

Total : 62 files,  -5971 codes, -305 comments, -1002 blanks, all -7278 lines

[Summary](results.md) / [Details](details.md) / [Diff Summary](diff.md) / Diff Details

## Files
| filename | language | code | comment | blank | total |
| :--- | :--- | ---: | ---: | ---: | ---: |
| [README.md](/README.md) | Markdown | -30 | 0 | -17 | -47 |
| [docs/bitstream\_format.md](/docs/bitstream_format.md) | Markdown | 0 | 0 | -1 | -1 |
| [docs/clb\_structure.md](/docs/clb_structure.md) | Markdown | 0 | 0 | -1 | -1 |
| [docs/implementation\_notes.md](/docs/implementation_notes.md) | Markdown | -8 | 0 | -8 | -16 |
| [docs/routing\_architecture.md](/docs/routing_architecture.md) | Markdown | 0 | 0 | -1 | -1 |
| [pin\_planning/spreadsheet\_maker.py](/pin_planning/spreadsheet_maker.py) | Python | -37 | -11 | -19 | -67 |
| [simulator/README.md](/simulator/README.md) | Markdown | -13 | 0 | -8 | -21 |
| [simulator/index.html](/simulator/index.html) | HTML | -7 | 0 | 0 | -7 |
| [simulator/index.tsx](/simulator/index.tsx) | TypeScript JSX | -16 | 0 | -2 | -18 |
| [simulator/metadata.json](/simulator/metadata.json) | JSON | -5 | 0 | 0 | -5 |
| [simulator/package-lock.json](/simulator/package-lock.json) | JSON | -2,581 | 0 | -1 | -2,582 |
| [simulator/package.json](/simulator/package.json) | JSON | -23 | 0 | -1 | -24 |
| [simulator/src/App.tsx](/simulator/src/App.tsx) | TypeScript JSX | 6 | 0 | -1 | 5 |
| [simulator/src/LogicArray.tsx](/simulator/src/LogicArray.tsx) | TypeScript JSX | -142 | -2 | -32 | -176 |
| [simulator/src/SimulatorContext.tsx](/simulator/src/SimulatorContext.tsx) | TypeScript JSX | 439 | 62 | 102 | 603 |
| [simulator/src/components/BusComponent.tsx](/simulator/src/components/BusComponent.tsx) | TypeScript JSX | -12 | 0 | -3 | -15 |
| [simulator/src/components/LineSegment.tsx](/simulator/src/components/LineSegment.tsx) | TypeScript JSX | 28 | 0 | 3 | 31 |
| [simulator/src/components/LogicCellRenderer.tsx](/simulator/src/components/LogicCellRenderer.tsx) | TypeScript JSX | 138 | 2 | 15 | 155 |
| [simulator/src/components/LogicElementComponent.tsx](/simulator/src/components/LogicElementComponent.tsx) | TypeScript JSX | -177 | -13 | -34 | -224 |
| [simulator/src/components/LogicElementModal.tsx](/simulator/src/components/LogicElementModal.tsx) | TypeScript JSX | 219 | 15 | 31 | 265 |
| [simulator/src/components/LogicElementPrimitives.tsx](/simulator/src/components/LogicElementPrimitives.tsx) | TypeScript JSX | 232 | 0 | 22 | 254 |
| [simulator/src/components/NodeBusComponent.tsx](/simulator/src/components/NodeBusComponent.tsx) | TypeScript JSX | -24 | 0 | -5 | -29 |
| [simulator/src/components/NodeComponent.tsx](/simulator/src/components/NodeComponent.tsx) | TypeScript JSX | -17 | 0 | -4 | -21 |
| [simulator/src/components/SimulationCanvas.tsx](/simulator/src/components/SimulationCanvas.tsx) | TypeScript JSX | 105 | 5 | 12 | 122 |
| [simulator/src/components/SimulationToolbar.tsx](/simulator/src/components/SimulationToolbar.tsx) | TypeScript JSX | 61 | 0 | 4 | 65 |
| [simulator/src/components/SwitchComponent.tsx](/simulator/src/components/SwitchComponent.tsx) | TypeScript JSX | -12 | 0 | -2 | -14 |
| [simulator/src/components/SwitchMatrixEditor.tsx](/simulator/src/components/SwitchMatrixEditor.tsx) | TypeScript JSX | 163 | 6 | 23 | 192 |
| [simulator/src/components/modals/LogicElementModal.tsx](/simulator/src/components/modals/LogicElementModal.tsx) | TypeScript JSX | -202 | -12 | -33 | -247 |
| [simulator/src/components/modals/LogicElementPrimitives.tsx](/simulator/src/components/modals/LogicElementPrimitives.tsx) | TypeScript JSX | -232 | -10 | -23 | -265 |
| [simulator/src/configs/Routing.ts](/simulator/src/configs/Routing.ts) | TypeScript | 13 | 0 | 4 | 17 |
| [simulator/src/configs/configs.ts](/simulator/src/configs/configs.ts) | TypeScript | 309 | 1 | 23 | 333 |
| [simulator/src/constants.tsx](/simulator/src/constants.tsx) | TypeScript JSX | -25 | 0 | -4 | -29 |
| [simulator/src/context/SimulatorContext.tsx](/simulator/src/context/SimulatorContext.tsx) | TypeScript JSX | -45 | -4 | -22 | -71 |
| [simulator/src/models/IOBank.ts](/simulator/src/models/IOBank.ts) | TypeScript | 16 | 0 | 8 | 24 |
| [simulator/src/models/LogicCell.ts](/simulator/src/models/LogicCell.ts) | TypeScript | 102 | 23 | 32 | 157 |
| [simulator/src/models/LogicElement.tsx](/simulator/src/models/LogicElement.tsx) | TypeScript JSX | -104 | -15 | -31 | -150 |
| [simulator/src/models/SwitchMatrix.ts](/simulator/src/models/SwitchMatrix.ts) | TypeScript | 42 | 0 | 11 | 53 |
| [simulator/src/styles/Bus.css](/simulator/src/styles/Bus.css) | PostCSS | -15 | -1 | -3 | -19 |
| [simulator/src/styles/LogicArray.css](/simulator/src/styles/LogicArray.css) | PostCSS | -35 | -1 | -7 | -43 |
| [simulator/src/styles/Modal.css](/simulator/src/styles/Modal.css) | PostCSS | 18 | 0 | 2 | 20 |
| [simulator/src/styles/Node.css](/simulator/src/styles/Node.css) | PostCSS | -10 | -1 | -1 | -12 |
| [simulator/src/styles/Switch.css](/simulator/src/styles/Switch.css) | PostCSS | -10 | 0 | -1 | -11 |
| [simulator/src/types.ts](/simulator/src/types.ts) | TypeScript | 22 | 0 | 6 | 28 |
| [simulator/tsconfig.json](/simulator/tsconfig.json) | JSON with Comments | -29 | 0 | 0 | -29 |
| [simulator/vite.config.ts](/simulator/vite.config.ts) | TypeScript | -22 | 0 | -2 | -24 |
| [src/openxc2064/\_\_init\_\_.py](/src/openxc2064/__init__.py) | Python | -4 | 0 | -1 | -5 |
| [src/openxc2064/hdl/\_\_init\_\_.py](/src/openxc2064/hdl/__init__.py) | Python | -2 | -4 | -2 | -8 |
| [src/openxc2064/hdl/ast\_nodes.py](/src/openxc2064/hdl/ast_nodes.py) | Python | -97 | -4 | -50 | -151 |
| [src/openxc2064/hdl/parser.py](/src/openxc2064/hdl/parser.py) | Python | -193 | -14 | -51 | -258 |
| [src/openxc2064/simulator/\_\_init\_\_.py](/src/openxc2064/simulator/__init__.py) | Python | -1 | 0 | -1 | -2 |
| [src/openxc2064/simulator/high\_level\_rtl\_simulator.py](/src/openxc2064/simulator/high_level_rtl_simulator.py) | Python | -239 | -47 | -69 | -355 |
| [src/openxc2064/synthesis/\_\_init\_\_.py](/src/openxc2064/synthesis/__init__.py) | Python | -2 | 0 | -1 | -3 |
| [src/openxc2064/synthesis/elaborator.py](/src/openxc2064/synthesis/elaborator.py) | Python | -268 | -48 | -74 | -390 |
| [src/openxc2064/synthesis/rtl\_nodes.py](/src/openxc2064/synthesis/rtl_nodes.py) | Python | -72 | -9 | -29 | -110 |
| [src/openxc2064/synthesis/synthesis.py](/src/openxc2064/synthesis/synthesis.py) | Python | -255 | -27 | -56 | -338 |
| [tests/\_\_init\_\_.py](/tests/__init__.py) | Python | 0 | 0 | -1 | -1 |
| [tests/test\_elaborator.py](/tests/test_elaborator.py) | Python | -627 | -20 | -80 | -727 |
| [tests/test\_high\_level\_rtl\_simulator.py](/tests/test_high_level_rtl_simulator.py) | Python | -600 | -39 | -256 | -895 |
| [tests/test\_integration\_high\_level\_rtl\_simulator.py](/tests/test_integration_high_level_rtl_simulator.py) | Python | -539 | -29 | -125 | -693 |
| [tests/test\_parser.py](/tests/test_parser.py) | Python | -601 | -67 | -105 | -773 |
| [tests/test\_synthesiser.py](/tests/test_synthesiser.py) | Python | -372 | -41 | -116 | -529 |
| [uv.lock](/uv.lock) | toml | -179 | 0 | -16 | -195 |

[Summary](results.md) / [Details](details.md) / [Diff Summary](diff.md) / Diff Details