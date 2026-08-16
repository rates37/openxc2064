import json
import openpyxl
from tqdm import tqdm
import matplotlib.pyplot as plt

DEBUG = False

possible_connections = [
        [0, 0, 1, 0, 1, 1, 1, 1],
        [0, 0, 1, 1, 1, 1, 0, 1],
        [1, 1, 0, 0, 1, 0, 1, 1],
        [0, 1, 0, 0, 1, 1, 1, 1],
        [1, 1, 1, 1, 0, 0, 1, 0],
        [1, 1, 0, 1, 0, 0, 1, 1],
        [1, 0, 1, 1, 1, 1, 0, 0],
        [1, 1, 1, 1, 0, 1, 0, 0]
    ]

def parse_clb(data) -> dict[str, int]:
    bitstream = {}

    if DEBUG:
        print(data)

    for lut in data["luts"]:
        lut_idx = 1 if lut["id"] == "lut_0" else 2
        for bit_idx in range(8):
            bitstream[f"CLB {data['id']} Logic Table: {lut_idx} Bit: {bit_idx}"] = 1 if lut["truthTable"][bit_idx] else 0

    bitstream[f"CLB {data['id']} Select Latch/FF"] = 0 ## TODO: Verify!
    bitstream[f"CLB {data['id']} BASE FG"] = 0 ## TODO: Verify!


    for mux in data["muxes"]:
        if (mux["id"] == "m6"):
            bitstream[f"CLB {data['id']} Logic Table: 1 Mux A/B"] = mux["select"]
        elif (mux["id"] == "m8"):
            bitstream[f"CLB {data['id']} Logic Table: 1 Mux B/C"] = mux["select"]
        elif (mux["id"] == "m13"):
            bitstream[f"CLB {data['id']} Logic Table: 1 Mux C/D/Q Bit: 0"] = 1 if mux["select"] == 1 else 0
            bitstream[f"CLB {data['id']} Logic Table: 1 Mux C/D/Q Bit: 1"] = 1 if mux["select"] == 2 else 0
        elif (mux["id"] == "m18"):
            bitstream[f"CLB {data['id']} Logic Table: 2 Mux A/B"] = mux["select"]
        elif (mux["id"] == "m20"):
            bitstream[f"CLB {data['id']} Logic Table: 2 Mux B/C"] = mux["select"]
        elif (mux["id"] == "m24"):
            bitstream[f"CLB {data['id']} Logic Table: 2 Mux C/D/Q Bit: 0"] = 1 if mux["select"] == 1 else 0
            bitstream[f"CLB {data['id']} Logic Table: 2 Mux C/D/Q Bit: 1"] = 1 if mux["select"] == 2 else 0
        elif (mux["id"] == "m46"):
            bitstream[f"CLB {data['id']} Reset-Enable"] = 1 if mux["select"] != 2 else 0
            bitstream[f"CLB {data['id']} Reset D/G"] = 1 if mux["select"] == 0 else 0
        elif (mux["id"] == "m51"):
            pass
        elif (mux["id"] == "m56"):
            bitstream[f"CLB {data['id']} Set-Enable"] = 1 if mux["select"] != 2 else 0
            bitstream[f"CLB {data['id']} Set A/F"] = 1 if mux["select"] == 0 else 0
        elif (mux["id"] == "m59"):
            bitstream[f"CLB {data['id']}.Y G"] = 1 if mux["select"] == 0 else 0
            bitstream[f"CLB {data['id']}.Y F/M or Q"] = 1 if mux["select"] == 2 else 0
        elif (mux["id"] == "m61"):
            bitstream[f"CLB {data['id']}.X G"] = 1 if mux["select"] == 0 else 0
            bitstream[f"CLB {data['id']}.X F/M or Q"] = 1 if mux["select"] == 2 else 0
        elif (mux["id"] == "m100"):

            pass

        
    return bitstream

def parse_switches(data) -> dict[str, int]:
    bitstream = {}

    ## Load in the CSV from XC2064-spreadsheet
    bitstream_csv = open("XC2064-spreadsheet.csv", "r").readlines()
    
    magics = []
    magic_strs = []
    for line in bitstream_csv:
        for part in line.split(","):
            if part.startswith("Magic"):
                magic_strs.append(part.strip())
                magics.append(part.strip()[:-4])
        
    ## Reduce magics to only unique values
    magics = list(set(magics))
    
    magic_objs = []
    for magic in magics:
        _temp = {}
        parts = magic.split(" ")
        parts = parts[2].split("G")
        _temp["id"] = magic
        _temp["x"] = int(parts[0])
        _temp["y"] = int(parts[1])
        magic_objs.append(_temp)
        
    ## Sort magics by x, then y
    magic_objs.sort(key=lambda m: (m["x"], m["y"]))
    
    switches = data["switchMatrices"]
    switches.sort(key=lambda m: (m["pos"]["x"], m["pos"]["y"]))
    
    ## Rotate switches by 180 degrees
    min_x = min(switch["pos"]["x"] for switch in switches)
    max_y = max(switch["pos"]["y"] for switch in switches)
    for switch in switches:
        switch["pos"]["x"] = -min_x + switch["pos"]["x"]
        switch["pos"]["y"] = max_y - switch["pos"]["y"]
        
    for switch, magic in zip(switches, magic_objs):
        for i, row in enumerate(switch["connections"]):
            for j, connected in enumerate(row):
                magic_str = f"{magic['id']} {i+1} {j+1}"
                if magic_str in magic_strs:
                    bitstream[magic_str] = 1 if connected else 0
    return bitstream

def parse_pips(data) -> dict[str, int]:
    pips_sim = data["pips"]
    bitstream = {}
    
    ## Load in the CSV from XC2064-spreadsheet
    bitstream_csv = open("XC2064-spreadsheet.csv", "r").readlines()
    
    pips = []
    for line in bitstream_csv:
        for part in line.split(","):
            if part.startswith("PIP"):
                pips.append(part)
    
    
    pip_objs = []
    for pip in pips:
        # print(pip)
        _temp = {}
        parts = pip.split("  ")
        parts = parts[1].split("G")
        _temp["id"] = pip
        _temp["x"] = int(parts[0])
        _temp["y"] = int(parts[1])
        pip_objs.append(_temp)
        
    ## Sort magics by x, then y
    pip_objs.sort(key=lambda m: (m["y"], m["x"]))

    ## import the mapping json object
    coord_map = json.load(open("coordinate_mapping.json", "r"))

    for pip in tqdm(pip_objs):
        new_x = coord_map["x_mappings"].get(str(pip["x"]), pip["x"])
        new_y = coord_map["y_mappings"].get(str(pip["y"]), pip["y"])
        
        for sim_pip in pips_sim:
            if sim_pip["pos"]["x"] == new_x and sim_pip["pos"]["y"] == new_y:
                bitstream[pip["id"]] = 1 if sim_pip["enabled"] else 0
                break
        
        if pip["id"] not in bitstream:
            print("unable to find pip for", pip["id"], "at", new_x, new_y)

    return bitstream
    
    
def generate_bitstream(data) -> dict[str, int] :
    logic_cells = data["logicCells"]
    bitstream = {}


    print("Generating bitstream...")

    print("Populating Unused Bits...")
    ununsed_bits = {
        "----- NOT USED -----": -1
    }
    bitstream.update(ununsed_bits)

    print("Parsing CLBs...")
    for clb in tqdm(logic_cells):
        clb_bitstream = parse_clb(clb)
        bitstream.update(clb_bitstream)
    
    print("Parsing Switches...")
    switch_bitstream = parse_switches(data)
    bitstream.update(switch_bitstream)
    
    print("Parsing PIPs...")
    pip_bitstream = parse_pips(data)
    bitstream.update(pip_bitstream)

    return bitstream
    




def generate_spreadsheet(mapping_sheet: openpyxl.Workbook, bitstream: dict[str, int], filename: str) -> openpyxl.Workbook:
    sheet = mapping_sheet.active

    print("Writing Bitstream")
    
    bit_count = 0
    for key, value in tqdm(bitstream.items()):
        if DEBUG:
            print(key, value)

        # if key is in a cell in the sheet, colour that cell green
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value == key:
                    fill_colour = "00FF00"
                    if (value == -1):
                        fill_colour = "000000"


                    cell.fill = openpyxl.styles.PatternFill(start_color=fill_colour, end_color=fill_colour, fill_type="solid")
                    bit_count += 1

    print(f"Num bits: {bit_count} / 11358 ({bit_count/11358*100:.2f}%)")
    
    return mapping_sheet












if __name__ == "__main__":
    FILENAME = "sim_out.json"
    
    # import file
    with open(FILENAME, "r") as f:
        # parse to json
        data = json.load(f)
    
    # get bitstream
    bitstream = generate_bitstream(data)

    # generate speadsheet
    ## import mapping sheet from XC2064-spreadsheet
    mapping_sheet = openpyxl.load_workbook("XC2064-bits.xlsx")

    mapping_sheet = generate_spreadsheet(mapping_sheet, bitstream, "sim_out.xlsx")

    # save spreadsheet
    mapping_sheet.save("XC2064_output.xlsx")