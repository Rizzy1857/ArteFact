import pytest
from pathlib import Path
from artefact.modules import carving

def test_carve_files_jpg(tmp_path):
    # Create a fake disk image with a JPG header/footer
    img = tmp_path / "disk.img"
    jpg_data = b'\xff\xd8\xff' + b'hello' + b'\xff\xd9'
    img.write_bytes(jpg_data)
    outdir = tmp_path / "out"
    carving.carve_files(img, outdir, types=["jpg"])
    files = list(outdir.glob("*.jpg"))
    assert len(files) == 1
    assert files[0].read_bytes() == jpg_data

def test_carve_files_none(tmp_path):
    img = tmp_path / "disk.img"
    img.write_bytes(b"no signatures here")
    outdir = tmp_path / "out"
    carving.carve_files(img, outdir, types=["jpg"])
    files = list(outdir.glob("*.jpg"))
    assert len(files) == 0
