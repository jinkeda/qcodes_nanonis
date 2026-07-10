# qcodes_nanonis

A research-stage Python control layer for integrating **Nanonis SPM** with the **QCoDeS** measurement framework.

The repository currently contains a metadata-driven Nanonis TCP client, a small QCoDeS instrument wrapper, a PyQt terminal, a Lakeshore 625 magnet-supply driver, and tooling that extracts command definitions from the Nanonis TCP manual.

> **Project status:** experimental laboratory software. The current code is useful for development and controlled measurements, but it is not yet packaged, simulated, comprehensively tested, or equipped with a complete hardware-safety layer. Review every command and limit against the connected microscope before use.

## Architecture today

```text
Measurement script / interactive terminal
                 |
                 v
NanonisIPInstrument
QCoDeS parameters and convenience operations
                 |
                 v
NanonisIPInstrumentbase
command parsing, binary encoding/decoding, socket I/O, error handling
                 |
          +------+------+
          |             |
          v             v
 nanonis_tcp.json    sigma.json
 command metadata    connection/configuration
                 |
                 v
        Nanonis TCP server
```

The design is **command-catalog driven**: argument and response types are loaded from `nanonis_tcp.json`, then encoded or decoded by the protocol layer at runtime.

## Implemented capabilities

### Protocol and transport

- Loads the Nanonis command catalogue and connection configuration from JSON files.
- Encodes scalar numeric types, strings, and supported one-dimensional arrays using the Nanonis big-endian TCP format.
- Receives complete TCP headers and bodies rather than assuming a single socket read is sufficient.
- Decodes scalar values, strings, one- and two-dimensional numeric arrays, and string arrays.
- Parses Nanonis error payloads and raises runtime errors for reported instrument failures.
- Supports both string-style commands such as `"Bias.Set 0.1"` and lower-level `ask_raw` / `write_raw` calls.

### QCoDeS-facing Nanonis operations

`NanonisIPInstrument` currently exposes or assists with:

- tunnelling current, current setpoint, bias, Z position, and feedback state;
- signal-name discovery and single/multiple channel reads;
- tip withdrawal and auto approach;
- coarse motor motion and repeated Z regulation;
- scan start/stop/pause/resume actions;
- waiting for scan-line completion;
- a guarded coarse-step sequence that stops scanning, retracts, moves, re-approaches, and acquires a line;
- early bias-spectroscopy property and acquisition helpers.

### Additional tools

- `terminal.py`: a small PyQt5 command terminal for sending catalogue-defined Nanonis commands.
- `generate_nanonis_tcp.py`: parses the vendor TCP protocol PDF and writes a normalized JSON command catalogue.
- `Lakeshore_model625.py`: a QCoDeS VISA driver for a Lakeshore Model 625 magnet power supply.

## Repository map

| Path | Purpose |
|---|---|
| `Nanonis_ipinstrumentbase.py` | TCP connection, command parsing, binary codec, response decoding, and error handling |
| `Nanonis_ipinstrument.py` | QCoDeS parameters and higher-level microscope operations |
| `nanonis_tcp.json` | Runtime Nanonis command metadata |
| `sigma.json` | Local TCP endpoint and coarse-motion configuration |
| `generate_nanonis_tcp.py` | Command-catalog generator based on the Nanonis protocol PDF |
| `terminal.py` | Interactive PyQt5 command terminal |
| `Lakeshore_model625.py` | Lakeshore 625 QCoDeS/VISA driver |
| `TCPProtocol_SPM.pdf` | Vendor protocol reference used by the generator |
| `reports/blueprint.md` | Current architecture assessment and staged modernization plan |

## Development setup

The repository does not yet contain a `pyproject.toml`, lock file, or authoritative dependency file. For the current source snapshot, create an isolated environment and install the libraries used by the modules you intend to run:

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install qcodes numpy PyPDF2 PyQt5 pyvisa tqdm matplotlib
```

Python 3.10 or newer is recommended.

### Current packaging limitation

The code is still stored in a flat repository layout. `Nanonis_ipinstrument.py` uses a package-relative import, while `terminal.py` uses a top-level import. Consequently, the high-level driver is not yet a reliable pip-installable package. The first milestone in the blueprint moves the source into `src/qcodes_nanonis/`, adds packaging metadata, and makes imports consistent.

## Configuration

The driver expects `nanonis_tcp.json` and `sigma.json` in the directory supplied as `configpath`.

A minimal `sigma.json` is:

```json
{
  "Interface": {
    "IP-Adress": "127.0.0.1",
    "Port": 6501
  },
  "CoarseMotionConstants": {
    "+X": 0.1,
    "-X": 0.1,
    "+Y": 0.1,
    "-Y": 0.1
  }
}
```

`IP-Adress` retains the spelling currently expected by the implementation. Do not expose the Nanonis TCP server to an untrusted network.

## Minimal protocol-level example

The protocol layer can be used directly from the repository root:

```python
from pathlib import Path

from Nanonis_ipinstrumentbase import NanonisIPInstrumentbase

config_dir = Path(__file__).resolve().parent

nanonis = NanonisIPInstrumentbase(
    name="nanonis",
    configpath=str(config_dir),
    timeout=10.0,
)

try:
    bias_response = nanonis.ask("Bias.Get")
    print(bias_response["Bias value (V)"])

    nanonis.write("Bias.Set 0.1")
finally:
    nanonis.close()
```

Before setting bias, current, feedback, scan, Z, or motor parameters, verify the intended units, sign convention, valid range, and physical state of the microscope.

## Interactive terminal

With Nanonis running and the JSON configuration files available in the repository directory:

```bash
python terminal.py
```

Example terminal input:

```text
Bias.Get
Bias.Set 0.1
Signals.ValGet 0 0
```

Only commands present in `nanonis_tcp.json` can be encoded.

## Regenerating the command catalogue

```bash
python generate_nanonis_tcp.py \
  TCPProtocol_SPM.pdf \
  nanonis_tcp_auto.json \
  --start-page 37 \
  --existing nanonis_tcp.json
```

The PDF parser is a maintenance aid, not an automatic guarantee of protocol correctness. Review generated argument order, count fields, array dimensions, and response names against the vendor manual before replacing the runtime catalogue.

## Safety principles

Until the planned safety layer is implemented, measurement scripts should enforce these rules explicitly:

1. Bound every bias, current, field, Z, and coarse-motion request.
2. Stop scanning and confirm tip withdrawal before coarse movement.
3. Give every blocking poll loop a timeout and a defined failure action.
4. Restore or leave the instrument in a known safe state after exceptions.
5. Log hardware-changing commands with sufficient context to reconstruct a run.
6. Test new workflows against a fake transport or disconnected codec before using real hardware.

## Known limitations

- No installable package metadata or stable public API.
- No automated test suite, simulator, CI workflow, or hardware-in-the-loop test profile.
- No centralized safety policy, transaction/rollback mechanism, or cancellation model.
- Command decoding depends on correct catalogue ordering and preceding size/count fields.
- Decode failures in `ask_raw` may fall back to returning raw bytes, which can hide catalogue defects from higher-level code.
- Blocking scan logic and several measurement helpers need validation and refactoring before routine unattended use.
- Configuration, protocol data, instrument drivers, workflows, and UI code are not yet separated into independent modules.

## Roadmap

See [`reports/blueprint.md`](reports/blueprint.md) for:

- the current architecture assessment;
- target package boundaries;
- safety and reliability requirements;
- the proposed shared sweep engine for bias and Z spectroscopy;
- staged milestones for packaging, testing, simulation, workflows, and releases.

## Contributing

For each change:

- keep protocol-code changes separate from measurement-policy changes;
- add unit tests for codecs, catalogue validation, and state transitions;
- document hardware assumptions and units;
- avoid unbounded loops and silent exception recovery;
- do not commit laboratory IP addresses, credentials, unpublished measurement data, or machine-specific paths.

## License

No license is currently declared. Add an explicit open-source or institutional license before redistributing the software.

## Acknowledgements

Developed by **Keda Jin** and collaborators. Built on QCoDeS and the Nanonis TCP protocol.
