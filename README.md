# QCoDeS Nanonis Interface

A Python driver layer that connects Nanonis SPM control software with the [QCoDeS](https://qcodes.github.io/Qcodes/) measurement framework.  
The package wraps the Nanonis TCP/IP protocol in higher-level abstractions so you can configure experiments, trigger scans, and collect data while staying inside a QCoDeS workflow.

## Features
- **Drop-in QCoDeS instruments** – `NanonisIPInstrument` and `NanonisIPInstrumentbase` extend `IPInstrument`, exposing signals as QCoDeS parameters.
- **Command catalogue loading** – reads the official TCP command descriptions from `nanonis_tcp.json` (or the auto-generated variant) and sigma configuration.
- **Robust encoding/decoding** – handles strings, scalars, and array payloads according to the Nanonis protocol, including error parsing.
- **Higher-level utilities** – helpers for bias spectroscopy, coarse motion, scan control, Z regulation, and TCP diagnostics.
- **Generation tooling** – `generate_nanonis_tcp.py` extracts protocol metadata into JSON, keeping the driver in sync with new Nanonis releases.
- **Interactive examples** – `demo.ipynb` demonstrates typical measurement flows and can serve as a starting point for lab notebooks.

## Getting Started
1. **Clone the repository**
   ```bash
   git clone https://github.com/jinkeda/qcodes_nanonis.git
   cd qcodes_nanonis
   ```
2. **Install dependencies**  
   A minimal environment requires:
   - Python 3.10+
   - `qcodes`
   - `numpy`
   - `ipykernel` / `jupyter` (for the notebook demo)

   Install with pip:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate         # Use `source .venv/bin/activate` on Unix
   pip install -r requirements.txt  # If you create one
   ```
   or install packages manually:
   ```bash
   pip install qcodes numpy jupyter
   ```

3. **Configure Nanonis connection**
   - Copy your lab-specific configuration JSONs (`nanonis_tcp.json`, `sigma.json`, etc.) into the repository directory or update paths accordingly.
   - Ensure the target Nanonis system exposes the TCP interface and that the IP/port in `sigma.json` matches your setup.

4. **Instantiate the instrument**
   ```python
   from Nanonis_ipinstrument import NanonisIPInstrument

   nanonis = NanonisIPInstrument(
       name="nanonis",
       configpath="C:/path/to/configs",
       timeout=10.0,
   )

   print(nanonis.bias())        # Read the current bias
   nanonis.bias.set(0.5)        # Set new bias
   print(nanonis.It.get())      # Read tunneling current
   ```

## Repository Structure
- `Nanonis_ipinstrumentbase.py` – core TCP encoder/decoder, logging, and response parsing.
- `Nanonis_ipinstrument.py` – QCoDeS instrument exposing measurement parameters and scan helpers.
- `generate_nanonis_tcp.py` – script to build `nanonis_tcp_auto.json` from upstream protocol docs.
- `demo.ipynb` – example Jupyter notebook demonstrating common tasks.
- `terminal.py`, `_tmp_inspect*.py` – assorted utilities used during development/testing.
- `TCPProtocol_SPM.pdf` – vendor documentation for the TCP protocol.

## Development Workflow
- Run `generate_nanonis_tcp.py` when the protocol changes to refresh command definitions.
- Use `pytest` or custom scripts for regression testing of command encoders/decoders.
- Before contributing, format code with `black` or your preferred formatter and run linting if available.

## License
No license has been provided yet. When you are ready to share the project publicly, add a license statement here (e.g., MIT, BSD, or proprietary notice).

## Acknowledgements
Developed by **Keda Jin** and collaborators. Built on top of QCoDeS and the Nanonis TCP protocol.
