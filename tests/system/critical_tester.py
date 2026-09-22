"""
Critical testing module for comprehensive system testing
"""

import time
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table

@dataclass
class TestResult:
    name: str
    result: bool
    duration: float
    error: str = ""
    
class CriticalTester:
    """Comprehensive system tester for critical functionality."""
    
    def __init__(self):
        self.console = Console()
        self.test_cases: List[Dict[str, Any]] = [
            {'name': 'File Hashing', 'func': self._test_hashing},
            {'name': 'Metadata Extraction', 'func': self._test_metadata},
            {'name': 'Timeline Analysis', 'func': self._test_timeline},
            {'name': 'Memory Analysis', 'func': self._test_memory},
            {'name': 'File Carving', 'func': self._test_carving}
        ]
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all critical tests and return results."""
        results = {
            'passed': 0,
            'failed': 0,
            'test_results': [],
            'critical_issues': []
        }
        
        for test in self.test_cases:
            start_time = time.time()
            try:
                test['func']()
                duration = time.time() - start_time
                results['test_results'].append(
                    TestResult(test['name'], True, duration)
                )
                results['passed'] += 1
            except Exception as e:
                duration = time.time() - start_time
                results['test_results'].append(
                    TestResult(test['name'], False, duration, str(e))
                )
                results['failed'] += 1
                if self._is_critical_error(e):
                    results['critical_issues'].append(str(e))
        
        return results
    
    def print_critical_analysis(self, results: Dict[str, Any]) -> None:
        """Print a detailed analysis of test results."""
        table = Table(title="Critical Test Results")
        table.add_column("Test Name")
        table.add_column("Result")
        table.add_column("Duration (s)")
        table.add_column("Error", width=40)
        
        for result in results['test_results']:
            table.add_row(
                result.name,
                "✅" if result.result else "❌",
                f"{result.duration:.2f}",
                result.error or ""
            )
        
        self.console.print(table)
        if results['critical_issues']:
            self.console.print("[red]Critical Issues Found:[/red]")
            for issue in results['critical_issues']:
                self.console.print(f"[red]- {issue}[/red]")
    
    def _is_critical_error(self, error: Exception) -> bool:
        """Determine if an error is critical."""
        critical_patterns = [
            "SecurityError",
            "MemoryError",
            "SystemError",
            "IntegrityError"
        ]
        return any(pattern in str(error) for pattern in critical_patterns)
    
    def _test_hashing(self) -> None:
        """Test file hashing functionality."""
        from Artefact.modules.hasher import hash_file
        test_file = Path("test/sample.jpg")
        hash_result = hash_file(test_file, "sha256")
        assert len(hash_result) == 64, "Invalid hash length"
    
    def _test_metadata(self) -> None:
        """Test metadata extraction functionality."""
        from Artefact.modules.metadata import extract_metadata
        test_file = Path("test/sample.jpg")
        metadata = extract_metadata(test_file)
        assert metadata is not None, "Failed to extract metadata"
        assert 'format' in metadata, "Missing format information"
    
    def _test_timeline(self) -> None:
        """Test timeline analysis functionality."""
        from Artefact.modules.timeline import extract_file_timestamps
        test_file = Path("test/sample.jpg")
        timeline = extract_file_timestamps(test_file)
        assert len(timeline) > 0, "No timeline events found"
    
    def _test_memory(self) -> None:
        """Test memory analysis functionality."""
        from Artefact.modules.memory import analyze_memory_dump
        with tempfile.TemporaryDirectory() as temp_dir:
            dump_path = Path(temp_dir) / "sample.raw"
            test_data = bytes(range(256))
            dump_path.write_bytes(test_data)
            result = analyze_memory_dump(dump_path)
            assert result.size == len(test_data), "Incorrect memory dump size"
            assert result.path == dump_path, "Incorrect memory dump path"
    
    def _test_carving(self) -> None:
        """Test file carving functionality."""
        from Artefact.modules.carving import carve_files
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            image_path = root / "sample.img"
            output_dir = root / "carved"
            image_path.write_bytes(b"prefix\xff\xd8\xfftest\xff\xd9suffix")
            carved = carve_files(image_path, output_dir, types=["jpg"], parallel=False)
            assert len(carved) == 1, "File carving failed"
