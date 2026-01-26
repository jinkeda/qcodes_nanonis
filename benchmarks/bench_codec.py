"""
Benchmark suite for comparing Python vs Rust codec performance.

Run with:
    python -m benchmarks.bench_codec

Requirements:
    - nanonis_core must be built and installed (maturin develop)
"""

import timeit
import sys

# Number of iterations for each benchmark
ITERATIONS = 100_000
LARGE_ARRAY_SIZE = 1000
MATRIX_SIZE = 100


def format_time(seconds: float, iterations: int) -> str:
    """Format time per operation in human-readable units."""
    per_op = seconds / iterations
    if per_op < 1e-6:
        return f"{per_op * 1e9:.1f} ns"
    elif per_op < 1e-3:
        return f"{per_op * 1e6:.1f} us"
    else:
        return f"{per_op * 1e3:.1f} ms"


def run_benchmark(name: str, python_setup: str, python_stmt: str, 
                  rust_setup: str, rust_stmt: str, 
                  iterations: int = ITERATIONS) -> dict:
    """Run a benchmark comparing Python and Rust implementations."""
    print(f"\n{'='*60}")
    print(f"Benchmark: {name}")
    print(f"{'='*60}")
    
    # Python benchmark
    try:
        python_time = timeit.timeit(python_stmt, setup=python_setup, number=iterations)
        python_per_op = format_time(python_time, iterations)
        print(f"  Python: {python_time:.3f}s total, {python_per_op}/op")
    except Exception as e:
        print(f"  Python: FAILED - {e}")
        python_time = None
    
    # Rust benchmark
    try:
        rust_time = timeit.timeit(rust_stmt, setup=rust_setup, number=iterations)
        rust_per_op = format_time(rust_time, iterations)
        print(f"  Rust:   {rust_time:.3f}s total, {rust_per_op}/op")
    except Exception as e:
        print(f"  Rust:   FAILED - {e}")
        rust_time = None
    
    # Calculate speedup
    if python_time and rust_time:
        speedup = python_time / rust_time
        print(f"  Speedup: {speedup:.1f}x")
        return {"python": python_time, "rust": rust_time, "speedup": speedup}
    
    return {"python": python_time, "rust": rust_time, "speedup": None}


def bench_encode_float32():
    """Benchmark float32 encoding."""
    return run_benchmark(
        "encode_float32",
        python_setup="import struct",
        python_stmt="struct.pack('>f', 3.14159)",
        rust_setup="import nanonis_core",
        rust_stmt="nanonis_core.encode_float32(3.14159)",
    )


def bench_encode_float64():
    """Benchmark float64 encoding."""
    return run_benchmark(
        "encode_float64",
        python_setup="import struct",
        python_stmt="struct.pack('>d', 3.14159265358979)",
        rust_setup="import nanonis_core",
        rust_stmt="nanonis_core.encode_float64(3.14159265358979)",
    )


def bench_encode_int32():
    """Benchmark int32 encoding."""
    return run_benchmark(
        "encode_int32",
        python_setup="import struct",
        python_stmt="struct.pack('>i', 12345678)",
        rust_setup="import nanonis_core",
        rust_stmt="nanonis_core.encode_int32(12345678)",
    )


def bench_encode_string():
    """Benchmark string encoding."""
    return run_benchmark(
        "encode_string",
        python_setup="import struct; s = 'Hello, World!'",
        python_stmt="struct.pack('>I', len(s.encode('utf-8'))) + s.encode('utf-8')",
        rust_setup="import nanonis_core",
        rust_stmt="nanonis_core.encode_string('Hello, World!')",
    )


def bench_encode_array_float32():
    """Benchmark float32 array encoding (1000 elements)."""
    return run_benchmark(
        f"encode_array_float32 ({LARGE_ARRAY_SIZE} elements)",
        python_setup=f"import struct; arr = [float(i) for i in range({LARGE_ARRAY_SIZE})]",
        python_stmt="struct.pack('>I', len(arr)) + b''.join(struct.pack('>f', x) for x in arr)",
        rust_setup=f"import nanonis_core; arr = [float(i) for i in range({LARGE_ARRAY_SIZE})]",
        rust_stmt="nanonis_core.encode_array_float32(arr)",
        iterations=ITERATIONS // 10,
    )


def bench_encode_array_float64():
    """Benchmark float64 array encoding (1000 elements)."""
    return run_benchmark(
        f"encode_array_float64 ({LARGE_ARRAY_SIZE} elements)",
        python_setup=f"import struct; arr = [float(i) for i in range({LARGE_ARRAY_SIZE})]",
        python_stmt="struct.pack('>I', len(arr)) + b''.join(struct.pack('>d', x) for x in arr)",
        rust_setup=f"import nanonis_core; arr = [float(i) for i in range({LARGE_ARRAY_SIZE})]",
        rust_stmt="nanonis_core.encode_array_float64(arr)",
        iterations=ITERATIONS // 10,
    )


def bench_decode_float32():
    """Benchmark float32 decoding."""
    return run_benchmark(
        "decode_float32",
        python_setup="import struct; data = struct.pack('>f', 3.14159)",
        python_stmt="struct.unpack('>f', data)[0]",
        rust_setup="import nanonis_core; data = nanonis_core.encode_float32(3.14159)",
        rust_stmt="nanonis_core.decode_float32(data)",
    )


def bench_decode_float64():
    """Benchmark float64 decoding."""
    return run_benchmark(
        "decode_float64",
        python_setup="import struct; data = struct.pack('>d', 3.14159265358979)",
        python_stmt="struct.unpack('>d', data)[0]",
        rust_setup="import nanonis_core; data = nanonis_core.encode_float64(3.14159265358979)",
        rust_stmt="nanonis_core.decode_float64(data)",
    )


def bench_decode_string():
    """Benchmark string decoding."""
    return run_benchmark(
        "decode_string",
        python_setup="import struct; s = 'Hello, World!'; data = struct.pack('>I', len(s.encode('utf-8'))) + s.encode('utf-8')",
        python_stmt="l = struct.unpack('>I', data[:4])[0]; data[4:4+l].decode('utf-8')",
        rust_setup="import nanonis_core; data = nanonis_core.encode_string('Hello, World!')",
        rust_stmt="nanonis_core.decode_string_simple(data)",
    )


def bench_decode_array_float32():
    """Benchmark float32 array decoding (1000 elements)."""
    setup = f"""
import struct
arr = [float(i) for i in range({LARGE_ARRAY_SIZE})]
data = struct.pack('>I', len(arr)) + b''.join(struct.pack('>f', x) for x in arr)
"""
    stmt = "n = struct.unpack('>I', data[:4])[0]; struct.unpack('>' + str(n) + 'f', data[4:])"
    return run_benchmark(
        f"decode_array_float32 ({LARGE_ARRAY_SIZE} elements)",
        python_setup=setup,
        python_stmt=stmt,
        rust_setup=f"import nanonis_core; arr = [float(i) for i in range({LARGE_ARRAY_SIZE})]; data = nanonis_core.encode_array_float32(arr)",
        rust_stmt="nanonis_core.decode_array_float32(data)",
        iterations=ITERATIONS // 10,
    )


def bench_encode_matrix_float32():
    """Benchmark float32 matrix encoding (100x100)."""
    setup = f"""
import struct
mat = [[float(i*{MATRIX_SIZE}+j) for j in range({MATRIX_SIZE})] for i in range({MATRIX_SIZE})]
"""
    stmt = """
result = struct.pack('>II', len(mat), len(mat[0]))
for row in mat:
    for val in row:
        result += struct.pack('>f', val)
"""
    return run_benchmark(
        f"encode_matrix_float32 ({MATRIX_SIZE}x{MATRIX_SIZE})",
        python_setup=setup,
        python_stmt=stmt,
        rust_setup=f"import nanonis_core; mat = [[float(i*{MATRIX_SIZE}+j) for j in range({MATRIX_SIZE})] for i in range({MATRIX_SIZE})]",
        rust_stmt="nanonis_core.encode_matrix_float32(mat)",
        iterations=ITERATIONS // 100,
    )


def bench_decode_matrix_float32():
    """Benchmark float32 matrix decoding (100x100)."""
    setup = f"""
import struct
mat = [[float(i*{MATRIX_SIZE}+j) for j in range({MATRIX_SIZE})] for i in range({MATRIX_SIZE})]
data = struct.pack('>II', len(mat), len(mat[0]))
for row in mat:
    for val in row:
        data += struct.pack('>f', val)
"""
    stmt = """
rows, cols = struct.unpack('>II', data[:8])
values = struct.unpack('>' + str(rows*cols) + 'f', data[8:])
result = [list(values[i*cols:(i+1)*cols]) for i in range(rows)]
"""
    return run_benchmark(
        f"decode_matrix_float32 ({MATRIX_SIZE}x{MATRIX_SIZE})",
        python_setup=setup,
        python_stmt=stmt,
        rust_setup=f"import nanonis_core; mat = [[float(i*{MATRIX_SIZE}+j) for j in range({MATRIX_SIZE})] for i in range({MATRIX_SIZE})]; data = nanonis_core.encode_matrix_float32(mat)",
        rust_stmt="nanonis_core.decode_matrix_float32(data)",
        iterations=ITERATIONS // 100,
    )


def run_all_benchmarks():
    """Run all benchmarks and print summary."""
    print("=" * 60)
    print("NANONIS CODEC BENCHMARK SUITE")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    
    # Check if nanonis_core is available
    try:
        import nanonis_core
        print(f"nanonis_core: available")
    except ImportError:
        print("ERROR: nanonis_core not found. Run 'maturin develop' first.")
        return
    
    results = {}
    
    # Scalar encoding benchmarks
    results["encode_float32"] = bench_encode_float32()
    results["encode_float64"] = bench_encode_float64()
    results["encode_int32"] = bench_encode_int32()
    results["encode_string"] = bench_encode_string()
    
    # Scalar decoding benchmarks
    results["decode_float32"] = bench_decode_float32()
    results["decode_float64"] = bench_decode_float64()
    results["decode_string"] = bench_decode_string()
    
    # Array benchmarks
    results["encode_array_float32"] = bench_encode_array_float32()
    results["encode_array_float64"] = bench_encode_array_float64()
    results["decode_array_float32"] = bench_decode_array_float32()
    
    # Matrix benchmarks
    results["encode_matrix_float32"] = bench_encode_matrix_float32()
    results["decode_matrix_float32"] = bench_decode_matrix_float32()
    
    # Print summary table
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Operation':<35} {'Python':>10} {'Rust':>10} {'Speedup':>10}")
    print("-" * 60)
    
    for name, result in results.items():
        python_str = f"{result['python']:.3f}s" if result['python'] else "N/A"
        rust_str = f"{result['rust']:.3f}s" if result['rust'] else "N/A"
        speedup_str = f"{result['speedup']:.1f}x" if result['speedup'] else "N/A"
        print(f"{name:<35} {python_str:>10} {rust_str:>10} {speedup_str:>10}")
    
    print("=" * 60)


if __name__ == "__main__":
    run_all_benchmarks()
