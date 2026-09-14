import json

## Helper function to strip the first X bits from a byte array and return the reamining array and stripped bits
def strip_bits(data: bytes, num_bits: int) -> tuple[bytes, int]:
    if num_bits == 0:
        return data, 0

    total_bits = len(data) * 8
    if num_bits > total_bits:
        raise ValueError(f"Requested {num_bits} bits but only {total_bits} available")

    # Interpret the entire byte array as a big integer (MSB-first)
    full_int = int.from_bytes(data, "big")

    # Extract the top `num_bits` bits
    stripped_bits = full_int >> (total_bits - num_bits)

    # Remaining bits as integer
    remaining_bits_count = total_bits - num_bits
    if remaining_bits_count == 0:
        remaining_bytes = b""
    else:
        remaining_int = full_int & ((1 << remaining_bits_count) - 1)
        # When remaining bits don't fill a whole byte, left-align them so the
        # next bit to read is the MSB of the first returned byte. This avoids
        # accidental rotation when strip_bits is called repeatedly.
        out_len = (remaining_bits_count + 7) // 8
        pad = out_len * 8 - remaining_bits_count
        if pad:
            remaining_int <<= pad
        remaining_bytes = remaining_int.to_bytes(out_len, "big")

    return remaining_bytes, stripped_bits


def load_xact_bitstream(filename: str) -> bytearray:
    bitstream = bytearray()
    bit_buffer = 0
    bit_pos = 0
    
    def append_bits(value, num_bits):
        nonlocal bit_buffer, bit_pos
        bit_buffer = (bit_buffer << num_bits) | value
        bit_pos += num_bits
        while bit_pos >= 8:
            bit_pos -= 8
            byte_val = (bit_buffer >> bit_pos) & 0xFF
            bitstream.append(byte_val)
            bit_buffer &= (1 << bit_pos) - 1
    
    with open(filename, "rb") as f:
        data = f.read()

    data, stripped_bits = strip_bits(data, 8)
    data, stripped_bits = strip_bits(data, 4)
    data, stripped_bits = strip_bits(data, 24)
    data, stripped_bits = strip_bits(data, 4)

    accumulator = 0

    for i in range(160):
        data, header = strip_bits(data, 1)
        accumulator += 1
        data, frame = strip_bits(data, 71)
        accumulator += 71
        data, footer = strip_bits(data, 3)
        accumulator += 3

        append_bits(frame, 71)
        
    if bit_pos > 0:
        bitstream.append((bit_buffer << (8 - bit_pos)) & 0xFF)
    
    return bitstream
    

def load_bitstream_names(filename: str, bits) -> dict[int, str]:
    bit_names: dict[str, int] = {}

    with open(filename, "r", encoding="utf-8") as f:
        # read csv rows (simple CSV parsing - file expected to be rectangular)
        rows = [line.split(",") for line in f.read().splitlines() if line.strip()]

        if not rows:
            return bit_names

        num_rows = len(rows)
        num_cols = len(rows[0])

        # iterate column-major: for each column, then each row
        for col in range(num_cols):
            for row_idx in range(num_rows):
                # guard against ragged rows
                if col >= len(rows[row_idx]):
                    continue
                name = rows[row_idx][col].strip()
                if not name:
                    continue

                bit_index = col * num_rows + row_idx
                if bit_index < len(bits):
                    bit_names[name] = bits[bit_index]

    return bit_names
    

                
import openpyxl
from tqdm import tqdm
                
def generate_spreadsheet(mapping_sheet: openpyxl.Workbook, bitstream: dict[str, int], filename: str) -> openpyxl.Workbook:
    sheet = mapping_sheet.active

    print("Writing Bitstream")

    fills = {
        1: openpyxl.styles.PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid"),
        0: openpyxl.styles.PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid"),
        -1: openpyxl.styles.PatternFill(start_color="000000", end_color="000000", fill_type="solid"),
    }
    bit_count = 0
    for row in tqdm(sheet.iter_rows()):
        for cell in row:
            value = bitstream.get(cell.value)
            if value is None:
                continue

            cell.fill = fills[value]
            bit_count += 1

    print(f"Num bits: {bit_count} / 11358 ({bit_count/11358*100:.2f}%)")
    
    return mapping_sheet

    
    
if __name__ == "__main__":
    FILENAME = 'BIG2'
    xact_bytes = load_xact_bitstream("./" + FILENAME + ".BIT")
    xact_bits = []
    for byte in xact_bytes:
        for i in range(8):
            xact_bits.append((byte >> (7 - i)) & 1)
    
    
    bitstream = load_bitstream_names("../XC2064-spreadsheet.csv", xact_bits)

    ## import mapping sheet from XC2064-spreadsheet
    mapping_sheet = openpyxl.load_workbook("XC2064-bits.xlsx")

    mapping_sheet = generate_spreadsheet(mapping_sheet, bitstream, "sim_out.xlsx")

    # save spreadsheet
    mapping_sheet.save("XC2064_output.xlsx")