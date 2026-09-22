import hashlib
import zipfile

import pytest

from Artefact.case import Case
from Artefact.core import safe_filename
from Artefact.plugins import PluginMarketplace, PluginRegistry
from Artefact.reporting import ReportBuilder


def test_plugin_archive_blocks_absolute_and_parent_paths(tmp_path):
    for member in ("../outside.py", "/absolute.py"):
        archive = tmp_path / (hashlib.sha256(member.encode()).hexdigest() + ".zip")
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr(member, "malicious")
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        with pytest.raises(ValueError, match="unsafe path"):
            PluginMarketplace(PluginRegistry(tmp_path / "plugins")).install_archive(archive, digest)


def test_reports_escape_untrusted_html():
    case = Case.create("<script>alert(1)</script>")
    rendered = ReportBuilder(case).html()
    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;" in rendered


def test_safe_filename_removes_windows_metacharacters():
    assert safe_filename('../bad<name>:file?.txt') == '.._bad_name__file_.txt'
