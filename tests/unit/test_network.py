import socket
import struct
from pathlib import Path

from Artefact.modules.network import (analyze_pcap, extract_http_objects,
                                      parse_pcap, reconstruct_sessions)


def _pcap(path: Path, payload=None) -> None:
    payload = payload or b"GET http://example.com/ HTTP/1.1\r\nHost: example.com\r\n\r\n"
    ethernet = b"\x00" * 12 + b"\x08\x00"
    total = 20 + 20 + len(payload)
    ip = (b"\x45\x00" + struct.pack("!H", total) + b"\x00\x01\x00\x00\x40\x06\x00\x00" +
          socket.inet_aton("192.0.2.1") + socket.inet_aton("198.51.100.2"))
    tcp = struct.pack("!HHII", 12345, 80, 0, 0) + b"\x50\x18\x20\x00\x00\x00\x00\x00"
    frame = ethernet + ip + tcp + payload
    global_header = b"\xd4\xc3\xb2\xa1" + struct.pack("<HHIIII", 2, 4, 0, 0, 65535, 1)
    record = struct.pack("<IIII", 1_700_000_000, 0, len(frame), len(frame)) + frame
    path.write_bytes(global_header + record)


def test_parse_and_analyze_pcap(tmp_path):
    capture = tmp_path / "sample.pcap"
    _pcap(capture)
    packets = parse_pcap(capture)
    assert len(packets) == 1
    assert packets[0].protocol == "tcp"
    assert packets[0].destination_port == 80
    sessions = reconstruct_sessions(packets)
    assert sessions[0]["packets"] == 1
    result = analyze_pcap(capture)
    assert result["protocols"] == {"tcp": 1}
    assert "http://example.com/" in result["iocs"]["url"]


def test_rejects_non_pcap(tmp_path):
    path = tmp_path / "bad.pcap"
    path.write_bytes(b"not a capture")
    try:
        parse_pcap(path)
    except ValueError as exc:
        assert "header" in str(exc)
    else:
        raise AssertionError("invalid capture accepted")


def test_http_extraction_and_threat_feed(tmp_path):
    capture = tmp_path / "response.pcap"
    _pcap(capture, b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 5\r\n\r\nhello")
    extracted = extract_http_objects(parse_pcap(capture), tmp_path / "objects")
    assert len(extracted) == 1
    assert extracted[0].read_bytes() == b"hello"
    feed = tmp_path / "feed.json"
    feed.write_text('{"ipv4": ["192.0.2.1"]}', encoding="utf-8")
    result = analyze_pcap(capture, feed)
    assert result["threat_matches"]["ipv4"] == ["192.0.2.1"]
