import pytest
from pathlib import Path
from artefact.modules import metadata

def test_extract_metadata_image(tmp_path):
    # Create a minimal PNG file
    file = tmp_path / "test.png"
    file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'0' * 100 + b'IEND\xaeB`\x82')
    # Should not raise, even if no real metadata
    metadata.extract_metadata(file)

def test_extract_metadata_pdf(tmp_path):
    try:
        from PyPDF2 import PdfWriter
    except ImportError:
        pytest.skip("PyPDF2 not installed")
    file = tmp_path / "test.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with open(file, "wb") as f:
        writer.write(f)
    metadata.extract_metadata(file)

def test_extract_metadata_missing(tmp_path):
    file = tmp_path / "nofile.txt"
    metadata.extract_metadata(file)
