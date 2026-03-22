"""
Comprehensive Netlist and CLB Visualiser for OpenXC2064.
"""
import json
from openxc2064.synthesis.rtl_nodes import Netlist, Node, LogicGate, DFF, Input, Constant
from openxc2064.mapping.xc2064_primitives import LUT, CLB, IOB

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>OpenXC2064 Netlist Visualiser</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.23.0/cytoscape.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/dagre/0.8.5/dagre.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
    
    <!-- Tooltip Dependencies -->
    <script src="https://unpkg.com/@popperjs/core@2"></script>
    <script src="https://unpkg.com/tippy.js@6"></script>
    <link rel="stylesheet" href="https://unpkg.com/tippy.js@6/animations/scale.css" />
    <script src="https://cdn.jsdelivr.net/npm/cytoscape-popper@2.0.0/cytoscape-popper.min.js"></script>

    <style>
        body { font-family: sans-serif; margin: 0; padding: 0; overflow: hidden; background: #fafafa; }
        #cy { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: block; }
        
        .tippy-box {
            background-color: #2b2b2b;
            color: #e0e0e0;
            border-radius: 6px;
            padding: 10px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.5;
            max-width: 450px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            white-space: pre-wrap; /* allow nice formatting for grids */
        }
        .tippy-arrow { color: #2b2b2b; }
        .node-tag { color: #64ffda; font-weight: bold; }
        .net-tag { color: #ffeb3b; font-weight: bold; }
        .tt-grid { 
            display: inline-block; 
            border: 1px solid #555; 
            padding: 4px; 
            margin-top: 4px; 
            background: #1e1e1e;
        }
        
        /* Floating Controls */
        #controls {
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            gap: 8px;
            z-index: 100;
        }
        button {
            padding: 8px 16px;
            border: 1px solid #ddd;
            background: #f8f9fa;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            font-family: sans-serif;
            font-weight: bold;
            color: #333;
            transition: background 0.2s;
        }
        button:hover { background: #e9ecef; }
        button:active { background: #dee2e6; }
    </style>
</head>
<body>
    <div id="cy"></div>
    <div id="controls">
        <button id="btn-fit">Fit Design</button>
        <button id="btn-zoom-in">Zoom In</button>
        <button id="btn-zoom-out">Zoom Out</button>
    </div>

    <script>
        const graphData = GRAPH_DATA_PLACEHOLDER;

        const cy = cytoscape({
            container: document.getElementById('cy'),
            elements: graphData,
            style: [
                {
                    selector: 'node',
                    style: {
                        'label': 'data(label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'shape': 'round-rectangle',
                        'padding': '10px',
                        'background-color': '#e0e0e0',
                        'border-width': 2,
                        'border-color': '#9e9e9e',
                        'font-family': 'monospace',
                        'font-size': '12px',
                        'width': 'label',
                        'height': 'label'
                    }
                },
                {
                    selector: 'node[type = "Input"]',
                    style: { 'shape': 'tag', 'background-color': '#e3f2fd', 'border-color': '#2196f3' }
                },
                {
                    selector: 'node[type = "Constant"]',
                    style: { 'shape': 'barrel', 'background-color': '#fff3e0', 'border-color': '#ff9800' }
                },
                {
                    selector: 'node[type = "LogicGate"]',
                    style: {
                        'shape': 'polygon',
                        'shape-polygon-points': '-1, -1, 0.5, -1, 1, 0, 0.5, 1, -1, 1',
                        'background-color': '#f3e5f5',
                        'border-color': '#9c27b0'
                    }
                },
                {
                    selector: 'node[type = "DFF"]',
                    style: { 'shape': 'rectangle', 'background-color': '#e8f5e9', 'border-color': '#4caf50' }
                },
                {
                    selector: 'node[type = "LUT"]',
                    style: { 'shape': 'ellipse', 'background-color': '#ede7f6', 'border-color': '#673ab7' }
                },
                {
                    selector: 'node[type = "CLB"]',
                    style: { 'shape': 'hexagon', 'background-color': '#e1bee7', 'border-color': '#8e24aa', 'border-width': 3 }
                },
                {
                    selector: 'node[type = "IOB"]',
                    style: { 'shape': 'diamond', 'background-color': '#ffcc80', 'border-color': '#ef6c00' }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 'data(width)',
                        'line-color': '#b0bec5',
                        'target-arrow-color': '#b0bec5',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'label': 'data(label)',
                        'font-size': '10px',
                        'color': '#546e7a',
                        'text-background-opacity': 1,
                        'text-background-color': '#fafafa',
                        'text-background-padding': '2px',
                        'text-rotation': 'autorotate'
                    }
                }
            ],
            layout: {
                name: 'dagre',
                nodeSep: 60,
                rankSep: 100,
                rankDir: 'LR'
            },
            wheelSensitivity: 0.2,
            pixelRatio: 1
        });

        const dummyDomEle = document.createElement('div');
        const globalTip = tippy(dummyDomEle, {
            trigger: 'manual',
            allowHTML: true,
            placement: 'top',
            arrow: true,
            interactive: true, // Allow selecting text inside tooltip
            appendTo: document.body,
            animation: 'scale'
        });

        cy.on('mouseover', 'node, edge', function(evt){
            const ele = evt.target;
            const data = ele.data();
            let html = "";
            
            if (ele.isNode()) {
                html += `<div><span class="node-tag">${data.type}</span>: ${data.id}</div>`;
                if (data.details) {
                    for (const [k, v] of Object.entries(data.details)) {
                        // Allow v to be raw HTML (for our truth table grids)
                        html += `<div><strong style="color: #90caf9">${k}</strong>: ${v}</div>`;
                    }
                }
            } else {
                html += `<div><span class="net-tag">Net</span>: ${data.net_name}</div>`;
                html += `<div>Width: ${data.width}</div>`;
                html += `<div>Endpoints: ${data.source} → ${data.target}</div>`;
            }

            const ref = ele.popperRef();
            globalTip.setProps({ getReferenceClientRect: ref.getBoundingClientRect });
            globalTip.setContent(html);
            globalTip.show();
        });

        cy.on('mouseout', 'node, edge', function(evt){
            // Delay hide slightly so interactive tooltips can be hovered
            globalTip.hide();
        });
        
        cy.on('pan zoom grab', function(){ globalTip.hide(); });
        
        document.getElementById('btn-fit').addEventListener('click', () => { cy.fit(); cy.center(); });
        document.getElementById('btn-zoom-in').addEventListener('click', () => { cy.zoom(cy.zoom() * 1.5); cy.center(); });
        document.getElementById('btn-zoom-out').addEventListener('click', () => { cy.zoom(cy.zoom() / 1.5); cy.center(); });
    </script>
</body>
</html>
"""

class NetlistVisualiser:
    def __init__(self):
        pass
        
    def _format_tt_grid(self, tt: int, inputs: list[str]) -> str:
        """Returns an HTML truth table string evaluating the 8 physical memory states."""
        # For a 3-input LUT, it's 8 states.
        num_vars = len(inputs)
        # We cap grid rendering at 4 variables (16 rows) to avoid massive tooltips,
        # but XC2064 only uses 3-input LUTs (8 rows) anyway so this is perfect!
        if num_vars > 4:
            return f"Hex: {hex(tt)}"
            
        header = " | ".join(inputs[::-1]) + " || OUT"
        divider = "-" * len(header)
        
        rows = []
        for state in range(1 << num_vars):
            bits = []
            for i in reversed(range(num_vars)):
                bits.append(str((state >> i) & 1).center(len(inputs[len(inputs)-1-i])))
            val = str((tt >> state) & 1)
            rows.append(f"{' | '.join(bits)} ||  {val}")
            
        grid = "<br>".join([header, divider] + rows)
        return f"<br><div class='tt-grid'>{grid}</div>"

    def generate_html(self, netlist: Netlist, filename: str = "netlist_viewer.html") -> None:
        elements = []

        # 1. Export Nodes
        for node in netlist.nodes:
            label = node.id
            node_type = type(node).__name__
            details = {}
            
            if isinstance(node, Input):
                label = f"IN:{node.port_name}"
                details["Port"] = node.port_name
            elif isinstance(node, Constant):
                label = f"CONST:{node.value}"
                details["Value"] = str(node.value)
            elif isinstance(node, LogicGate):
                label = node.op
                details["Operation"] = node.op
            elif isinstance(node, DFF):
                label = "DFF"
                details["Edge Trigger"] = node.edge
            elif isinstance(node, LUT):
                label = "LUT"
                in_names = [n.name for n in node.inputs]
                details["Truth Table"] = self._format_tt_grid(node.truth_table, in_names)
            elif isinstance(node, IOB):
                label = f"IOB Pad"
                ts_map = {0: "OFF (High-Z)", 1: "TS (Bi-Directional)", 2: "ON (Drive Output)"}
                in_map = {0: "Combinational Bypass", 1: "Clocked DFF Q"}
                details["Pad Name"] = node.pad_name
                details["TS MUX"] = ts_map.get(node.ts_mux_sel, "Unknown")
                details["IN MUX"] = in_map.get(node.in_mux_sel, "Unknown")
                if node.dff:
                    details["Pad DFF"] = f"Trigger: {node.dff.edge}"
            elif isinstance(node, CLB):
                label = "CLB"
                # Decode all internal pin wirings and routing MUX arrays
                input_names = [n.name if n else "None" for n in node.inputs]
                A = input_names[0] if len(input_names) > 0 else "None"
                B = input_names[1] if len(input_names) > 1 else "None"
                C = input_names[2] if len(input_names) > 2 else "None"
                D = input_names[3] if len(input_names) > 3 else "None"
                K = input_names[4] if len(input_names) > 4 else "None"
                
                details["Bounded Pins"] = f"A:{A}, B:{B}, C:{C}, D:{D}, K:{K}"
                
                f_in0 = B if node.sel_f_in1 else A
                f_in1 = C if node.sel_f_in2 else B
                f_in2 = "Q" if node.sel_f_in3 == 2 else (D if node.sel_f_in3 == 1 else C)
                
                g_in0 = B if node.sel_g_in1 else A
                g_in1 = C if node.sel_g_in2 else B
                g_in2 = "Q" if node.sel_g_in3 == 2 else (D if node.sel_g_in3 == 1 else C)
                
                details["LUT F Inputs"] = f"in1:{f_in0}, in2:{f_in1}, in3:{f_in2}"
                details["LUT F Boolean Logic"] = self._format_tt_grid(node.lut_f_init, [f_in0, f_in1, f_in2])
                
                details["LUT G Inputs"] = f"in1:{g_in0}, in2:{g_in1}, in3:{g_in2}"
                details["LUT G Boolean Logic"] = self._format_tt_grid(node.lut_g_init, [g_in0, g_in1, g_in2])
                
                # Global Exports
                x_map = {0: "G", 1: "Q", 2: "F"}
                y_map = {0: "G", 1: "Q", 2: "F"}
                details["Output Routing"] = f"X exports '{x_map.get(node.sel_x)}' | Y exports '{y_map.get(node.sel_y)}'"
                
                if node.dff:
                    details["Internal DFF"] = f"Mapped (Clock: {node.dff.edge})"

            in_nets = [n.name for n in node.inputs if n]
            out_nets = [n.name for n in node.outputs if n]
            if in_nets and not isinstance(node, CLB): details["Inputs"] = ", ".join(in_nets)
            if out_nets: details["Outputs"] = ", ".join(out_nets)

            elements.append({
                "group": "nodes",
                "data": {
                    "id": node.id,
                    "label": label,
                    "type": node_type,
                    "details": details
                }
            })

        # 2. Export Edges (Nets)
        for net in netlist.nets:
            for source in net.drivers:
                src_id = source.id
                width = net.width
                scaled_width = 1.5 if width == 1 else min(6, 1.5 + (width * 0.3))

                for i, sink in enumerate(net.sinks):
                    elements.append({
                        "group": "edges",
                        "data": {
                            "id": f"{net.name}_{src_id}_{sink.id}_{i}",
                            "source": src_id,
                            "target": sink.id,
                            "label": f"{net.name} [{width}]",
                            "net_name": net.name,
                            "width": scaled_width
                        }
                    })

        # 3. Inject and write mapping
        json_data = json.dumps(elements)
        html_out = HTML_TEMPLATE.replace("GRAPH_DATA_PLACEHOLDER", json_data)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_out)
