# Variable-Length Command Validation Walkthrough

## Outcome

The typed Nanonis command path now validates every cataloged variable-length send argument before opening a TCP transaction. It can also infer derived sizes through a named-field API.

Response decoding no longer relies on the nearest preceding integer for catalog commands. All 57 response commands containing arrays or matrices use explicit size relationships, including the previously broken `Marks.PointsGet` layout.

The implementation covers:

- 19 array-bearing send commands;
- 57 array-bearing response commands;
- 108 response array or matrix fields;
- 13 response matrix fields;
- element counts, shared counts, encoded string-array byte sizes, rows, and columns.

## Constraint catalog

Curated relationships live in:

```text
configs/command_constraints.json
```

This file is intentionally outside `configs/commands/`. The per-module command files are generated from the protocol PDF and can be replaced when their wire shapes change. Keeping constraints in a separate overlay prevents regeneration from silently deleting curated relationships.

Constraints use sanitized runtime field names. A typical numeric-array relationship is:

```json
"Scan.BufferSet": {
  "send": {
    "channel_indexes": {"count": "num_channels"}
  }
}
```

String arrays declare both their element count and aggregate encoded byte size:

```json
"Scan.PropsSet": {
  "send": {
    "modules_names": {
      "count": "modules_names_number",
      "byte_size": "modules_names_size"
    }
  }
}
```

Matrices identify both dimensions:

```json
"Scan.FrameDataGrab": {
  "recv": {
    "scan_data": {
      "rows": "scan_data_rows",
      "columns": "scan_data_columns"
    }
  }
}
```

## Registry loading and linting

`CommandRegistry.load_from_dir()` loads the generated command files first, then looks for `command_constraints.json` in their parent directory.

If a loaded catalog contains an array or matrix and the overlay is missing, loading now fails with `FileNotFoundError`. This prevents deployed installations from silently returning to heuristic decoding. Intentionally unconstrained custom schemas can opt out explicitly:

```python
registry.load_from_dir(path, require_constraints=False)
```

The controller exposes the same explicit opt-out as `NanonisController(..., require_constraints=False)` for legacy custom catalogs.

During loading, the registry verifies:

- field names remain unique after sanitization;
- overlay command names exist;
- overlay field references exist on the correct command side;
- size fields are integer types;
- array constraints declare a count;
- matrix constraints declare rows and columns;
- `byte_size` is used only with string arrays;
- a constrained command side covers every one of its arrays or matrices;
- the complete catalog overlay covers all send and receive variable fields.

The resolved relationships are attached to each `CommandDefinition` as `send_constraints` and `recv_constraints`.

## Positional sending

The existing positional API remains available:

```python
controller.send("Scan.BufferSet", 2, [0, 1], 256, 128)
```

Immediately before serialization, `CommandArgumentValidator` materializes variable iterables and compares the explicit values with the resolved constraints.

This malformed call now raises `NanonisArgumentError` before anything is sent:

```python
controller.send("Scan.BufferSet", 3, [0, 1], 256, 128)
```

The exception identifies:

- the command;
- the size field;
- the corresponding data field;
- the expected value;
- the supplied value.

An explicitly supplied mismatch is never silently corrected and is never sent with only a warning.

Exact integral real counts such as `2.0` remain accepted for compatibility with the previous NumPy integer coercion. Non-integral values are rejected instead of being truncated.

## Named-field sending and inference

`NanonisController.send_fields()` provides the inferred-size API:

```python
controller.send_fields(
    "Scan.BufferSet",
    channel_indexes=[0, 1],
    pixels=256,
    lines=128,
)
```

The controller derives `num_channels=2`, restores the command's wire-order argument tuple, validates it, and passes it to the normal encoder and TCP path.

Callers may still provide a derived field explicitly:

```python
controller.send_fields(
    "Scan.BufferSet",
    num_channels=2,
    channel_indexes=[0, 1],
    pixels=256,
    lines=128,
)
```

If the explicit value is wrong, the same pre-send exception is raised.

Transport controls use underscore-prefixed names so they cannot shadow protocol fields:

```python
controller.send_fields(
    "HSSwp.Start",
    wait_until_done=1,
    timeout=10,      # HSSwp protocol field
    _timeout=15.0,   # TCP transaction timeout
    _check_error=True,
)
```

The registry also lints the catalog against these reserved control names.

Shared counts are checked against every target. For example, all five arrays in `Marks.LinesDraw` must have `num_lines` elements, and all seven segment arrays in `BiasSpectr.MLSValsSet` must have `num_segments` elements.

## String-array sizes

The April 2025 protocol manual specifies that a one-dimensional string array has:

- a separate aggregate size in bytes;
- a separate number of elements;
- a length prefix before each string element.

The implemented aggregate calculation matches the existing codec wire format:

```python
sum(4 + len(item.encode("utf-8")) for item in values)
```

`send_fields()` therefore derives both values for commands such as `DataLog.PropsSet`, `HSSwp.SaveOptionsSet`, and `Scan.PropsSet`.

UTF-8 byte length is used rather than Python character count. `str` and `bytes` elements are accepted; other element types are rejected.

## Structural serializer checks

The encoder now defensively rejects malformed local values even when it is used directly:

- numeric 1D array types require exactly one dimension;
- numeric matrix types require exactly two dimensions;
- string arrays reject a scalar `str` or `bytes` value;
- string arrays and matrices accept only `str` or `bytes` elements;
- string matrices must be rectangular.

The command validator additionally:

- rejects negative or out-of-range derived integer sizes;
- rejects unequal parallel arrays;
- materializes generators once so validation and serialization see identical data;
- rejects multidimensional data for 1D fields and ragged string matrices.

`send_raw()` remains the explicit escape hatch for intentionally unvalidated bodies.

## Response decoding

`NanonisController.send()` passes the command's resolved receive constraints to `CommandDecoder`.

For a numeric array, the decoder reads its element count from the named constraint field. For a matrix, it reads the named row and column fields. For a string array, it also compares the bytes consumed while decoding the elements with the declared aggregate byte size.

Generic standalone decoder use without constraints retains the legacy preceding-integer behavior for compatibility. Catalog commands do not use that fallback because the overlay has complete receive coverage.

### `Marks.PointsGet` correction

The response layout contains:

```text
Number of points
X array
Y array
Text byte size
Text string array
Color array
Visible array
```

Previously, the nearest-integer heuristic interpreted `Text byte size` as the text item count and then reused it for color and visibility. The explicit relationships now specify:

```text
len(X)       = Number of points
len(Y)       = Number of points
len(Text)    = Number of points
bytes(Text)  = Text byte size
len(Color)   = Number of points
len(Visible) = Number of points
```

A binary regression fixture covers UTF-8 text followed by color and visibility arrays, ensuring that all trailing fields remain aligned.

## Tests and verification

The new test module covers:

- exact catalog coverage counts;
- mandatory-overlay failure and its explicit opt-out;
- positional mismatch rejection before TCP send;
- named-field count inference;
- the `HSSwp.Start.timeout` keyword-collision regression;
- shared-count consistency;
- compatibility with integral floating-point counts;
- UTF-8 string-array byte-size inference;
- one-time generator materialization;
- direct encoder dimension checks;
- consistent command-layer errors for ragged numeric input;
- correct `Marks.PointsGet` decoding;
- response byte-size mismatch rejection;
- all-or-nothing command-side constraints;
- sanitized-name collision detection.

Verification results:

```text
ruff check src/nanonis/command tests/test_variable_length_validation.py
All checks passed

pytest -q
294 passed
```

The protocol PDF was inspected locally and confirms the string-array framing used by the implementation. No live command was sent to physical Nanonis hardware during this implementation. A non-destructive `Scan.PropsGet`/`Scan.PropsSet` round trip remains recommended before the next live measurement session; it can verify both string-array aggregate byte sizing and the element-count interpretation of `size_of_num_parameters_per_module_array`.

## Files changed

```text
configs/command_constraints.json
src/nanonis/command/registry.py
src/nanonis/command/validation.py
src/nanonis/command/exceptions.py
src/nanonis/command/controller.py
src/nanonis/command/encoder.py
src/nanonis/command/__init__.py
tests/test_variable_length_validation.py
reports/variable_length_argument_validation_plan.md
reports/variable_length_argument_validation_walkthrough.md
```
