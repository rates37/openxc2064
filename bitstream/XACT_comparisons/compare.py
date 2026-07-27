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


def load_xact_bitstream(filename: str) -> dict[str, int]:
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
    

def load_bitstream_names(filename: str) -> dict[int, str]:
    bit_names = []
    with open(filename, "r") as f:
        ## load csv rows
        rows = f.read().splitlines()
        
        ## append to the list, column first, then rows
        for col in range(len(rows[0].split(","))):
            for row in rows:
                bit_names.append(row.split(",")[col].strip())
        
    return bit_names
    
    
if __name__ == "__main__":
    FILENAME = 'COUNTER'
    xact_bytes = load_xact_bitstream("./" + FILENAME + ".BIT")
    xact_bits = []
    for byte in xact_bytes:
        for i in range(8):
            xact_bits.append((byte >> (7 - i)) & 1)
    
    
    bit_names = load_bitstream_names("../XC2064-spreadsheet.csv")
    
    [print(name, " | ", xact_bits[i]) for i, name in enumerate(bit_names)]