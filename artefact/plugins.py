"""
Plugin loader for ArteFact. Loads plugins from the plugins/ directory and entry points.
"""
import importlib
import pkg_resources
import os
from pathlib import Path

PLUGIN_NAMESPACE = "artefact_plugins"


def load_plugins():
    plugins = {}
    # Load from plugins/ directory
    plugins_dir = Path(__file__).parent / "plugins"
    if plugins_dir.exists():
        for file in plugins_dir.glob("*.py"):
            if file.name == "__init__.py":
                continue
            mod_name = f"artefact.plugins.{file.stem}"
            mod = importlib.import_module(mod_name)
            plugins[file.stem] = mod
    # Load from entry points
    for entry_point in pkg_resources.iter_entry_points(PLUGIN_NAMESPACE):
        plugin = entry_point.load()
        plugins[entry_point.name] = plugin
    return plugins
