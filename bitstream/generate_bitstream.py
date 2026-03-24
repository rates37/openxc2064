import json
import openpyxl
import tqdm

DEBUG = False

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

def generate_bitstream(data) -> dict[str, int]:
    logic_cells = data["logicCells"]
    bitstream = {}


    print("Generating bitstream...")

    print("Parsing CLBs...")
    for clb in tqdm.tqdm(logic_cells):
        clb_bitstream = parse_clb(clb)
        bitstream.update(clb_bitstream)




    return bitstream
    




def generate_spreadsheet(mapping_sheet: openpyxl.Workbook, bitstream: dict[str, int], filename: str) -> openpyxl.Workbook:
    sheet = mapping_sheet.active

    print("Writing Bitstream")
    for key, value in tqdm.tqdm(bitstream.items()):
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

    print(f"Num bits: {len(bitstream)} / 11358 ({len(bitstream)/11358*100:.2f}%)")
    
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
    mapping_sheet = openpyxl.load_workbook("XC2064.xlsx")

    mapping_sheet = generate_spreadsheet(mapping_sheet, bitstream, "sim_out.xlsx")

    # save spreadsheet
    mapping_sheet.save("XC2064.xlsx")