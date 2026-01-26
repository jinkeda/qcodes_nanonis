$ErrorActionPreference = "Stop"

$env:CARGO_INCREMENTAL = "0"
$env:RUSTFLAGS = "-C debuginfo=0"
$env:CARGO_PROFILE_TEST_DEBUG = "0"
$env:CARGO_PROFILE_DEV_DEBUG = "0"
$env:CARGO_TARGET_DIR = Join-Path $env:TEMP "nanonis_core_target"

Push-Location (Join-Path $PSScriptRoot "..\\nanonis_core")
try {
    cargo test
} finally {
    Pop-Location
}
