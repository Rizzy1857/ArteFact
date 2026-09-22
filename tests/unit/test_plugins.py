import hashlib
import json
import zipfile

import pytest

from Artefact.plugins import PluginMarketplace, PluginMetadata, PluginRegistry


def test_verified_plugin_lifecycle(tmp_path):
    root = tmp_path / "plugins"
    plugin = root / "demo"
    plugin.mkdir(parents=True)
    source = plugin / "main.py"
    source.write_text("def analyze(value):\n    return value + 1\n", encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    registry = PluginRegistry(root)
    registry.register(PluginMetadata("demo", "1.0.0", "main.py", sha256=digest))
    assert registry.discover()[0].name == "demo"
    assert registry.verify(registry.discover()[0])
    assert registry.load("demo").analyze(1) == 2
    source.write_text("def analyze(value): return 0", encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        registry.load("demo")


def test_marketplace_archive_install_and_traversal_protection(tmp_path):
    source = tmp_path / "source"
    package_dir = source / "market-demo"
    package_dir.mkdir(parents=True)
    entrypoint = package_dir / "plugin.py"
    entrypoint.write_text("VALUE = 42\n", encoding="utf-8")
    manifest = PluginMetadata("market-demo", "1.0.0", "plugin.py",
                              sha256=hashlib.sha256(entrypoint.read_bytes()).hexdigest())
    (package_dir / "plugin.json").write_text(json.dumps({
        "name": manifest.name, "version": manifest.version,
        "entrypoint": manifest.entrypoint, "api_version": manifest.api_version,
        "sha256": manifest.sha256, "description": "", "requires": []
    }), encoding="utf-8")
    archive = tmp_path / "plugin.zip"
    with zipfile.ZipFile(archive, "w") as package:
        package.write(entrypoint, "market-demo/plugin.py")
        package.write(package_dir / "plugin.json", "market-demo/plugin.json")
    registry = PluginRegistry(tmp_path / "installed")
    installed = PluginMarketplace(registry).install_archive(
        archive, hashlib.sha256(archive.read_bytes()).hexdigest())
    assert installed.name == "market-demo"
    assert registry.load("market-demo").VALUE == 42

    unsafe = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(unsafe, "w") as package:
        package.writestr("../escape.py", "bad")
    with pytest.raises(ValueError, match="unsafe path"):
        PluginMarketplace(PluginRegistry(tmp_path / "other")).install_archive(
            unsafe, hashlib.sha256(unsafe.read_bytes()).hexdigest())


def test_plugin_dependency_check(tmp_path):
    plugin = tmp_path / "plugins" / "needs-package"
    plugin.mkdir(parents=True)
    source = plugin / "main.py"
    source.write_text("VALUE = 1", encoding="utf-8")
    registry = PluginRegistry(tmp_path / "plugins")
    metadata = PluginMetadata("needs-package", "1.0", "main.py",
                              sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                              requires=["definitely-not-an-installed-package>=9"])
    registry.register(metadata)
    with pytest.raises(RuntimeError, match="dependencies missing"):
        registry.load("needs-package")
