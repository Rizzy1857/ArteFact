#!/usr/bin/env python3
"""
Comprehensive Deep-Dive Testing and Critical Analysis of ArteFact
================================================================

This script performs exhaustive testing of all ArteFact functionality
and provides detailed analysis of code quality, performance, and reliability.
"""

import sys
import os
import time
import tempfile
import shutil
import traceback
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class CriticalTester:
    """Comprehensive testing and analysis framework for ArteFact."""
    
    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'performance_issues': [],
            'critical_issues': [],
            'test_details': []
        }
        self.temp_dir = None
    
    def setup_test_environment(self):
        """Set up test environment with sample files."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix='artefact_test_'))
        print(f"📁 Test environment created at: {self.temp_dir}")
        
        # Create test files
        test_files = {
            'text_file.txt': b"Hello, World! This is a test file for ArteFact.\nIt contains multiple lines.\nAnd various characters: !@#$%^&*()",
            'binary_file.bin': bytes(range(256)),
            'large_file.dat': b"A" * 10000,  # 10KB file
            'empty_file.empty': b"",
            'unicode_file.txt': "Unicode test: αβγδε 中文 🎉 العربية".encode('utf-8')
        }
        
        for filename, content in test_files.items():
            (self.temp_dir / filename).write_bytes(content)
        
        # Create subdirectory with files
        subdir = self.temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested_file.txt").write_text("Nested content")
        
        # Create a mock disk image for carving tests
        self.create_mock_disk_image()
        
        return True
    
    def create_mock_disk_image(self):
        """Create a mock disk image with embedded files for carving tests."""
        disk_image = self.temp_dir / "mock_disk.img"
        
        # Create image with some JPG and PDF signatures
        content = bytearray(50000)  # 50KB image
        
        # Embed a fake JPG at position 1000
        jpg_header = b'\xff\xd8\xff\xe0'
        jpg_footer = b'\xff\xd9'
        jpg_content = b'fake jpeg content here'
        
        pos = 1000
        content[pos:pos+len(jpg_header)] = jpg_header
        content[pos+len(jpg_header):pos+len(jpg_header)+len(jpg_content)] = jpg_content
        content[pos+len(jpg_header)+len(jpg_content):pos+len(jpg_header)+len(jpg_content)+len(jpg_footer)] = jpg_footer
        
        # Embed a fake PDF at position 2000
        pdf_header = b'%PDF-1.4'
        pdf_footer = b'%%EOF'
        pdf_content = b'fake pdf content here'
        
        pos = 2000
        content[pos:pos+len(pdf_header)] = pdf_header
        content[pos+len(pdf_header):pos+len(pdf_header)+len(pdf_content)] = pdf_content
        content[pos+len(pdf_header)+len(pdf_content):pos+len(pdf_header)+len(pdf_content)+len(pdf_footer)] = pdf_footer
        
        disk_image.write_bytes(content)
    
    def test_imports_and_structure(self) -> bool:
        """Test all imports and verify code structure."""
        print("\n🔍 Testing Imports and Code Structure...")
        
        try:
            # Test main package import
            from Artefact import __version__, __codename__
            print(f"✓ Main package: v{__version__} '{__codename__}'")
            
            # Test all module imports
            modules = [
                ('Artefact.modules.hasher', ['hash_file', 'hash_directory', 'SUPPORTED_ALGORITHMS']),
                ('Artefact.modules.carving', ['carve_files', 'FILE_SIGNATURES']),
                ('Artefact.modules.metadata', ['extract_metadata']),
                ('Artefact.modules.timeline', ['extract_file_timestamps', 'TimelineEvent', 'timeline_to_json']),
                ('Artefact.modules.memory', ['extract_strings', 'extract_iocs', 'carve_binaries']),
                ('Artefact.modules.liveops', ['list_processes', 'list_connections']),
                ('Artefact.modules.mount', ['list_partitions', 'extract_partition']),
                ('Artefact.error_handler', ['handle_error', 'ArtefactError']),
                ('Artefact.core', ['get_config', 'get_logger']),
                ('Artefact.console', ['interactive_mode']),
                ('Artefact.cli', ['main'])
            ]
            
            for module_name, expected_functions in modules:
                try:
                    module = __import__(module_name, fromlist=expected_functions)
                    for func in expected_functions:
                        if not hasattr(module, func):
                            self.results['critical_issues'].append(f"Missing function {func} in {module_name}")
                            return False
                    print(f"✓ {module_name}")
                except Exception as e:
                    self.results['critical_issues'].append(f"Failed to import {module_name}: {e}")
                    return False
            
            self.results['passed'] += 1
            return True
            
        except Exception as e:
            self.results['failed'] += 1
            self.results['critical_issues'].append(f"Import test failed: {e}")
            return False
    
    def test_hasher_functionality(self) -> bool:
        """Comprehensive test of hashing functionality."""
        print("\n🔐 Testing Hasher Functionality...")
        
        try:
            from Artefact.modules.hasher import hash_file, hash_directory, SUPPORTED_ALGORITHMS
            
            # Test single file hashing
            test_file = self.temp_dir / "text_file.txt"
            
            for algorithm in SUPPORTED_ALGORITHMS.keys():
                start_time = time.time()
                result = hash_file(test_file, algorithm)
                elapsed = time.time() - start_time
                
                if not result or len(result) == 0:
                    self.results['critical_issues'].append(f"Hash result empty for {algorithm}")
                    return False
                
                # Verify hash format (hex string)
                try:
                    int(result, 16)
                except ValueError:
                    self.results['critical_issues'].append(f"Invalid hash format for {algorithm}: {result}")
                    return False
                
                print(f"✓ {algorithm.upper()}: {result} ({elapsed:.3f}s)")
                
                if elapsed > 1.0:
                    self.results['performance_issues'].append(f"Slow hashing: {algorithm} took {elapsed:.3f}s for small file")
            
            # Test directory hashing
            start_time = time.time()
            dir_results = hash_directory(self.temp_dir, "sha256", output_format="json")
            elapsed = time.time() - start_time
            
            if not dir_results:
                self.results['warnings'].append("Directory hashing returned no results")
            
            print(f"✓ Directory hashing: {len(dir_results)} files ({elapsed:.3f}s)")
            
            # Test error conditions
            try:
                hash_file(Path("nonexistent_file.txt"), "sha256")
                self.results['critical_issues'].append("Hasher should fail on nonexistent file")
                return False
            except Exception:
                print("✓ Error handling: Nonexistent file")
            
            try:
                hash_file(test_file, "invalid_algorithm")
                self.results['critical_issues'].append("Hasher should fail on invalid algorithm")
                return False
            except Exception:
                print("✓ Error handling: Invalid algorithm")
            
            self.results['passed'] += 1
            return True
            
        except Exception as e:
            self.results['failed'] += 1
            self.results['critical_issues'].append(f"Hasher test failed: {e}")
            traceback.print_exc()
            return False
    
    def test_carving_functionality(self) -> bool:
        """Test file carving functionality."""
        print("\n🔍 Testing File Carving...")
        
        try:
            from Artefact.modules.carving import carve_files, FILE_SIGNATURES
            
            disk_image = self.temp_dir / "mock_disk.img"
            output_dir = self.temp_dir / "carved_output"
            output_dir.mkdir()
            
            start_time = time.time()
            carve_files(disk_image, output_dir, types=['jpg', 'pdf'])
            elapsed = time.time() - start_time
            
            carved_files = list(output_dir.glob("*"))
            print(f"✓ Carved {len(carved_files)} files in {elapsed:.3f}s")
            
            if len(carved_files) == 0:
                self.results['warnings'].append("No files were carved from test image")
            
            # Verify carved files exist and have content
            for carved_file in carved_files:
                if carved_file.stat().st_size == 0:
                    self.results['warnings'].append(f"Carved file is empty: {carved_file.name}")
            
            # Test error conditions
            try:
                carve_files(Path("nonexistent_image.img"), output_dir)
                self.results['critical_issues'].append("Carving should fail on nonexistent image")
                return False
            except Exception:
                print("✓ Error handling: Nonexistent image")
            
            self.results['passed'] += 1
            return True
            
        except Exception as e:
            self.results['failed'] += 1
            self.results['critical_issues'].append(f"Carving test failed: {e}")
            traceback.print_exc()
            return False
    
    def test_metadata_functionality(self) -> bool:
        """Test metadata extraction."""
        print("\n📋 Testing Metadata Extraction...")
        
        try:
            from Artefact.modules.metadata import extract_metadata
            
            test_file = self.temp_dir / "text_file.txt"
            
            # Test basic extraction
            start_time = time.time()
            result = extract_metadata(test_file)
            elapsed = time.time() - start_time
            
            if not isinstance(result, dict):
                self.results['critical_issues'].append("Metadata extraction should return dict")
                return False
            
            if 'timestamps' not in result:
                self.results['critical_issues'].append("Metadata result missing timestamps key")
                return False
            
            print(f"✓ Basic extraction: {len(result.get('timestamps', []))} timestamps ({elapsed:.3f}s)")
            
            # Test with nonexistent file
            try:
                result = extract_metadata(Path("nonexistent_file.txt"))
                if result.get('timestamps'):
                    self.results['warnings'].append("Metadata extraction returned data for nonexistent file")
            except Exception:
                print("✓ Error handling: Nonexistent file")
            
            self.results['passed'] += 1
            return True
            
        except Exception as e:
            self.results['failed'] += 1
            self.results['critical_issues'].append(f"Metadata test failed: {e}")
            traceback.print_exc()
            return False
    
    def test_timeline_functionality(self) -> bool:
        """Test timeline generation."""
        print("\n⏰ Testing Timeline Generation...")
        
        try:
            from Artefact.modules.timeline import extract_file_timestamps, TimelineEvent, timeline_to_json, timeline_to_markdown
            from datetime import datetime
            
            test_file = self.temp_dir / "text_file.txt"
            
            # Test timestamp extraction
            start_time = time.time()
            events = extract_file_timestamps(str(test_file))
            elapsed = time.time() - start_time
            
            if not events:
                self.results['critical_issues'].append("Timeline extraction returned no events")
                return False
            
            print(f"✓ Extracted {len(events)} events ({elapsed:.3f}s)")
            
            # Verify event structure
            for event in events:
                if not isinstance(event, TimelineEvent):
                    self.results['critical_issues'].append("Timeline events should be TimelineEvent instances")
                    return False
                
                if not hasattr(event, 'timestamp') or not hasattr(event, 'event_type'):
                    self.results['critical_issues'].append("TimelineEvent missing required attributes")
                    return False
            
            # Test JSON export
            start_time = time.time()
            json_output = timeline_to_json(events)
            elapsed = time.time() - start_time
            
            try:
                json.loads(json_output)
                print(f"✓ JSON export valid ({elapsed:.3f}s)")
            except json.JSONDecodeError:
                self.results['critical_issues'].append("Timeline JSON export is invalid")
                return False
            
            # Test Markdown export
            start_time = time.time()
            md_output = timeline_to_markdown(events)
            elapsed = time.time() - start_time
            
            if not md_output or len(md_output) == 0:
                self.results['critical_issues'].append("Timeline Markdown export is empty")
                return False
            
            print(f"✓ Markdown export ({len(md_output)} chars, {elapsed:.3f}s)")
            
            self.results['passed'] += 1
            return True
            
        except Exception as e:
            self.results['failed'] += 1
            self.results['critical_issues'].append(f"Timeline test failed: {e}")
            traceback.print_exc()
            return False
    
    def test_memory_functionality(self) -> bool:
        """Test memory analysis functionality."""
        print("\n🧠 Testing Memory Analysis...")
        
        try:
            from Artefact.modules.memory import extract_strings, extract_iocs, carve_binaries
            
            # Create a mock memory dump
            memory_dump = self.temp_dir / "memory_dump.mem"
            memory_content = (
                b"This is a test string with http://example.com and admin@test.com\n" +
                b"Another line with 192.168.1.1 and https://malicious.site\n" +
                b"MZ" + b"A" * 100 + b"PE header content here" +  # Mock PE
                b"\x7fELF" + b"B" * 50 + b"ELF content"  # Mock ELF
            )
            memory_dump.write_bytes(memory_content)
            
            # Test string extraction
            start_time = time.time()
            strings = extract_strings(memory_dump, min_length=4)
            elapsed = time.time() - start_time
            
            if not strings:
                self.results['warnings'].append("No strings extracted from memory dump")
            else:
                print(f"✓ Extracted {len(strings)} strings ({elapsed:.3f}s)")
            
            # Test IOC extraction
            start_time = time.time()
            iocs = extract_iocs(strings)
            elapsed = time.time() - start_time
            
            if not isinstance(iocs, dict):
                self.results['critical_issues'].append("IOC extraction should return dict")
                return False
            
            expected_keys = ['ipv4', 'ipv6', 'url', 'email']
            for key in expected_keys:
                if key not in iocs:
                    self.results['critical_issues'].append(f"IOC result missing key: {key}")
                    return False
            
            print(f"✓ IOC extraction: {sum(len(v) for v in iocs.values())} total IOCs ({elapsed:.3f}s)")
            
            # Test binary carving
            carve_output = self.temp_dir / "carved_binaries"
            carve_output.mkdir()
            
            start_time = time.time()
            carve_binaries(memory_dump, carve_output, types=['pe', 'elf'])
            elapsed = time.time() - start_time
            
            carved_binaries = list(carve_output.glob("*"))
            print(f"✓ Carved {len(carved_binaries)} binaries ({elapsed:.3f}s)")
            
            self.results['passed'] += 1
            return True
            
        except Exception as e:
            self.results['failed'] += 1
            self.results['critical_issues'].append(f"Memory analysis test failed: {e}")
            traceback.print_exc()
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling and robustness."""
        print("\n🛡️ Testing Error Handling...")
        
        try:
            from Artefact.error_handler import handle_error, ArtefactError
            
            # Test custom exception
            try:
                raise ArtefactError("Test error message")
            except ArtefactError as e:
                handle_error(e, context="test_context")
                print("✓ Custom exception handling")
            
            # Test various error types
            error_types = [
                FileNotFoundError("Test file not found"),
                ImportError("Test import error"),
                PermissionError("Test permission error"),
                ValueError("Test value error")
            ]
            
            for error in error_types:
                try:
                    handle_error(error, context="test")
                    print(f"✓ {type(error).__name__} handling")
                except Exception as e:
                    self.results['critical_issues'].append(f"Error handler failed on {type(error).__name__}: {e}")
                    return False
            
            self.results['passed'] += 1
            return True
            
        except Exception as e:
            self.results['failed'] += 1
            self.results['critical_issues'].append(f"Error handling test failed: {e}")
            traceback.print_exc()
            return False
    
    def test_cli_functionality(self) -> bool:
        """Test CLI functionality."""
        print("\n💻 Testing CLI Functionality...")
        
        try:
            # Test version command
            import subprocess
            result = subprocess.run([
                sys.executable, "-c",
                "import sys; sys.path.insert(0, '.'); from Artefact.cli import main; main()",
                "--version"
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode != 0:
                self.results['critical_issues'].append("CLI --version command failed")
                return False
            
            if "ARTEFACT" not in result.stdout:
                self.results['critical_issues'].append("CLI version output missing ARTEFACT")
                return False
            
            print("✓ CLI version command")
            
            # Test list-tools command
            result = subprocess.run([
                sys.executable, "-c",
                "import sys; sys.path.insert(0, '.'); from Artefact.cli import main; main()",
                "--list-tools"
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode != 0:
                self.results['critical_issues'].append("CLI --list-tools command failed")
                return False
            
            expected_tools = ['hash', 'carve', 'meta', 'timeline', 'memory', 'mount', 'liveops']
            for tool in expected_tools:
                if tool not in result.stdout:
                    self.results['warnings'].append(f"Tool '{tool}' not found in --list-tools output")
            
            print("✓ CLI list-tools command")
            
            # Test hash command with actual file
            test_file = self.temp_dir / "text_file.txt"
            result = subprocess.run([
                sys.executable, "-c",
                f"import sys; sys.path.insert(0, '.'); from Artefact.cli import main; main()",
                "hash", str(test_file)
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode != 0:
                self.results['warnings'].append(f"CLI hash command failed: {result.stderr}")
            else:
                print("✓ CLI hash command")
            
            self.results['passed'] += 1
            return True
            
        except Exception as e:
            self.results['failed'] += 1
            self.results['critical_issues'].append(f"CLI test failed: {e}")
            traceback.print_exc()
            return False
    
    def test_performance(self) -> bool:
        """Test performance characteristics."""
        print("\n⚡ Testing Performance...")
        
        try:
            from Artefact.modules.hasher import hash_file
            
            # Create a larger test file (1MB)
            large_file = self.temp_dir / "large_test.dat"
            large_file.write_bytes(b"A" * (1024 * 1024))
            
            # Test hashing performance
            start_time = time.time()
            result = hash_file(large_file, "sha256")
            elapsed = time.time() - start_time
            
            throughput = (1024 * 1024) / elapsed / (1024 * 1024)  # MB/s
            print(f"✓ Hash performance: {throughput:.2f} MB/s ({elapsed:.3f}s for 1MB)")
            
            if elapsed > 5.0:
                self.results['performance_issues'].append(f"Slow hashing: {elapsed:.3f}s for 1MB file")
            
            self.results['passed'] += 1
            return True
            
        except Exception as e:
            self.results['failed'] += 1
            self.results['critical_issues'].append(f"Performance test failed: {e}")
            traceback.print_exc()
            return False
    
    def analyze_code_quality(self) -> Dict[str, Any]:
        """Analyze code quality and structure."""
        print("\n🔬 Analyzing Code Quality...")
        
        analysis = {
            'file_count': 0,
            'total_lines': 0,
            'python_files': [],
            'issues': []
        }
        
        try:
            artefact_dir = Path('Artefact')
            if not artefact_dir.exists():
                analysis['issues'].append("Main Artefact directory not found")
                return analysis
            
            # Analyze Python files
            for py_file in artefact_dir.rglob('*.py'):
                analysis['file_count'] += 1
                try:
                    content = py_file.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    analysis['total_lines'] += len(lines)
                    
                    file_analysis = {
                        'path': str(py_file),
                        'lines': len(lines),
                        'has_docstring': content.strip().startswith('"""') or content.strip().startswith("'''"),
                        'has_imports': 'import ' in content,
                        'has_main_guard': 'if __name__ == "__main__"' in content
                    }
                    analysis['python_files'].append(file_analysis)
                    
                    # Check for common issues
                    if len(lines) > 500:
                        analysis['issues'].append(f"Large file: {py_file} ({len(lines)} lines)")
                    
                    if not file_analysis['has_docstring'] and py_file.name != '__init__.py':
                        analysis['issues'].append(f"Missing docstring: {py_file}")
                    
                except Exception as e:
                    analysis['issues'].append(f"Failed to analyze {py_file}: {e}")
            
            print(f"✓ Analyzed {analysis['file_count']} Python files ({analysis['total_lines']} total lines)")
            
            # Check project structure
            expected_files = [
                'Artefact/__init__.py',
                'Artefact/cli.py',
                'Artefact/core.py',
                'Artefact/error_handler.py',
                'Artefact/modules/__init__.py',
                'Artefact/modules/hasher.py',
                'pyproject.toml',
                'README.md'
            ]
            
            missing_files = []
            for expected_file in expected_files:
                if not Path(expected_file).exists():
                    missing_files.append(expected_file)
            
            if missing_files:
                analysis['issues'].extend([f"Missing expected file: {f}" for f in missing_files])
            else:
                print("✓ All expected files present")
            
        except Exception as e:
            analysis['issues'].append(f"Code analysis failed: {e}")
        
        return analysis
    
    def cleanup_test_environment(self):
        """Clean up test environment."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up test environment: {self.temp_dir}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        print("=" * 80)
        print("🔍 COMPREHENSIVE ARTEFACT TESTING & CRITICAL ANALYSIS")
        print("=" * 80)
        
        try:
            # Setup
            if not self.setup_test_environment():
                return {"error": "Failed to setup test environment"}
            
            # Run all tests
            tests = [
                ("Imports & Structure", self.test_imports_and_structure),
                ("Hasher Functionality", self.test_hasher_functionality),
                ("Carving Functionality", self.test_carving_functionality),
                ("Metadata Extraction", self.test_metadata_functionality),
                ("Timeline Generation", self.test_timeline_functionality),
                ("Memory Analysis", self.test_memory_functionality),
                ("Error Handling", self.test_error_handling),
                ("CLI Interface", self.test_cli_functionality),
                ("Performance", self.test_performance)
            ]
            
            for test_name, test_func in tests:
                print(f"\n📋 Running: {test_name}")
                try:
                    success = test_func()
                    self.results['test_details'].append({
                        'name': test_name,
                        'passed': success,
                        'timestamp': time.time()
                    })
                except Exception as e:
                    self.results['failed'] += 1
                    self.results['critical_issues'].append(f"{test_name} crashed: {e}")
                    self.results['test_details'].append({
                        'name': test_name,
                        'passed': False,
                        'error': str(e),
                        'timestamp': time.time()
                    })
            
            # Code quality analysis
            code_analysis = self.analyze_code_quality()
            self.results['code_analysis'] = code_analysis
            
        finally:
            self.cleanup_test_environment()
        
        return self.results
    
    def print_critical_analysis(self, results: Dict[str, Any]):
        """Print detailed critical analysis."""
        print("\n" + "=" * 80)
        print("📊 CRITICAL ANALYSIS REPORT")
        print("=" * 80)
        
        # Test Results Summary
        total_tests = results['passed'] + results['failed']
        success_rate = (results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📈 TEST RESULTS SUMMARY:")
        print(f"   ✅ Passed: {results['passed']}")
        print(f"   ❌ Failed: {results['failed']}")
        print(f"   ⚠️  Warnings: {results['warnings']}")
        print(f"   📊 Success Rate: {success_rate:.1f}%")
        
        # Critical Issues
        if results['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES ({len(results['critical_issues'])}):")
            for i, issue in enumerate(results['critical_issues'], 1):
                print(f"   {i}. {issue}")
        else:
            print(f"\n✅ No critical issues found!")
        
        # Performance Issues
        if results['performance_issues']:
            print(f"\n⚡ PERFORMANCE ISSUES ({len(results['performance_issues'])}):")
            for i, issue in enumerate(results['performance_issues'], 1):
                print(f"   {i}. {issue}")
        
        # Code Quality Analysis
        if 'code_analysis' in results:
            analysis = results['code_analysis']
            print(f"\n📋 CODE QUALITY ANALYSIS:")
            print(f"   📁 Files: {analysis['file_count']} Python files")
            print(f"   📝 Lines: {analysis['total_lines']} total lines")
            print(f"   ⚠️  Issues: {len(analysis['issues'])}")
            
            if analysis['issues']:
                print(f"\n   Code Quality Issues:")
                for issue in analysis['issues'][:10]:  # Show first 10
                    print(f"      • {issue}")
                if len(analysis['issues']) > 10:
                    print(f"      ... and {len(analysis['issues']) - 10} more")
        
        # Overall Rating
        print(f"\n" + "=" * 80)
        print("🎯 OVERALL CRITICAL ASSESSMENT")
        print("=" * 80)
        
        if results['critical_issues']:
            rating = "❌ FAILING"
            recommendation = "Critical issues must be resolved before production use"
        elif success_rate < 80:
            rating = "⚠️  NEEDS WORK"  
            recommendation = "Several issues need attention before production ready"
        elif results['performance_issues'] or results['warnings'] > 3:
            rating = "⚠️  ACCEPTABLE"
            recommendation = "Minor issues should be addressed for optimal performance"
        else:
            rating = "✅ GOOD"
            recommendation = "Ready for production with minor monitoring"
        
        print(f"Rating: {rating}")
        print(f"Recommendation: {recommendation}")
        print("=" * 80)

def main():
    """Run comprehensive testing and analysis."""
    tester = CriticalTester()
    results = tester.run_all_tests()
    tester.print_critical_analysis(results)
    
    # Return appropriate exit code
    return 0 if results['failed'] == 0 and not results['critical_issues'] else 1

if __name__ == "__main__":
    sys.exit(main())
