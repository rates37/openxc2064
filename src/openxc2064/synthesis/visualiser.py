"""
Disclaimer: this is almost completely AI generated, shouldn't be used for anything
serious.
"""
import json
from openxc2064.synthesis.rtl_nodes import Netlist, Node, LogicGate, DFF, Input, Constant

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
            background-color: #333;
            color: white;
            border-radius: 4px;
            padding: 8px;
            font-family: monospace;
            font-size: 13px;
            line-height: 1.4;
            max-width: 300px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .tippy-arrow { color: #333; }
        .node-tag { color: #64ffda; font-weight: bold; }
        .net-tag { color: #ffeb3b; font-weight: bold; }
        
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
                    style: {
                        'shape': 'tag',
                        'background-color': '#e3f2fd',
                        'border-color': '#2196f3'
                    }
                },
                {
                    selector: 'node[type = "Constant"]',
                    style: {
                        'shape': 'barrel',
                        'background-color': '#fff3e0',
                        'border-color': '#ff9800'
                    }
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
                    style: {
                        'shape': 'rectangle',
                        'background-color': '#e8f5e9',
                        'border-color': '#4caf50'
                    }
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
            wheelSensitivity: 0.2, // Smoother, much less sensitive zooming
            pixelRatio: 1 // Fixes drag/mouse coordinate scaling issues on high-DPI/Windows zoomed displays
        });

        // Setup Tooltip Singleton via Tippy/Popper
        const dummyDomEle = document.createElement('div');
        const globalTip = tippy(dummyDomEle, {
            trigger: 'manual',
            allowHTML: true,
            placement: 'top',
            arrow: true,
            interactive: false,
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
                        html += `<div>${k}: ${v}</div>`;
                    }
                }
            } else {
                html += `<div><span class="net-tag">Net</span>: ${data.net_name}</div>`;
                html += `<div>Width: ${data.width}</div>`;
                html += `<div>Endpoints: ${data.source} → ${data.target}</div>`;
            }

            // Update Popper target to this specific element's bounding box
            const ref = ele.popperRef();
            globalTip.setProps({
                getReferenceClientRect: ref.getBoundingClientRect
            });
            globalTip.setContent(html);
            globalTip.show();
        });

        cy.on('mouseout', 'node, edge', function(evt){
            globalTip.hide();
        });
        
        // Hide tooltip actively during pans/drags to avoid coordinate lag
        cy.on('pan zoom grab', function(){
            globalTip.hide();
        });
        
        // Button Controls
        document.getElementById('btn-fit').addEventListener('click', () => {
            cy.fit();
            cy.center();
        });
        document.getElementById('btn-zoom-in').addEventListener('click', () => {
            cy.zoom(cy.zoom() * 1.5);
            cy.center();
        });
        document.getElementById('btn-zoom-out').addEventListener('click', () => {
            cy.zoom(cy.zoom() / 1.5);
            cy.center();
        });
    </script>
</body>
</html>
"""

class NetlistVisualiser:
    def __init__(self):
        pass

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

            in_nets = [n.name for n in node.inputs]
            out_nets = [n.name for n in node.outputs]
            if in_nets: details["Inputs"] = ", ".join(in_nets)
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
        # We model a Net as directed edges from Net.source to each of Net.sinks
        for net in netlist.nets:
            if not net.source:
                continue # Unknown driver (maybe implicitly driven external port, but shouldn't happen)
                
            src_id = net.source.id
            width = net.width
            
            # visual edge width scaling
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
