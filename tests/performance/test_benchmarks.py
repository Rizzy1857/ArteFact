import time

import pytest

from Artefact.modules.hasher import hash_file
from Artefact.modules.memory import extract_strings


@pytest.mark.performance
def test_streaming_hash_throughput(tmp_path):
    sample = tmp_path / "sample.bin"
    size = 32 * 1024 * 1024
    sample.write_bytes(b"A" * size)
    started = time.perf_counter()
    digest = hash_file(sample)
    elapsed = time.perf_counter() - started
    assert len(digest) == 64
    assert size / max(elapsed, 0.001) > 5 * 1024 * 1024


@pytest.mark.performance
def test_memory_string_extraction_is_bounded(tmp_path):
    sample = tmp_path / "sample.raw"
    sample.write_bytes((b"printable-string\x00\x01" * 250_000))
    started = time.perf_counter()
    result = extract_strings(sample, encodings=["ascii"])
    elapsed = time.perf_counter() - started
    assert result["ascii"]
    assert elapsed < 15
