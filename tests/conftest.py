"""
ArteFact Pytest Configuration and Fixtures
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator, List
from datetime import datetime, timezone


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test requiring multiple modules"
    )
    config.addinivalue_line(
        "markers",
        "system: mark test as system test requiring full environment"
    )
    config.addinivalue_line(
        "markers",
        "performance: mark test as performance benchmark test"
    )


def pytest_collection_modifyitems(session, config, items):
    """Modify test items in-place to ensure proper test ordering."""
    def test_order(item):
        if "system" in item.keywords:
            return 2  # Run system tests last
        if "integration" in item.keywords:
            return 1  # Run integration tests after unit tests
        return 0  # Run unit tests first
    
    items.sort(key=test_order)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-system",
        action="store_true",
        default=False,
        help="run system tests"
    )
    parser.addoption(
        "--performance",
        action="store_true",
        default=False,
        help="run performance tests"
    )


def pytest_runtest_setup(item):
    """Skip tests based on markers and options."""
    if "system" in item.keywords and not item.config.getoption("--run-system"):
        pytest.skip("need --run-system option to run")
    if "performance" in item.keywords and not item.config.getoption("--performance"):
        pytest.skip("need --performance option to run")


# ==== Core Fixtures ====

@pytest.fixture(scope="session")
def test_root() -> Path:
    """Return the root directory of the test suite."""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def fixtures_dir(test_root: Path) -> Path:
    """Return the fixtures directory."""
    fixtures = test_root / "fixtures"
    fixtures.mkdir(exist_ok=True)
    return fixtures


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        yield temp_path
        if temp_path.exists():
            shutil.rmtree(temp_path)


# ==== Test Data Fixtures ====

@pytest.fixture
def sample_files(temp_dir: Path) -> Dict[str, Path]:
    """Create sample files for testing."""
    files = {
        'text': temp_dir / "text_file.txt",
        'binary': temp_dir / "binary_file.bin",
        'large': temp_dir / "large_file.dat",
        'empty': temp_dir / "empty_file.empty",
        'unicode': temp_dir / "unicode_file.txt",
        'image': temp_dir / "test.jpg",
        'document': temp_dir / "test.pdf",
        'archive': temp_dir / "test.zip"
    }
    
    # Create test files
    files['text'].write_text("Hello, World! This is a test file.\n")
    files['binary'].write_bytes(bytes(range(256)))
    files['large'].write_bytes(b"A" * (1024 * 1024))  # 1MB
    files['empty'].touch()
    files['unicode'].write_text("Unicode test: αβγδε 中文 � العربية")
    
    # Create mock image/document files
    files['image'].write_bytes(b'\xff\xd8\xff\xe0' + b'MOCK JPEG' + b'\xff\xd9')
    files['document'].write_bytes(b'%PDF-1.4' + b'MOCK PDF' + b'%%EOF')
    files['archive'].write_bytes(b'PK\x03\x04' + b'MOCK ZIP' + b'PK\x05\x06')
    
    return files


@pytest.fixture
def mock_disk_image(temp_dir: Path) -> Path:
    """Create a mock disk image with embedded files."""
    image_path = temp_dir / "test.img"
    content = bytearray(50000)  # 50KB image
    
    # Add file signatures and content
    signatures = {
        1000: (b'\xff\xd8\xff\xe0', b'JPEG content', b'\xff\xd9'),  # JPEG
        2000: (b'%PDF-1.4', b'PDF content', b'%%EOF'),  # PDF
        3000: (b'PK\x03\x04', b'ZIP content', b'PK\x05\x06')  # ZIP
    }
    
    for pos, (header, content_bytes, footer) in signatures.items():
        content[pos:pos+len(header)] = header
        content[pos+len(header):pos+len(header)+len(content_bytes)] = content_bytes
        content[pos+len(header)+len(content_bytes):pos+len(header)+len(content_bytes)+len(footer)] = footer
    
    image_path.write_bytes(content)
    return image_path


@pytest.fixture
def sample_timeline_events() -> List[Any]:
    """Create sample timeline events for testing."""
    from Artefact.modules.timeline import TimelineEvent
    
    now = datetime.now(timezone.utc)
    events = [
        TimelineEvent(
            timestamp=now,
            event_type="file_created",
            source="test",
            description="Test file created"
        ),
        TimelineEvent(
            timestamp=now,
            event_type="file_modified",
            source="test",
            description="Test file modified"
        ),
        TimelineEvent(
            timestamp=now,
            event_type="file_accessed",
            source="test",
            description="Test file accessed"
        )
    ]
    return events


@pytest.fixture
def memory_dump(temp_dir: Path) -> Path:
    """Create a mock memory dump for testing."""
    dump_path = temp_dir / "memory.dump"
    content = (
        b"This is a test string with http://example.com and admin@test.com\n"
        b"Another line with 192.168.1.1 and https://malicious.site\n"
        b"MZ" + b"A" * 100 + b"PE header content here\n"  # Mock PE
        b"\x7fELF" + b"B" * 50 + b"ELF content\n"  # Mock ELF
        b"FLAG{test_flag_1234}\n"  # Mock flag
        b"API_KEY=secret123456789\n"  # Mock secret
    )
    dump_path.write_bytes(content)
    return dump_path
