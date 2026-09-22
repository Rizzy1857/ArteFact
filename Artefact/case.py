"""Case and evidence-chain management."""

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Evidence:
    id: str
    path: str
    sha256: str
    size: int
    added_at: str
    description: str = ""


@dataclass
class Case:
    id: str
    title: str
    created_at: str
    evidence: List[Evidence] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    chain_of_custody: List[Dict[str, str]] = field(default_factory=list)

    @classmethod
    def create(cls, title: str, case_id: Optional[str] = None) -> "Case":
        return cls(case_id or str(uuid.uuid4()), title, _now())

    def add_evidence(self, path: Path, description: str = "", actor: str = "analyst") -> Evidence:
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(path)
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        item = Evidence(str(uuid.uuid4()), str(path.resolve()), digest.hexdigest(),
                        path.stat().st_size, _now(), description)
        self.evidence.append(item)
        self.chain_of_custody.append({"timestamp": _now(), "actor": actor,
                                      "action": "evidence_added", "evidence_id": item.id,
                                      "sha256": item.sha256})
        return item

    def add_finding(self, title: str, details: Any, severity: str = "informational") -> None:
        self.findings.append({"title": title, "details": details,
                              "severity": severity, "timestamp": _now()})

    def verify_evidence(self) -> List[Dict[str, Any]]:
        """Re-hash every evidence item and report missing or modified sources."""
        results = []
        for item in self.evidence:
            path = Path(item.path)
            if not path.is_file():
                results.append({"evidence_id": item.id, "valid": False, "reason": "missing"})
                continue
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            valid = digest.hexdigest() == item.sha256 and path.stat().st_size == item.size
            results.append({"evidence_id": item.id, "valid": valid,
                            "reason": "verified" if valid else "hash_or_size_mismatch"})
        return results

    def save(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path) -> "Case":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        data["evidence"] = [Evidence(**item) for item in data.get("evidence", [])]
        return cls(**data)


__all__ = ["Case", "Evidence"]
