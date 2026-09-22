"""Dependency-free PCAP analysis for common Ethernet/IP traffic."""

import ipaddress
import socket
import struct
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple


@dataclass(frozen=True)
class Packet:
    timestamp: datetime
    source: str
    destination: str
    protocol: str
    source_port: Optional[int]
    destination_port: Optional[int]
    length: int
    payload: bytes = b""


def _pcap_records(path: Path) -> Iterator[Tuple[datetime, bytes]]:
    with Path(path).open("rb") as stream:
        header = stream.read(24)
        if len(header) != 24:
            raise ValueError("PCAP global header is missing or truncated")
        magic = header[:4]
        formats = {
            b"\xd4\xc3\xb2\xa1": ("<", 1_000_000),
            b"\xa1\xb2\xc3\xd4": (">", 1_000_000),
            b"\x4d\x3c\xb2\xa1": ("<", 1_000_000_000),
            b"\xa1\xb2\x3c\x4d": (">", 1_000_000_000),
        }
        if magic not in formats:
            raise ValueError("Unsupported capture format (expected classic PCAP)")
        endian, resolution = formats[magic]
        _, _, _, _, _, network = struct.unpack(endian + "HHIIII", header[4:])
        if network != 1:
            raise ValueError(f"Unsupported PCAP link type: {network}; Ethernet is required")
        while True:
            record = stream.read(16)
            if not record:
                break
            if len(record) != 16:
                raise ValueError("Truncated PCAP packet header")
            seconds, fraction, included, _ = struct.unpack(endian + "IIII", record)
            data = stream.read(included)
            if len(data) != included:
                raise ValueError("Truncated PCAP packet data")
            timestamp = datetime.fromtimestamp(seconds + fraction / resolution, timezone.utc)
            yield timestamp, data


def _parse_packet(timestamp: datetime, frame: bytes) -> Optional[Packet]:
    if len(frame) < 14:
        return None
    offset = 14
    ether_type = struct.unpack("!H", frame[12:14])[0]
    if ether_type == 0x8100 and len(frame) >= 18:
        ether_type = struct.unpack("!H", frame[16:18])[0]
        offset = 18
    if ether_type == 0x0800 and len(frame) >= offset + 20:
        version_ihl = frame[offset]
        ihl = (version_ihl & 0x0F) * 4
        if version_ihl >> 4 != 4 or ihl < 20 or len(frame) < offset + ihl:
            return None
        protocol_number = frame[offset + 9]
        source = socket.inet_ntoa(frame[offset + 12:offset + 16])
        destination = socket.inet_ntoa(frame[offset + 16:offset + 20])
        transport = offset + ihl
    elif ether_type == 0x86DD and len(frame) >= offset + 40:
        protocol_number = frame[offset + 6]
        source = str(ipaddress.IPv6Address(frame[offset + 8:offset + 24]))
        destination = str(ipaddress.IPv6Address(frame[offset + 24:offset + 40]))
        transport = offset + 40
    else:
        return None
    protocols = {1: "icmp", 6: "tcp", 17: "udp", 58: "icmpv6"}
    protocol = protocols.get(protocol_number, str(protocol_number))
    source_port = destination_port = None
    payload_offset = transport
    if protocol_number == 6 and len(frame) >= transport + 20:
        source_port, destination_port = struct.unpack("!HH", frame[transport:transport + 4])
        payload_offset = transport + max(20, (frame[transport + 12] >> 4) * 4)
    elif protocol_number == 17 and len(frame) >= transport + 8:
        source_port, destination_port = struct.unpack("!HH", frame[transport:transport + 4])
        payload_offset = transport + 8
    return Packet(timestamp, source, destination, protocol, source_port,
                  destination_port, len(frame), frame[payload_offset:])


def parse_pcap(path: Path) -> List[Packet]:
    """Parse supported packets from a classic PCAP file."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    return [packet for timestamp, frame in _pcap_records(path)
            for packet in [_parse_packet(timestamp, frame)] if packet is not None]


def reconstruct_sessions(packets: List[Packet]) -> List[Dict[str, Any]]:
    """Aggregate packets into bidirectional transport sessions."""
    sessions: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
    for packet in packets:
        left = (packet.source, packet.source_port or 0)
        right = (packet.destination, packet.destination_port or 0)
        endpoints = tuple(sorted((left, right)))
        key = (packet.protocol,) + endpoints
        row = sessions.setdefault(key, {
            "protocol": packet.protocol, "endpoints": endpoints, "packets": 0,
            "bytes": 0, "first_seen": packet.timestamp, "last_seen": packet.timestamp,
        })
        row["packets"] += 1
        row["bytes"] += packet.length
        row["last_seen"] = max(row["last_seen"], packet.timestamp)
    return sorted(sessions.values(), key=lambda row: row["first_seen"])


def extract_network_iocs(packets: List[Packet]) -> Dict[str, List[str]]:
    """Extract IP addresses, DNS-looking names, URLs and email addresses."""
    from Artefact.modules.memory import extract_iocs
    text = []
    for packet in packets:
        text.extend((packet.source, packet.destination))
        if packet.payload:
            text.append(packet.payload.decode("utf-8", errors="ignore"))
    found = extract_iocs(text)
    return {key: sorted(values) for key, values in found.items()
            if key in {"ipv4", "ipv6", "domain", "url", "email"}}


def extract_http_objects(packets: List[Packet], output_dir: Path,
                         max_object_size: int = 100 * 1024 * 1024) -> List[Path]:
    """Extract bounded HTTP response bodies visible in TCP payloads."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    streams: Dict[Tuple[Any, ...], bytearray] = defaultdict(bytearray)
    for packet in packets:
        if packet.protocol != "tcp" or not packet.payload:
            continue
        endpoints = tuple(sorted(((packet.source, packet.source_port or 0),
                                  (packet.destination, packet.destination_port or 0))))
        stream = streams[endpoints]
        if len(stream) <= max_object_size * 2:
            stream.extend(packet.payload)
    extracted = []
    for stream in streams.values():
        data = bytes(stream)
        cursor = 0
        while True:
            start = data.find(b"HTTP/1.", cursor)
            if start < 0:
                break
            header_end = data.find(b"\r\n\r\n", start)
            if header_end < 0:
                break
            headers = data[start:header_end].decode("iso-8859-1", errors="replace")
            length_match = re.search(r"(?im)^Content-Length:\s*(\d+)\s*$", headers)
            if not length_match:
                cursor = header_end + 4
                continue
            length = int(length_match.group(1))
            if length < 0 or length > max_object_size:
                cursor = header_end + 4
                continue
            body_start = header_end + 4
            body = data[body_start:body_start + length]
            if len(body) != length:
                break
            content_type = re.search(r"(?im)^Content-Type:\s*([^;\r\n]+)", headers)
            extensions = {"image/jpeg": ".jpg", "image/png": ".png",
                          "application/pdf": ".pdf", "text/plain": ".txt",
                          "application/json": ".json"}
            suffix = extensions.get(content_type.group(1).strip().lower(), ".bin") if content_type else ".bin"
            digest = hashlib.sha256(body).hexdigest()
            target = output_dir / f"http_{digest[:16]}{suffix}"
            target.write_bytes(body)
            extracted.append(target)
            cursor = body_start + length
    return extracted


def match_threat_intelligence(iocs: Dict[str, List[str]], feed_path: Path) -> Dict[str, List[str]]:
    """Match extracted IOCs against a local JSON threat-intelligence feed."""
    feed = json.loads(Path(feed_path).read_text(encoding="utf-8"))
    if not isinstance(feed, dict):
        raise ValueError("Threat intelligence feed must be a JSON object")
    return {kind: sorted(set(values) & {str(item) for item in feed.get(kind, [])})
            for kind, values in iocs.items() if set(values) & {str(item) for item in feed.get(kind, [])}}


def analyze_pcap(path: Path, threat_feed: Optional[Path] = None) -> Dict[str, Any]:
    """Return packets, sessions, IOCs, timeline and traffic statistics."""
    packets = parse_pcap(path)
    protocols = Counter(packet.protocol for packet in packets)
    hosts = Counter(endpoint for packet in packets for endpoint in (packet.source, packet.destination))
    iocs = extract_network_iocs(packets)
    result = {
        "source": str(path),
        "packet_count": len(packets),
        "byte_count": sum(packet.length for packet in packets),
        "protocols": dict(protocols),
        "top_hosts": hosts.most_common(20),
        "sessions": reconstruct_sessions(packets),
        "iocs": iocs,
        "timeline": [{"timestamp": p.timestamp, "source": p.source,
                      "destination": p.destination, "protocol": p.protocol,
                      "length": p.length} for p in packets],
        "packets": [{**asdict(p), "payload": p.payload.hex()} for p in packets],
    }
    if threat_feed:
        result["threat_matches"] = match_threat_intelligence(iocs, threat_feed)
    return result


__all__ = ["Packet", "analyze_pcap", "extract_http_objects", "extract_network_iocs",
           "match_threat_intelligence", "parse_pcap", "reconstruct_sessions"]
