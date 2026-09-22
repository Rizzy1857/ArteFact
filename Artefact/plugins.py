"""Versioned, integrity-checked local plugin registry."""

import hashlib
import importlib.util
import importlib.metadata
import json
import shutil
import tempfile
import urllib.parse
import urllib.request
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

PLUGIN_API_VERSION = "2.0"


@dataclass(frozen=True)
class PluginMetadata:
    name: str
    version: str
    entrypoint: str
    api_version: str = PLUGIN_API_VERSION
    sha256: Optional[str] = None
    description: str = ""
    requires: Sequence[str] = ()


class PluginRegistry:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def discover(self) -> List[PluginMetadata]:
        plugins = []
        for manifest in sorted(self.root.glob("*/plugin.json")):
            data = json.loads(manifest.read_text(encoding="utf-8"))
            metadata = PluginMetadata(**data)
            if metadata.api_version != PLUGIN_API_VERSION:
                continue
            plugins.append(metadata)
        return plugins

    def _directory(self, name: str) -> Path:
        if not name or Path(name).name != name:
            raise ValueError("Invalid plugin name")
        return self.root / name

    def verify(self, metadata: PluginMetadata) -> bool:
        entrypoint = (self._directory(metadata.name) / metadata.entrypoint).resolve()
        if self._directory(metadata.name).resolve() not in entrypoint.parents or not entrypoint.is_file():
            return False
        if not metadata.sha256:
            return False
        digest = hashlib.sha256(entrypoint.read_bytes()).hexdigest()
        return digest.lower() == metadata.sha256.lower()

    def load(self, name: str) -> Any:
        metadata = next((item for item in self.discover() if item.name == name), None)
        if metadata is None:
            raise KeyError(f"Plugin not found or API-incompatible: {name}")
        if not self.verify(metadata):
            raise ValueError(f"Plugin integrity verification failed: {name}")
        missing = self.missing_dependencies(metadata)
        if missing:
            raise RuntimeError(f"Plugin dependencies missing: {', '.join(missing)}")
        path = self._directory(name) / metadata.entrypoint
        spec = importlib.util.spec_from_file_location(f"artefact_plugin_{name}", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load plugin: {name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def missing_dependencies(self, metadata: PluginMetadata) -> List[str]:
        """Return declared Python distributions that are unavailable."""
        missing = []
        for requirement in metadata.requires:
            distribution = requirement.split(";", 1)[0].strip()
            for marker in ("<", ">", "=", "!", "~", "["):
                distribution = distribution.split(marker, 1)[0].strip()
            try:
                importlib.metadata.version(distribution)
            except importlib.metadata.PackageNotFoundError:
                missing.append(requirement)
        return missing

    def register(self, metadata: PluginMetadata) -> Path:
        if metadata.api_version != PLUGIN_API_VERSION:
            raise ValueError(f"Unsupported plugin API: {metadata.api_version}")
        directory = self._directory(metadata.name)
        entrypoint = (directory / metadata.entrypoint).resolve()
        if directory.resolve() not in entrypoint.parents or not entrypoint.is_file():
            raise FileNotFoundError(entrypoint)
        manifest = directory / "plugin.json"
        manifest.write_text(json.dumps(asdict(metadata), indent=2), encoding="utf-8")
        return manifest


class PluginMarketplace:
    """Install integrity-pinned plugins from a trusted HTTPS index."""

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    @staticmethod
    def fetch_index(url: str, timeout: int = 15) -> Dict[str, Any]:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https":
            raise ValueError("Plugin indexes must use HTTPS")
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.headers.get_content_type() != "application/json":
                raise ValueError("Plugin index must be JSON")
            return json.loads(response.read(2 * 1024 * 1024).decode("utf-8"))

    def install_archive(self, archive: Path, expected_sha256: str) -> PluginMetadata:
        """Verify and safely install a plugin ZIP archive."""
        archive = Path(archive)
        actual = hashlib.sha256(archive.read_bytes()).hexdigest()
        if actual.lower() != expected_sha256.lower():
            raise ValueError("Plugin archive integrity verification failed")
        with tempfile.TemporaryDirectory(prefix="artefact-plugin-") as temp:
            staging = Path(temp)
            with zipfile.ZipFile(archive) as package:
                for member in package.infolist():
                    target = (staging / member.filename).resolve()
                    if staging.resolve() not in target.parents and target != staging.resolve():
                        raise ValueError("Plugin archive contains an unsafe path")
                package.extractall(staging)
            manifests = list(staging.glob("*/plugin.json"))
            if len(manifests) != 1:
                raise ValueError("Plugin archive must contain one top-level plugin manifest")
            data = json.loads(manifests[0].read_text(encoding="utf-8"))
            metadata = PluginMetadata(**data)
            source = manifests[0].parent
            destination = self.registry._directory(metadata.name)
            if destination.exists():
                raise FileExistsError(f"Plugin already installed: {metadata.name}")
            shutil.copytree(source, destination)
            try:
                installed = next(item for item in self.registry.discover() if item.name == metadata.name)
                if not self.registry.verify(installed):
                    raise ValueError("Installed plugin entrypoint failed integrity verification")
                return installed
            except Exception:
                shutil.rmtree(destination, ignore_errors=True)
                raise

    def install(self, index_url: str, name: str) -> PluginMetadata:
        index = self.fetch_index(index_url)
        entry = next((item for item in index.get("plugins", []) if item.get("name") == name), None)
        if entry is None:
            raise KeyError(f"Plugin not found in marketplace: {name}")
        download_url = entry.get("url", "")
        if urllib.parse.urlparse(download_url).scheme != "https":
            raise ValueError("Plugin downloads must use HTTPS")
        with tempfile.TemporaryDirectory(prefix="artefact-download-") as temp:
            archive = Path(temp) / "plugin.zip"
            with urllib.request.urlopen(download_url, timeout=30) as response:
                archive.write_bytes(response.read(50 * 1024 * 1024 + 1))
            if archive.stat().st_size > 50 * 1024 * 1024:
                raise ValueError("Plugin archive exceeds 50 MiB limit")
            return self.install_archive(archive, entry["sha256"])


__all__ = ["PLUGIN_API_VERSION", "PluginMarketplace", "PluginMetadata", "PluginRegistry"]
