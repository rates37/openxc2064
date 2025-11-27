import csv
import re
import os

def main():
    input_file = 'XC2064-def.txt'
    output_file = 'XC2064-spreadsheet.csv'
    
    # Get absolute path if needed, assuming script is in the same dir as txt file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, input_file)
    output_path = os.path.join(script_dir, output_file)

    print(f"Reading from {input_path}")

    # Read lines
    with open(input_path, 'r') as f:
        lines = f.readlines()
    
    # Filter lines that start with "Bit:"
    data_lines = [line.strip() for line in lines if line.strip().startswith('Bit:')]
    
    print(f"Found {len(data_lines)} lines starting with 'Bit:'.")
    
    expected_count = 160 * 71
    if len(data_lines) != expected_count:
        print(f"Warning: Expected {expected_count} lines, but found {len(data_lines)}.")
    
    rows = 71
    cols = 160
    
    # Initialize grid
    grid = [['' for _ in range(cols)] for _ in range(rows)]
    
    for i, line in enumerate(data_lines):
        if i >= rows * cols:
            break
        
        # Parse line to get description
        # Format: Bit:    0  ----- NOT USED -----
        # We want the part after the bit number.
        match = re.match(r'Bit:\s+[0-9A-Fa-f]+\s+(.*)', line)
        content = line
        if match:
            content = match.group(1)
        
        # Calculate position
        # Top to bottom, then left to right
        # i=0 -> (0,0), i=1 -> (1,0), ... i=70 -> (70,0), i=71 -> (0,1)
        c = i // rows
        r = i % rows
        
        if c < cols:
            grid[r][c] = content
            
    # Write to CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(grid)
        
    print(f"Spreadsheet written to {output_path}")

if __name__ == '__main__':
    main()
