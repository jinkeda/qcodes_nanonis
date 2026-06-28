# Legacy

Pre-refactor code, kept for reference and the working manual terminal. **Not**
part of the `src/nanonis` package and not covered by the test suite.

| File | Purpose |
|------|---------|
| `terminal.py` | PyQt5 GUI to send raw Nanonis commands manually |
| `Nanonis_ipinstrumentbase.py` | QCoDeS `IPInstrument` driver used by the terminal |
| `Nanonis_ipinstrument.py` | Older instrument wrapper (uses a relative import; orphaned) |
| `nanonis_tcp.json` | Legacy command definitions (the refactored package uses `configs/*.yaml`) |
| `sigma.json` | Connection config (`IP-Adress`, `Port`) read by the driver |

## Running the terminal

Requires `qcodes`, `PyQt5`, `numpy` and a Nanonis TCP server reachable at the
`IP-Adress`/`Port` in `sigma.json` (default `127.0.0.1:6501`):

```bash
python legacy/terminal.py
```

The driver loads `nanonis_tcp.json` and `sigma.json` from this same directory,
so keep these files together.
