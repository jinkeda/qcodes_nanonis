# qcodes_nanonis modernization blueprint

**Baseline reviewed:** `main` at commit `645cbb8`  
**Scope:** Nanonis TCP/QCoDeS control, measurement workflows, safety, testing, and operator-facing tools  
**Primary objective:** turn the current research prototype into reliable measurement software without losing direct access to the Nanonis command set.

## 1. Executive assessment

The repository already contains the most important low-level asset: a metadata-driven Nanonis TCP codec that can translate catalogue-defined commands into binary messages and decode structured responses. The current high-level driver also demonstrates useful laboratory operations such as channel reads, auto approach, coarse motion, Z regulation, scan control, and early bias-spectroscopy support.

The main problem is not the absence of functionality. It is that protocol transport, command metadata, QCoDeS parameters, safety decisions, multi-step workflows, configuration, and user-interface code are still coupled in a flat source layout. This makes behavior difficult to test without hardware and makes failure handling too implicit for unattended measurements.

The modernization should therefore preserve the existing codec and command catalogue while placing them below a typed, testable, safety-aware workflow layer.

## 2. Current repository model

### 2.1 Implemented components

| Component | Current file | Responsibility |
|---|---|---|
| Nanonis transport and codec | `Nanonis_ipinstrumentbase.py` | TCP connection, command parsing, request encoding, response decoding, and error handling |
| QCoDeS Nanonis adapter | `Nanonis_ipinstrument.py` | QCoDeS parameters and microscope convenience operations |
| Command catalogue | `nanonis_tcp.json` | Runtime argument and response definitions |
| Local configuration | `sigma.json` | TCP endpoint and coarse-motion constants |
| Catalogue generator | `generate_nanonis_tcp.py` | Extract and normalize command definitions from the vendor PDF |
| Command terminal | `terminal.py` | PyQt5 interface for direct command dispatch |
| Magnet driver | `Lakeshore_model625.py` | QCoDeS VISA driver and blocking field ramp |

### 2.2 Current data flow

```text
operator / notebook / terminal
            |
            v
NanonisIPInstrument
QCoDeS parameters + procedural helper methods
            |
            v
NanonisIPInstrumentbase
parse -> validate count -> encode -> send -> receive -> decode
            |
            +-----------------------+
            |                       |
            v                       v
    nanonis_tcp.json            sigma.json
            |
            v
      Nanonis TCP server
```

### 2.3 Strengths worth preserving

- The command catalogue keeps most protocol details out of handwritten methods.
- `_recv_exactly` avoids partial-read assumptions.
- Scalar, string, one-dimensional array, and selected two-dimensional response types are supported.
- Existing QCoDeS parameters provide a practical bridge to datasets and measurement scripts.
- The command generator creates a path for tracking future Nanonis protocol releases.
- The repository contains real laboratory workflow knowledge that should be extracted rather than rewritten from scratch.

### 2.4 Immediate technical risks

1. **Packaging inconsistency.** The source is flat, the high-level driver uses a relative import, and the terminal uses a top-level import. There is no `pyproject.toml` or stable package boundary.
2. **Insufficient safety separation.** Methods such as `stepper` make hardware-safety decisions directly inside the instrument class.
3. **Untestable hardware coupling.** Socket I/O is embedded in the codec/instrument object, so workflows cannot be exercised against a deterministic fake transport.
4. **Weak failure semantics.** `ask_raw` can return raw bytes after a decoding failure, allowing malformed catalogue entries to escape typed handling.
5. **Blocking-loop defects.** Blocking scan logic uses inconsistent references to the imported `time` module and requires timeout/cancellation tests.
6. **Catalogue fragility.** Array decoding depends on the exact order of preceding length, row, and column fields.
7. **Configuration ambiguity.** Connection settings, motion constants, and future safety limits are not validated by a typed schema.
8. **No automated verification.** There are no unit tests, integration tests, CI checks, simulation fixtures, or hardware-in-the-loop profiles.
9. **Mixed responsibilities.** Nanonis, Lakeshore, UI, PDF parsing, configuration, and measurement operations share one repository level.
10. **No stable result model.** Multi-step measurements return dictionaries or side effects rather than validated immutable results with metadata.

## 3. Target architecture

```text
┌───────────────────────────────────────────────────────────────┐
│ Applications                                                  │
│ notebooks | CLI | optional GUI | experiment orchestration     │
└──────────────────────────────┬────────────────────────────────┘
                               v
┌───────────────────────────────────────────────────────────────┐
│ Workflows                                                     │
│ bias spectroscopy | Z spectroscopy | scan | pattern | stepper  │
│ typed config -> preflight -> transaction -> validated result   │
└──────────────────────────────┬────────────────────────────────┘
                               v
┌───────────────────────────────────────────────────────────────┐
│ Safety and domain services                                    │
│ SafetyPolicy | state snapshots | limits | cleanup | audit log  │
└──────────────────────────────┬────────────────────────────────┘
                               v
┌───────────────────────────────────────────────────────────────┐
│ Instrument adapters                                           │
│ NanonisController | Lakeshore625 | QCoDeS parameter adapters   │
└──────────────────────────────┬────────────────────────────────┘
                               v
┌───────────────────────────────────────────────────────────────┐
│ Protocol core                                                 │
│ command catalogue | typed command specs | codec | exceptions   │
└──────────────────────────────┬────────────────────────────────┘
                               v
┌───────────────────────────────────────────────────────────────┐
│ Transport                                                     │
│ SocketTransport | RecordingTransport | FakeTransport           │
└───────────────────────────────────────────────────────────────┘
```

### 3.1 Proposed package layout

```text
qcodes_nanonis/
├── pyproject.toml
├── README.md
├── src/
│   └── qcodes_nanonis/
│       ├── __init__.py
│       ├── config/
│       │   ├── models.py
│       │   └── loader.py
│       ├── protocol/
│       │   ├── catalogue.py
│       │   ├── codec.py
│       │   ├── command.py
│       │   ├── errors.py
│       │   └── transport.py
│       ├── instruments/
│       │   ├── nanonis.py
│       │   ├── nanonis_qcodes.py
│       │   └── lakeshore_625.py
│       ├── subsystems/
│       │   ├── bias.py
│       │   ├── signals.py
│       │   ├── z_controller.py
│       │   ├── scan.py
│       │   ├── motor.py
│       │   └── spectroscopy.py
│       ├── safety/
│       │   ├── policy.py
│       │   ├── limits.py
│       │   ├── state.py
│       │   └── transaction.py
│       ├── workflows/
│       │   ├── common.py
│       │   ├── bias_spectroscopy.py
│       │   ├── z_spectroscopy.py
│       │   ├── scan.py
│       │   ├── stepper.py
│       │   └── pattern.py
│       ├── results/
│       │   ├── spectroscopy.py
│       │   └── scan.py
│       └── cli/
│           └── terminal.py
├── data/
│   └── nanonis_tcp.json
├── tools/
│   └── generate_nanonis_tcp.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── hardware/
└── reports/
    └── blueprint.md
```

### 3.2 Dependency rules

- `protocol` must not import QCoDeS, GUI libraries, or workflow modules.
- `transport` must be replaceable without changing the codec or workflows.
- `instruments` may depend on `protocol`, configuration models, and domain exceptions.
- `subsystems` expose coherent Nanonis feature groups; they must not contain experiment-specific sequencing.
- `safety` owns limits, preconditions, state snapshots, and cleanup policy.
- `workflows` coordinate subsystems and safety services but do not encode raw TCP messages.
- QCoDeS adapters wrap the same controller/subsystem API used by non-QCoDeS applications.
- UI and notebooks depend only on public workflow/instrument interfaces.

## 4. Core design decisions

### 4.1 Separate transport from protocol encoding

Define a minimal transport interface:

```python
from typing import Protocol


class Transport(Protocol):
    def request(self, payload: bytes) -> bytes:
        ...

    def close(self) -> None:
        ...
```

Required implementations:

- `SocketTransport`: real Nanonis TCP connection;
- `FakeTransport`: scripted request/response behavior for unit and workflow tests;
- `RecordingTransport`: wraps another transport and records command traffic for debugging and reproducibility.

The codec should accept bytes and metadata and should not know whether the response came from hardware, a fixture, or a replay file.

### 4.2 Replace untyped catalogue dictionaries with validated models

At load time, convert JSON records into immutable command specifications:

```python
@dataclass(frozen=True)
class FieldSpec:
    name: str
    type_code: str


@dataclass(frozen=True)
class CommandSpec:
    name: str
    arguments: tuple[FieldSpec, ...]
    responses: tuple[FieldSpec, ...]
```

Catalogue validation must reject:

- unsupported type codes;
- duplicate field names;
- arrays without a valid preceding count/dimension field;
- inconsistent command names;
- ambiguous string-length definitions;
- legacy records that cannot be normalized safely.

Generation from PDF remains a tool. Generated output is not promoted to runtime data until validation and review pass.

### 4.3 Use typed exceptions

Replace generic `RuntimeError` and raw-byte fallback behavior with an exception hierarchy:

```text
QcodesNanonisError
├── ConfigurationError
├── CatalogueError
├── ProtocolEncodeError
├── ProtocolDecodeError
├── TransportError
├── NanonisCommandError
├── SafetyViolation
├── WorkflowTimeout
└── WorkflowCancelled
```

Raw responses may be attached to exceptions for diagnostics, but a method declared to return a mapping must never silently return bytes.

### 4.4 Keep QCoDeS as an adapter, not the domain model

The controller API should work independently of QCoDeS:

```python
bias = controller.bias.get()
controller.bias.set(0.100)
```

The QCoDeS layer then exposes these operations as parameters. This allows protocol and workflow tests to run without creating QCoDeS instruments or datasets.

### 4.5 Separate shared sweep mechanics from measurement-specific semantics

Bias spectroscopy and Z spectroscopy should **share a common sweep/acquisition engine**, but remain separate workflow modules.

Shared engine responsibilities:

- point generation and direction;
- forward/backward and repeated sweeps;
- dwell and settling times;
- channel selection and aligned acquisition;
- progress, timeout, and cancellation;
- state snapshots and cleanup;
- timestamps and run metadata.

Separate workflow responsibilities:

| Bias spectroscopy | Z spectroscopy |
|---|---|
| bias limits and ramp policy | Z displacement/absolute-position limits |
| feedback behavior around bias sweep | feedback-off and tip-height preconditions |
| bias-specific Nanonis commands | Z-specific movement/acquisition commands |
| bias-axis result metadata | Z-axis reference and displacement metadata |
| current/compliance checks | crash prevention and minimum-clearance checks |

Do not merge both into one large `spectroscopy()` function with mode flags. Use a shared internal engine and distinct typed configurations/results.

## 5. Safety model

### 5.1 Required invariants

The safety layer must enforce at least the following:

- bias is within configured absolute and slew-rate limits;
- current setpoint is within configured polarity and magnitude limits;
- Z target is within controller limits and experiment-specific clearance limits;
- coarse motion is forbidden unless scanning is stopped and the tip is confirmed withdrawn;
- auto approach has a timeout and explicit terminal states;
- every polling loop supports timeout and cancellation;
- magnet ramps are bounded by field, ramp-rate, current, voltage, and quench state;
- failure cleanup is deterministic and recorded;
- safety limits cannot be relaxed implicitly by a workflow.

### 5.2 Transactional workflow pattern

Every hardware-changing workflow should follow:

```text
validate configuration
        -> acquire exclusive run lock
        -> capture initial state
        -> evaluate safety preconditions
        -> execute bounded operations
        -> validate acquired data
        -> create immutable result
        -> restore configured final state
        -> release lock
```

On exceptions:

```text
classify failure
        -> execute best-effort safe cleanup
        -> record cleanup outcome
        -> raise typed workflow exception with original cause
```

A cleanup failure must not replace the original failure; both must remain visible.

### 5.3 State snapshots

A snapshot should include the subset relevant to the workflow:

- bias;
- current setpoint;
- feedback state;
- Z position and limits;
- scan status/direction/frame;
- lock-in state and modulation settings;
- selected channels;
- magnetic field and supply status where applicable.

Restoration policy must be explicit: `restore_initial`, `leave_final`, or a named safe state.

## 6. Configuration and result models

Use frozen dataclasses or a validated equivalent for user-facing configurations.

Example:

```python
@dataclass(frozen=True)
class BiasSpectroscopyConfig:
    start: float
    stop: float
    points: int
    sweeps: int = 1
    backward: bool = False
    channels: tuple[str, ...] = ()
    settle_time: float = 0.0
    timeout: float = 120.0
    restore_bias: bool = True
```

Validation belongs at construction or preflight, not halfway through a measurement.

Results should be immutable and self-describing:

```python
@dataclass(frozen=True)
class SpectroscopyResult:
    axis_name: str
    axis_unit: str
    axis: np.ndarray
    channels: Mapping[str, np.ndarray]
    started_at: datetime
    completed_at: datetime
    configuration: object
    initial_state: object
    final_state: object
    command_log_id: str | None
```

Result validation must confirm shape agreement, finite axes where required, channel uniqueness, and acquisition completeness.

## 7. Milestones

### M0 — Baseline documentation and risk register

**Status:** documentation update in progress.

Deliverables:

- accurate README describing the current source snapshot;
- this blueprint;
- explicit list of known safety and packaging limitations;
- no claims that deleted notebooks, missing dependency files, or unavailable APIs exist.

Exit criteria:

- a new developer can distinguish implemented behavior from planned behavior;
- high-risk operations are clearly marked as experimental.

### M1 — Package foundation

Deliverables:

- `pyproject.toml` using a `src/` layout;
- consistent imports and public API;
- dependency groups for runtime, GUI, development, and hardware tests;
- formatted, linted, typed baseline;
- migration of JSON data into package resources;
- deprecation wrappers for old import paths where practical.

Exit criteria:

- `pip install -e .` works on a clean environment;
- `python -c "import qcodes_nanonis"` succeeds;
- terminal and basic protocol examples run from the installed package.

### M2 — Protocol core extraction

Deliverables:

- transport interface and socket implementation;
- immutable command/field specifications;
- catalogue validation;
- codec split from instrument lifecycle;
- typed exceptions;
- removal of silent raw-byte return paths.

Exit criteria:

- protocol tests run without QCoDeS or hardware;
- golden request/response fixtures cover every supported type;
- malformed catalogues fail at startup with actionable errors.

### M3 — Controller and subsystem API

Deliverables:

- `NanonisController` composed from bias, signals, Z, scan, motor, lock-in, and spectroscopy subsystems;
- thin QCoDeS adapter;
- consistent units, naming, validation, and return types;
- bounded blocking operations with timeout and cancellation.

Exit criteria:

- current high-level operations are available through stable subsystem interfaces;
- no workflow constructs raw command strings directly.

### M4 — Safety policy and transaction framework

Deliverables:

- typed laboratory safety configuration;
- state snapshots;
- run lock;
- preflight checks;
- cleanup/restore policies;
- structured command and state-transition logging.

Exit criteria:

- unsafe coarse-motion sequences are rejected before hardware writes;
- injected failures demonstrate deterministic cleanup;
- all blocking loops terminate by completion, timeout, or cancellation.

### M5 — Spectroscopy workflows

Deliverables:

- shared sweep engine;
- production bias-spectroscopy workflow;
- production Z-spectroscopy workflow;
- typed configurations and immutable validated results;
- QCoDeS dataset integration kept outside the acquisition core.

Exit criteria:

- both workflows pass fake-transport success, timeout, cancellation, and cleanup tests;
- result arrays and metadata are validated before return;
- workflows can be run with or without QCoDeS storage.

### M6 — Scan, stepper, and pattern workflows

Deliverables:

- validated scan frame geometry;
- safe scan state transitions;
- transactional stepper workflow;
- pattern/path planning separated from hardware execution;
- support for line, grid, snake/sneak, and future cloud acquisition paths;
- conversion utilities from acquisition order to validated image grids.

Exit criteria:

- path generation is pure and independently testable;
- no coarse movement can occur without verified retraction;
- interrupted runs preserve enough metadata to diagnose partial acquisition.

### M7 — Simulation, tests, and CI

Deliverables:

- fake and recording transports;
- unit tests for codec/catalogue/configuration;
- workflow state-machine tests;
- integration fixtures based on recorded protocol exchanges;
- optional hardware tests protected by explicit markers and environment checks;
- CI for supported Python versions, linting, typing, and tests.

Suggested quality gates:

- protocol and safety modules: at least 90% branch coverage;
- no unbounded polling loops;
- no ignored broad exceptions in hardware paths;
- deterministic tests without microscope access.

### M8 — Operator experience and release process

Deliverables:

- CLI for connection diagnostics and command inspection;
- optional GUI built on public APIs;
- API and workflow documentation;
- versioned command catalogue compatibility;
- changelog, migration guide, license, and release automation.

Exit criteria:

- tagged releases can be installed reproducibly;
- compatibility with supported Nanonis/QCoDeS versions is documented;
- operators can identify software, configuration, catalogue, and hardware versions for every run.

## 8. Migration map

| Current element | Target |
|---|---|
| `Nanonis_ipinstrumentbase.py` socket methods | `protocol/transport.py` |
| request/response conversion methods | `protocol/codec.py` |
| command-dictionary parsing | `protocol/catalogue.py` and `protocol/command.py` |
| Nanonis error parsing | `protocol/errors.py` |
| QCoDeS parameters | `instruments/nanonis_qcodes.py` |
| signal, scan, Z, motor helper methods | individual `subsystems/` modules |
| `stepper` procedural method | `workflows/stepper.py` |
| early bias-spectroscopy helpers | `workflows/bias_spectroscopy.py` |
| `terminal.py` | `cli/terminal.py` using public controller API |
| `Lakeshore_model625.py` | `instruments/lakeshore_625.py` with safety-aware ramp service |
| `sigma.json` | validated user configuration outside the package, plus a safe example file |
| `nanonis_tcp.json` | versioned package data validated at load time |
| `generate_nanonis_tcp.py` | `tools/` maintenance command with generator tests |

## 9. Near-term implementation order

The next development sequence should be:

1. Add package metadata and move files without changing behavior.
2. Build codec/catalogue unit tests around the current implementation.
3. Extract `Transport` and introduce `FakeTransport`.
4. Make decoding failures explicit and typed.
5. Split Nanonis features into subsystem interfaces.
6. Add safety configuration, snapshots, and bounded polling helpers.
7. Implement the shared sweep engine.
8. Build bias spectroscopy first, then Z spectroscopy on the same engine.
9. Move stepper/scan/pattern logic into transactional workflows.
10. Add CI and only then expand operator UI features.

This order minimizes simultaneous behavioral and structural change. Existing hardware behavior should be captured in tests before major refactoring.

## 10. Definition of production-ready measurement software

The project should not be described as production-ready until all of the following are true:

- installable, versioned package with declared dependencies;
- stable public API and documented compatibility;
- validated configuration and command catalogue;
- fake-transport test coverage for all critical workflows;
- explicit hardware limits and preflight checks;
- timeouts and cancellation for every blocking operation;
- deterministic cleanup after injected failures;
- immutable validated measurement results;
- structured run and command logging;
- hardware-in-the-loop acceptance tests for supported microscope configurations;
- release, migration, and rollback procedures.

Until then, development should optimize for **correctness, observability, and recoverability**, not merely for adding more commands.
