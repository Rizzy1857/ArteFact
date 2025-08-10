import pytest
from pathlib import Path
from Artefact.modules import memory
import tempfile

def test_extract_strings_ascii(tmp_path):
    file = tmp_path / "mem.raw"
    file.write_bytes(b"hello\x00world\x00\x01\x02teststring123\x00")
    strings = memory.extract_strings(file, min_length=4, encoding='ascii')
    assert any("hello" in s for s in strings)
    assert any("teststring123" in s for s in strings)

def test_extract_strings_utf16(tmp_path):
    file = tmp_path / "mem.raw"
    # 'test' in UTF-16LE: 74 00 65 00 73 00 74 00
    file.write_bytes(b"t\x00e\x00s\x00t\x00\x00\x00")
    strings = memory.extract_strings(file, min_length=2, encoding='utf16')
    assert any("test" in s for s in strings)

def test_extract_iocs():
    strings = [
        "Contact admin@example.com or visit http://example.com",
        "Suspicious IP: 192.168.1.1",
        "IPv6: fe80::1ff:fe23:4567:890a"
    ]
    iocs = memory.extract_iocs(strings)
    assert any("192.168.1.1" in s for s in iocs['ipv4'])
    assert any("fe80::1ff:fe23:4567:890a" in s for s in iocs['ipv6'])
    assert any("http://example.com" in s for s in iocs['url'])
    assert any("admin@example.com" in s for s in iocs['email'])

def test_carve_binaries(tmp_path):
    file = tmp_path / "mem.raw"
    # Add a fake PE header
    file.write_bytes(b"MZ" + b"A"*100)
    outdir = tmp_path / "out"
    outdir.mkdir()
    memory.carve_binaries(file, outdir, types=["pe"])
    files = list(outdir.glob("*.exe"))
    assert len(files) >= 1
