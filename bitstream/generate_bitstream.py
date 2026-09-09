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

def neighbour_clb(clb_id: str, dir: str) -> str:
    row_letter = clb_id[0]
    col_letter = clb_id[1]
    
    if dir == "N":
        if row_letter == "A":
            raise ValueError("Cannot move north from row A")
        
        row_letter = chr(ord(row_letter) - 1)
    elif dir == "S":
        if row_letter == "H":
            raise ValueError("Cannot move south from row H")
        
        row_letter = chr(ord(row_letter) + 1)
    elif dir == "E":
        if col_letter == "H":
            raise ValueError("Cannot move east from column H")
        
        col_letter = chr(ord(col_letter) + 1)
    elif dir == "W":
        if col_letter == "A":
            raise ValueError("Cannot move west from column A")
        
        col_letter = chr(ord(col_letter) - 1)
    
    return f"{row_letter}{col_letter}"

def parse_clb(data, fabric) -> dict[str, int]:
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
            if mux["select"] == 0:
                bitstream[f"CLB {data['id']}"] = 0
            elif mux["select"] == 1:
                bitstream[f"CLB {data['id']}"] = 1
            elif mux["select"] == 2:
                bitstream[f"CLB {data['id']}"] = 0
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
            if mux["select"] == 0:
                bitstream[f"CLB {data['id']} CLK Invert"] = 1
                bitstream[f"CLB {data['id']} CLK enable"] = 1
            elif mux["select"] == 1:
                bitstream[f"CLB {data['id']} CLK Invert"] = 0
                bitstream[f"CLB {data['id']} CLK enable"] = 1
            elif mux["select"] == 2:
                bitstream[f"CLB {data['id']} CLK Invert"] = 0
                bitstream[f"CLB {data['id']} CLK enable"] = 0

    
    bitstream[f"CLB {data['id']}.C MuxBit: 0"] = 0
    bitstream[f"CLB {data['id']}.C MuxBit: 1"] = 0
    bitstream[f"CLB {data['id']}.C MuxBit: 2"] = 0
    bitstream[f"CLB {data['id']}.C MuxBit: 3"] = 0
    bitstream[f"CLB {data['id']}.C MuxBit: 4"] = 0

    bitstream[f"CLB {data['id']}.K MuxBit: 0"] = 0
    bitstream[f"CLB {data['id']}.K MuxBit: 1"] = 0

    bitstream[f"CLB {data['id']}.B MuxBit: 0"] = 0
    bitstream[f"CLB {data['id']}.B MuxBit: 1"] = 0
    bitstream[f"CLB {data['id']}.B MuxBit: 2"] = 0
    bitstream[f"CLB {data['id']}.B MuxBit: 3"] = 0
    bitstream[f"CLB {data['id']}.B MuxBit: 4"] = 0
    bitstream[f"CLB {data['id']}.B MuxBit: 5"] = 0

    bitstream[f"CLB {data['id']}.A MuxBit: 0"] = 0
    bitstream[f"CLB {data['id']}.A MuxBit: 1"] = 0
    bitstream[f"CLB {data['id']}.A MuxBit: 2"] = 0
    bitstream[f"CLB {data['id']}.A MuxBit: 3"] = 0

    bitstream[f"CLB {data['id']}.D MuxBit: 0"] = 0
    bitstream[f"CLB {data['id']}.D MuxBit: 1"] = 0
    bitstream[f"CLB {data['id']}.D MuxBit: 2"] = 0
    bitstream[f"CLB {data['id']}.D MuxBit: 3"] = 0
  

    ## Pips for the I/O Ports
    for pip in fabric["pips"]:
        # K <- Global Clk
        if pip["id"] == f"{data['id']}.pip_clk":
            bitstream[f"CLB {data['id']}.K MuxBit: 1"] = 1 if pip["enabled"] else 0
            continue
        
        # K <- Left side global vertical long line 
        if pip["id"] == f"{data['id']}.pip_v2_0_6":
            bitstream[f"CLB {data['id']}.K MuxBit: 0"] = 1 if pip["enabled"] else 0
            continue
        
        # CX
        try:
            if pip["id"] == f"{neighbour_clb(data['id'], 'S')}.pip_22":
                bitstream[f"CLB {data['id']}.C MuxBit: 4"] = 0 if pip["enabled"] else 1
                continue
        except ValueError:
            pass

        # C1
        if pip["id"] == f"{data['id']}.pip_8":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.C MuxBit: 0"] = 1
                bitstream[f"CLB {data['id']}.C MuxBit: 1"] = 1
            continue

        # C2
        if pip["id"] == f"{data['id']}.pip_9":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.C MuxBit: 1"] = 1
            continue

        # C3
        if pip["id"] == f"{data['id']}.pip_10":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.C MuxBit: 0"] = 1
                bitstream[f"CLB {data['id']}.C MuxBit: 4"] = 0
            continue

        # C4
        if pip["id"] == f"{data['id']}.pip_11":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.C MuxBit: 0"] = 1
                bitstream[f"CLB {data['id']}.C MuxBit: 3"] = 1
            continue

        # C5
        if pip["id"] == f"{data['id']}.pip_v2_0_21":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.C MuxBit: 3"] = 1
            continue

        # C6
        if pip["id"] == f"{data['id']}.pip_v2_0_3":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.C MuxBit: 2"] = 1
            continue

        # C7
        if pip["id"] == f"{data['id']}.pip_v2_0_4":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.C MuxBit: 0"] = 1
                bitstream[f"CLB {data['id']}.C MuxBit: 2"] = 1
            continue

        # B1
        if pip["id"] == f"{data['id']}.pip_4_1":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.B MuxBit: 0"] = 1
                bitstream[f"CLB {data['id']}.B MuxBit: 4"] = 1
            continue
        
        # B2
        if pip["id"] == f"{data['id']}.pip_5":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.B MuxBit: 0"] = 1
                bitstream[f"CLB {data['id']}.B MuxBit: 1"] = 1
            continue

        # B3
        if pip["id"] == f"{data['id']}.pip_6":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.B MuxBit: 5"] = 0
            continue

        # B4
        if pip["id"] == f"{data['id']}.pip_7":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.B MuxBit: 3"] = 1
            continue
        
        # B5
        if pip["id"] == f"{data['id']}.pip_v2_0_20":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.B MuxBit: 3"] = 1
                bitstream[f"CLB {data['id']}.B MuxBit: 0"] = 1
            continue
        
        # B6
        if pip["id"] == f"{data['id']}.pip_v2_0":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.B MuxBit: 0"] = 1
                bitstream[f"CLB {data['id']}.B MuxBit: 2"] = 1
            continue
        
        # B7
        if pip["id"] == f"{data['id']}.pip_v2_0_1":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.B MuxBit: 2"] = 1
            continue
        
        # BC
        if pip["id"] == f"{data['id']}.pip_v2_0_2":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.B MuxBit: 1"] = 1
            continue
        
        # BX
        try:
            if pip["id"] == f"{neighbour_clb(data['id'], 'N')}.pip_21_2":
                if pip["enabled"]:
                    bitstream[f"CLB {data['id']}.B MuxBit: 0"] = 1
                    bitstream[f"CLB {data['id']}.B MuxBit: 5"] = 0

                continue
        except ValueError:
            pass
        
        # BY
        try:
            if pip["id"] == f"{neighbour_clb(data['id'], 'W')}.pip_21_3":
                if pip["enabled"]:
                    bitstream[f"CLB {data['id']}.B MuxBit: 4"] = 1
                    bitstream[f"CLB {data['id']}.B MuxBit: 0"] = 1

                continue
        except ValueError:
            pass

        # A1
        if pip["id"] == f"{data['id']}.pip_0":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.A MuxBit: 2"] = 1
            continue
        
        # A2
        if pip["id"] == f"{data['id']}.pip_1":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.A MuxBit: 3"] = 0
            continue
        
        # A3
        if pip["id"] == f"{data['id']}.pip_2":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.A MuxBit: 1"] = 1
                bitstream[f"CLB {data['id']}.A MuxBit: 0"] = 1
            continue
        
        # A4
        if pip["id"] == f"{data['id']}.pip_3":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.A MuxBit: 2"] = 1
                bitstream[f"CLB {data['id']}.A MuxBit: 0"] = 1
            continue
        
        # A5
        if pip["id"] == f"{data['id']}.pip_4":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.A MuxBit: 3"] = 0
                bitstream[f"CLB {data['id']}.A MuxBit: 0"] = 1
            continue
        
        # AX
        try:
            if pip["id"] == f"{neighbour_clb(data['id'], 'W')}.pip_21_1":
                if pip["enabled"]:
                    bitstream[f"CLB {data['id']}.B MuxBit: 1"] = 1

                continue
        except ValueError:
            pass

        #D1
        if pip["id"] == f"{data['id']}.pip_12":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.D MuxBit: 2"] = 1
            continue

        #D2
        if pip["id"] == f"{data['id']}.pip_13":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.D MuxBit: 3"] = 0
            continue

        #D3
        if pip["id"] == f"{data['id']}.pip_14":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.D MuxBit: 1"] = 1
                bitstream[f"CLB {data['id']}.D MuxBit: 0"] = 1
            continue

        #D4
        if pip["id"] == f"{data['id']}.pip_15":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.D MuxBit: 2"] = 1
                bitstream[f"CLB {data['id']}.D MuxBit: 0"] = 1
            continue

        #D5
        if pip["id"] == f"{data['id']}.pip_v2_0_5":
            if pip["enabled"]:
                bitstream[f"CLB {data['id']}.D MuxBit: 3"] = 0
                bitstream[f"CLB {data['id']}.D MuxBit: 0"] = 1
            continue

        #DX
        try:
            if pip["id"] == f"{neighbour_clb(data['id'], 'S')}.pip_20":
                if pip["enabled"]:
                    bitstream[f"CLB {data['id']}.D MuxBit: 1"] = 1
    
                continue
        except ValueError:
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
        
    ## Sort pips by x, then y
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
            
    ## Do the same for the bidi's
    bidis = []
    for line in bitstream_csv:
        for part in line.split(","):
            if part.startswith("Bidi"):
                bidis.append(part)
    bidi_objs = []
    for bidi in bidis:
        _temp = {}
        parts = bidi.split(" ")
        parts = parts[1].split("G")
        _temp["id"] = bidi
        _temp["x"] = int(parts[0])
        _temp["y"] = int(parts[1])
        bidi_objs.append(_temp)
        
    ## Sort bidis by x, then y
    bidi_objs.sort(key=lambda m: (m["y"], m["x"]))
    
    for bidi in tqdm(bidi_objs):
        ##TODO : Implement bidirectional pip parsing - I HAVE NO CLUE WHAT THE BIDI LINES ARE
        bitstream[bidi["id"]] = 0
        
        
        

    return bitstream

def parse_io_banks(data) -> dict[str, int]:
    bitstream = {}
    io_banks = data["ioBanks"]

    coord_map = json.load(open("coordinate_mapping.json", "r"))

    for bank in io_banks:
        mapped_id = coord_map["io_mappings"].get(str(bank["id"]), bank["id"])
        bitstream[f"IOB {mapped_id}.I PAD/Latched"] = bank["muxes"][1]['select']

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
        clb_bitstream = parse_clb(clb, data)
        bitstream.update(clb_bitstream)
    
    print("Parsing Switches...")
    switch_bitstream = parse_switches(data)
    bitstream.update(switch_bitstream)
    
    print("Parsing PIPs...")
    pip_bitstream = parse_pips(data)
    bitstream.update(pip_bitstream)

    print("Parsing IO Banks...")
    io_bitstream = parse_io_banks(data)
    bitstream.update(io_bitstream)

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