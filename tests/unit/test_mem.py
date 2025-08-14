import pytest
from pathlib import Path
from Artefact.modules import memory
import tempfile

def test_extract_strings_ascii(tmp_path):
    file = tmp_path / "mem.raw"
    file.write_bytes(b"hello\x00world\x00\x01\x02teststring123\x00")
    strings = memory.extract_strings(file, min_length=4, encodings=['ascii'])
    found_strings = [s[0] for s in strings['ascii']]
    assert any("hello" in s for s in found_strings)
    assert any("teststring123" in s for s in found_strings)

def test_extract_strings_utf16(tmp_path):
    file = tmp_path / "mem.raw"
    # 'test' in UTF-16LE: 74 00 65 00 73 00 74 00
    file.write_bytes(b"t\x00e\x00s\x00t\x00\x00\x00")
    strings = memory.extract_strings(file, min_length=2, encodings=['utf-16le'])
    assert any("test" in s[0] for s in strings['utf-16le'])

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
    # Create a minimal PE header
    # DOS header with e_lfanew pointing to PE header at offset 0x80
    dos_header = bytearray(b"MZ" + b"\x00" * 0x3a)  # First part of DOS header
    dos_header[0x3c:0x40] = (0x80).to_bytes(4, byteorder='little')  # e_lfanew
    # Fill the rest with zeros until PE header
    padding = b"\x00" * (0x80 - len(dos_header))
    # PE header at offset 0x80
    pe_header = b"PE\0\0"  # PE signature
    pe_header += b"\x4C\x01"  # Machine (x86)
    pe_header += b"\x01\x00"  # Number of sections
    pe_header += b"\x00" * 16  # Timestamp + other fields
    file_data = bytes(dos_header) + padding + pe_header
    file.write_bytes(file_data)
    
    outdir = tmp_path / "out"
    outdir.mkdir()
    memory.carve_binaries(file, outdir, types=["pe"])
    files = list(outdir.glob("*.exe"))
    assert len(files) >= 1
