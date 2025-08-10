"""
System-level tests for ArteFact
"""

from pathlib import Path
import shutil
import tempfile
from rich.console import Console

console = Console()

def test_comprehensive():
    """Run comprehensive testing."""
    from tests.system.critical_tester import CriticalTester
    
    tester = CriticalTester()
    results = tester.run_all_tests()
    tester.print_critical_analysis(results)
    
    # Assert overall quality
    assert results['failed'] == 0, "Critical tests failed"
    assert not results['critical_issues'], "Critical issues found"
    
    # Check minimum standards
    total_tests = results['passed'] + results['failed']
    success_rate = (results['passed'] / total_tests * 100) if total_tests > 0 else 0
    assert success_rate >= 80, f"Success rate too low: {success_rate:.1f}%"

def test_real_world_scenario():
    """Test ArteFact with real-world file types and scenarios."""
    # Setup test environment
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        
        try:
            # Create test files
            (temp_dir / "text.txt").write_text("Test content")
            (temp_dir / "binary.bin").write_bytes(bytes(range(256)))
            
            # Test file operations
            from Artefact.modules.hasher import hash_file
            from Artefact.modules.metadata import extract_metadata
            from Artefact.modules.timeline import extract_file_timestamps
            
            # Run operations
            file_hash = hash_file(temp_dir / "text.txt", "sha256")
            assert len(file_hash) == 64, "Invalid hash length"
            
            metadata = extract_metadata(temp_dir / "text.txt")
            assert 'timestamps' in metadata, "Missing timestamps in metadata"
            
            timeline = extract_file_timestamps(temp_dir / "text.txt")
            assert len(timeline) > 0, "No timeline events found"
            
        finally:
            # Cleanup
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
