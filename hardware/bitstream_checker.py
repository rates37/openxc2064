


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


## Load in and print the binary data from "SIMPLE.bin"
with open("./SIMPLE.bin", "rb") as f:
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
    data, stripped_bits = strip_bits(data, 4)
    print(f"{stripped_bits:04b}")


    # # print original data byte by byte in binary
    # print("\nOriginal data:")
    # for i, byte in enumerate(full_data):
    #     print(f"{i:04d}: {byte:08b}")   

    