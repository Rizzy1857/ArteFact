"""Repeatable core benchmark runner; outputs machine-readable JSON."""

import json
import tempfile
import time
from pathlib import Path

from Artefact.modules.hasher import hash_file
from Artefact.modules.memory import extract_strings


def measure(name, operation):
    started = time.perf_counter()
    result = operation()
    return {"name": name, "seconds": time.perf_counter() - started, "result_count": len(result)}


def main():
    with tempfile.TemporaryDirectory(prefix="artefact-benchmark-") as directory:
        root = Path(directory)
        sample = root / "sample.raw"
        sample.write_bytes((b"ArteFact benchmark string\x00" * 400_000))
        results = [
            measure("sha256", lambda: hash_file(sample)),
            measure("ascii_strings", lambda: extract_strings(sample, encodings=["ascii"])["ascii"]),
        ]
        print(json.dumps({"input_bytes": sample.stat().st_size, "benchmarks": results}, indent=2))


if __name__ == "__main__":
    main()
