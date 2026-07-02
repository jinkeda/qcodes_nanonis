# Variable-Length Command Argument Validation Plan

## Decision

Add pre-send validation for variable-length Nanonis command arguments.

The validation must use explicit relationships declared in the command schema. It must not assume that the nearest preceding integer always describes the following value: several commands share one count across multiple arrays, string arrays have both an encoded byte size and an item count, and matrices have two dimensions.

Also treat the current `Marks.PointsGet` response decoding as a live bug, not merely a future cleanup. Its explicit field relationships should be fixed early, before the full response-catalog migration is complete.

No implementation changes are part of this plan.

## Current variable-length types

The command catalog contains these variable-length wire types:

| Raw type | Runtime type | Current send usage |
|---|---|---:|
| `s` | `string` | 48 fields in 36 commands |
| `1D array float32` | `array_float32` | 18 fields |
| `1D array int` | `array_int32` | 10 fields |
| `1D array string` | `array_string` | 5 fields |
| `1D array unsigned int32` | `array_uint32` | 3 fields |
| `1D array unsigned int8` | `array_uint8` | 1 field |
| `1D array float64` | `array_float64` | response-only currently |
| `2D array float32` | `matrix_float32` | response-only currently |
| `2D array string` | `matrix_string` | response-only currently |

Scalar strings are encoded as a 32-bit UTF-8 byte length followed by the UTF-8 bytes. Numeric arrays and matrices have no embedded dimensions; the encoder writes only their raw elements. Each element in a string array has its own string-length prefix, but the array still depends on external item-count and, where declared, aggregate-byte-size fields.

On the response side, 57 commands contain 108 array or matrix fields, including 13 matrix fields. This is a larger and more heterogeneous annotation task than the 19-command send-side catalog and must be planned and tested separately.

## Send commands containing arrays

There are 19 send commands containing externally sized arrays:

| Command | Required relationship |
|---|---|
| `BiasSpectr.ChsSet` | `Number of channels == len(Channel indexes)` |
| `BiasSpectr.MLSValsSet` | `Number of segments` applies to all seven following parallel arrays |
| `DataLog.ChsSet` | Channel count applies to channel indexes |
| `DataLog.PropsSet` | Module-list encoded byte size and module count apply to module strings |
| `DigLines.Pulse` | Digital-line size applies to the `uint8` array |
| `GenSwp.AcqChsSet` | Channel count applies to indexes; names byte size and names count apply to names |
| `HSSwp.AcqChsSet` | Channel count applies to indexes |
| `HSSwp.SaveOptionsSet` | Module names encoded byte size and count apply to names |
| `Marks.LinesDraw` | One line count applies to five parallel arrays |
| `Marks.PointsDraw` | Point count applies to X, Y, text, and color; text size is a separate encoded-byte-size field |
| `Pattern.CloudSet` | One point count applies to X and Y |
| `Piezo.HystValsSet` | Four independent count/array pairs |
| `Scan.BufferSet` | Channel count applies to indexes |
| `Scan.PropsSet` | Module names encoded byte size and count apply to names |
| `Script.ChsSet` | Channel count applies to indexes |
| `Script.LUTLoad` | LUT values size applies to the float array |
| `Signals.ValsGet` | Signal-index count applies to indexes |
| `TCPLog.ChsSet` | Channel count applies to indexes |
| `ZSpectr.ChsSet` | Channel count applies to indexes |

The immediate-predecessor rule is therefore not universally valid:

- `Marks.LinesDraw` has one count followed by five arrays.
- `BiasSpectr.MLSValsSet` has one count followed by seven arrays.
- `Marks.PointsDraw` combines a shared item count with a separate string-array byte size.
- A string array commonly has two preceding integers: total encoded byte size and item count.
- A matrix requires rows and columns rather than one length.

## Scalar strings

The runtime registry removes redundant explicit scalar-string size rows because the string codec calculates the UTF-8 byte length itself.

The raw definitions contain eight such redundant pairs:

- `Marks.PointDraw`: text
- `Script.Autosave`: folder path and basename
- `Util.SessionPathSet`
- `Util.SettingsLoad`
- `Util.SettingsSave`
- `BiasSpectr.Start`
- `ZSpectr.Start`

There are seven bullets but eight pairs because `Script.Autosave` contributes two independent pairs.

These sizes should not be exposed as user arguments. The serializer is authoritative because it knows the actual encoded byte length.

## Current validation gap

`NanonisController.send()` currently performs:

```text
registry lookup -> encoder.encode(...) -> TCP send
```

There is no relationship validation between arguments. The encoder checks the number of arguments and whether each value can be encoded, but it does not compare a declared array length with the actual data.

For example:

```python
ctrl.send("Scan.BufferSet", 3, [0, 1], 256, 256)
```

This serializes successfully. Nanonis may interpret `256`, the pixel count, as the missing third channel index and shift every remaining field.

The request header's total body length remains correct, but the internal command body is malformed. Consequences can include:

- a Nanonis command error;
- subsequent fields being interpreted as array elements;
- truncated or trailing command data;
- incorrect parameter values;
- timeouts or connection disruption, depending on server behavior.

Strict validation of the existing positional API cannot reject a correctly formed call: every explicit mismatch it would reject already produces a malformed wire body. The compatibility effect is therefore to convert existing silent corruption into an early, descriptive exception.

## Existing response-decoding bug

`Marks.PointsGet` is currently decoded incorrectly by the generic trailing-integer heuristic:

- `Number of points` is the item count shared by X, Y, text, color, and visibility arrays.
- `Text size` is the encoded byte size of the text string-array payload.
- The current decoder uses `Text size` as the text item count because it is the nearest preceding integer.
- The color and visibility arrays also bind to `Text size` rather than `Number of points`.

Calls that retrieve drawn point marks can consequently return garbage or raise a protocol error. Add an explicit regression fixture and correct these bindings as soon as the constraint model can represent them; do not wait for all 57 response commands to be annotated.

## Recommended ownership

Use three cooperating responsibilities:

1. The registry/schema layer declares size and shape relationships explicitly.
2. The command/controller layer infers or validates derived values immediately before encoding.
3. The serialization layer enforces local structural rules such as array dimensionality, rectangular matrices, and UTF-8 byte sizing.

The main validation should not live in workflows because direct controller calls would bypass it. The TCP layer lacks command and type context.

Relationships must not be inferred from argument names or adjacency. The response decoder's current preceding-integer heuristic is also vulnerable to fields such as those in `Marks.PointsGet`, where text byte size becomes the nearest integer before later arrays.

## Constraint storage and field namespace

Store relationship metadata in a separate overlay, proposed as `configs/command_constraints.json`, outside `configs/commands/`.

The per-module files in `configs/commands/` are generated by `generate_nanonis_tcp.py`. Although `--existing` can preserve complete existing payloads when their runtime wire shapes match, a regenerated shape change replaces the payload with freshly parsed PDF data. Embedding hand-maintained constraints there would therefore risk silent loss. A separate overlay keeps generated protocol extraction separate from curated semantic relationships.

The overlay should:

- be keyed by canonical command name and by `send` or `recv` side;
- reference sanitized runtime field names, such as `num_channels`, consistently;
- be loaded only after the raw fields have been sanitized by the registry;
- be covered by lint checks that every command and field reference resolves;
- reject duplicate sanitized names within one command side;
- reject conflicting constraints globally;
- enforce complete array-field coverage only at the rollout boundary for the applicable side: send coverage at the end of Phase 2 and receive coverage at the end of Phase 3.

Using sanitized names makes constraints operate in the same namespace as `CommandDefinition` and avoids coupling the validator to display text from the PDF. The registry must nevertheless detect if two original names sanitize to the same runtime name.

## Interim response-decoding rule

The migration between Phase 1 and Phase 3 will temporarily contain both explicitly constrained and legacy response commands. Apply an all-or-nothing rule per command side:

- If a command's `recv` side has no constraints, continue using the legacy trailing-integer heuristic until that command is migrated.
- If a command's `recv` side has any constraint, constraints must cover every array and matrix field on that `recv` side.
- Once constrained, that command must use only resolved constraints for array and matrix sizing; it must never fall back to the heuristic for an uncovered field.

A per-command lint must enforce this rule immediately. This permits phased migration while preventing a command from being decoded partly by explicit relationships and partly by positional inference.

## Proposed schema representation

Add declarative constraints through the overlay and attach the resolved constraints to each `CommandDefinition` at registry-load time.

One count and one array:

```json
"constraints": [
  {
    "field": "num_channels",
    "equals": {"length": "channel_indexes"}
  }
]
```

One count shared by parallel arrays:

```json
{
  "field": "number_of_lines",
  "equals_lengths": [
    "start_x",
    "start_y",
    "end_x",
    "end_y",
    "color"
  ]
}
```

String-array count and encoded byte size:

```json
[
  {
    "field": "modules_names_number",
    "equals": {"length": "modules_names"}
  },
  {
    "field": "modules_names_size",
    "equals": {"encoded_byte_size": "modules_names"}
  }
]
```

Support at least these relationship kinds:

- element count;
- UTF-8 byte length;
- encoded string-array byte size;
- matrix row count;
- matrix column count;
- one shared count for multiple parallel arrays.

For a string array, calculate encoded byte size as:

```python
sum(4 + len(item.encode("utf-8")) for item in values)
```

This differs from both the item count and the number of Unicode characters. It matches the current codec convention, but it must be treated as provisional until verified against the protocol PDF and with at least one live Nanonis round trip. Do not enable strict byte-size inference for `Scan.PropsSet`, `DataLog.PropsSet`, or related commands until that verification passes.

## Public API and mismatch policy

Recommended behavior:

- In a new named-argument API, omit derived fields and infer them automatically.
- Preserve the current positional `send()` API for compatibility, but strictly validate explicitly supplied counts.
- If a caller supplies a contradictory value, raise an error before sending.
- Do not silently correct an explicitly supplied mismatch.
- Do not merely warn and send a known malformed command.
- Keep `send_raw()` as the explicit unvalidated escape hatch.

Example inferred call:

```python
ctrl.send_fields(
    "Scan.BufferSet",
    channel_indexes=[0, 1],
    pixels=256,
    lines=256,
)
```

The command layer would insert `num_channels=2`.

Legacy positional use remains valid:

```python
ctrl.send("Scan.BufferSet", 2, [0, 1], 256, 256)
```

It should raise a command-specific exception if the explicit count is not `2`.

Automatic inference is not the same as silently correcting an explicit value: omitted derived values are calculated, while contradictory supplied values are treated as caller errors.

## Additional structural checks

The validator should reject:

- negative sizes;
- counts outside the declared integer type's range;
- multidimensional data passed to a 1D array field;
- ragged matrices;
- a scalar string passed as an `array_string`;
- unequal parallel-array lengths;
- incorrect string-array encoded byte sizes;
- iterators or generators that are consumed during validation and then encoded differently.

Variable iterables should be materialized once. The same materialized value must be used for validation and serialization.

Zero-length values should be supported where the individual Nanonis command permits them. String sizes must always use encoded UTF-8 bytes rather than Python character counts.

No current send command contains a matrix. Send-side matrix row/column inference can therefore be deferred until a send command requires it. Response matrices remain part of the response annotation and decoder work.

## Implementation strategy

### Phase 1: Constraint foundation and urgent decode fix

1. Define the separate constraints-overlay format and sanitized-name namespace.
2. Add resolved constraint metadata to `CommandDefinition`.
3. Add global lint tests for command resolution, field resolution, sanitized-name uniqueness, and conflicting relationships.
4. Add the per-command all-or-nothing receive-constraint lint for any command that has begun migration.
5. Fully annotate every array in `Marks.PointsGet`, add a binary regression fixture, and fix its X, Y, text, color, and visibility decoding through explicit relationships.

### Phase 2: Send-side validation

1. Annotate all 19 array-bearing send commands.
2. At the end of this phase, enable a global send-side coverage lint requiring every send array field to have complete, unambiguous size metadata.
3. Add a command-argument materializer/validator called by `NanonisController.send()` immediately before `CommandEncoder.encode()`.
4. Add a dedicated exception containing the command, size field, data field, expected value, and actual value.
5. Retain strict validation for the positional compatibility API.
6. Add a named-argument sending API in which derived size fields are omitted by default.
7. Verify string-array aggregate-byte-size semantics against the PDF and real hardware before enabling those constraints strictly.
8. Test zero-length data, Unicode, NumPy inputs, shared counts, dual string-array sizes, and mismatches.

### Phase 3: Complete response migration

1. Classify all 57 response commands and 108 array/matrix fields against the protocol PDF.
2. Explicitly distinguish element counts, encoded byte sizes, shared counts, rows, and columns.
3. At the end of this phase, enable a global response-side coverage lint mirroring the send-side lint.
4. Add representative binary fixtures for every relationship category and regression fixtures for exceptional layouts.
5. Replace the generic trailing-integer heuristic only when every response array and matrix has an explicit resolved relationship.

The response annotation and fixture work is estimated at two to four focused engineer-days, excluding access delays for live hardware. The estimate should be revised after auditing the first module because ambiguity in the PDF, rather than the number of JSON edits, is the main cost.

## Final recommendation

Infer size and count values when they are omitted by an ergonomic command API. Validate values when callers explicitly supply them. Raise before sending on every mismatch, and never knowingly send a mismatch through the typed command API.

The validation belongs at the command boundary, backed by declarative registry metadata and supported by structural serializer checks.
