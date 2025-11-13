# openxc2064
An open-source toolchain and development platform for the Xilinx XC2064, the first FPGA.

## Getting Started / Setup

### Installation

This project uses [uv](https://docs.astral.sh/uv/) for package management. If you don't have uv installed, you can install it using the [official uv install guide](https://docs.astral.sh/uv/getting-started/installation/).

### Setup

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/rates37/openxc2064.git
cd openxc2064
```

Install the project dependencies:

```bash
uv sync
```

### Running Tests

Run the test suite with pytest:

```bash
uv run pytest
```

### Running Code

To run Python scripts in this project with the correct environment:

```bash
uv run python <script.py>
```

To run an interactive Python repl with the correct environment:

```bash
uv run python
>>> from openxc2064 import *
```
