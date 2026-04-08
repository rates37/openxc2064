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

## Generate an intel format hex file from the binary data in "SIMPLE.bin"
def generate_hex_file(input_file: str, output_file: str):
    with open(input_file, "rb") as f:
        data = f.read()

    with open(output_file, "w") as f:
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_chunk = chunk.hex().upper()
            # Intel HEX format: :<byte count><address><record type><data><checksum>
            byte_count = len(chunk)
            address = i
            record_type = 0
            # Sum of byte count, address hi, address lo, record type and data bytes
            checksum = byte_count + (address >> 8) + (address & 0xFF) + record_type
            for j in range(0, len(hex_chunk), 2):
                checksum += int(hex_chunk[j:j+2], 16)
            # Intel HEX checksum is two's complement of LSB of sum
            checksum = ((~checksum + 1) & 0xFF)
            f.write(f":{byte_count:02X}{address:04X}{record_type:02X}{hex_chunk}{checksum:02X}\n")
        f.write(":00000001FF\n")  # End of file record


FILENAME = 'AND_OR'
## Load in and print the binary data from "SIMPLE.bin"
with open("./bitstreams/" + FILENAME + ".BIT", "rb") as f:
    data = f.read()
    full_data = data
    # Strip the first 8 bits
    data, stripped_bits = strip_bits(data, 8)
    print(f"{stripped_bits:08b}")

    data, stripped_bits = strip_bits(data, 4)
    print(f"{stripped_bits:04b}")

    data, stripped_bits = strip_bits(data, 24)
    print(f"{stripped_bits:024b} [{stripped_bits:x}] [{stripped_bits:d}]")

    data, stripped_bits = strip_bits(data, 4)
    print(f"{stripped_bits:04b}")

    accumulator = 0

    for i in range(160):
        data, header = strip_bits(data, 1)
        accumulator += 1
        data, frame = strip_bits(data, 71)
        accumulator += 71
        data, footer = strip_bits(data, 3)
        accumulator += 3

        print(f"Frame {i:03d}: {header:01b} {frame:071b} {footer:03b}")
        
    print(f"Total bits processed: {accumulator}")
    data, stripped_bits = strip_bits(data, 45)
    print(f"{stripped_bits:04b}")

    generate_hex_file("./bitstreams/" + FILENAME + ".BIT", "./rom_outputs/" + FILENAME + ".HEX")
    # # print original data byte by byte in binary
    # print("\nOriginal data:")
    # for i, byte in enumerate(full_data):
    #     print(f"{i:04d}: {byte:08b}")   

    