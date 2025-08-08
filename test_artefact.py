#!/usr/bin/env python3
"""
Test script to verify Artefact functionality without installation issues.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from Artefact import __version__, __codename__
        print(f"✓ Artefact {__version__} ({__codename__})")
    except ImportError as e:
        print(f"✗ Failed to import Artefact: {e}")
        return False
    
    try:
        from Artefact.modules.hasher import hash_file, hash_directory
        print("✓ Hasher module imported")
    except ImportError as e:
        print(f"✗ Failed to import hasher: {e}")
        return False
    
    try:
        from Artefact.modules.carving import carve_files
        print("✓ Carving module imported")
    except ImportError as e:
        print(f"✗ Failed to import carving: {e}")
        return False
    
    try:
        from Artefact.modules.metadata import extract_metadata
        print("✓ Metadata module imported")
    except ImportError as e:
        print(f"✗ Failed to import metadata: {e}")
        return False
    
    try:
        from Artefact.modules.timeline import extract_file_timestamps, TimelineEvent
        print("✓ Timeline module imported")
    except ImportError as e:
        print(f"✗ Failed to import timeline: {e}")
        return False
    
    try:
        from Artefact.modules.memory import extract_strings, extract_iocs
        print("✓ Memory module imported")
    except ImportError as e:
        print(f"✗ Failed to import memory: {e}")
        return False
    
    try:
        from Artefact.modules.liveops import list_processes
        print("✓ Liveops module imported")
    except ImportError as e:
        print(f"✗ Failed to import liveops: {e}")
        return False
    
    try:
        from Artefact.modules.mount import list_partitions
        print("✓ Mount module imported")
    except ImportError as e:
        print(f"✗ Failed to import mount: {e}")
        return False
    
    try:
        from Artefact.error_handler import handle_error
        print("✓ Error handler imported")
    except ImportError as e:
        print(f"✗ Failed to import error handler: {e}")
        return False
    
    try:
        from Artefact.core import get_config, get_logger
        print("✓ Core utilities imported")
    except ImportError as e:
        print(f"✗ Failed to import core: {e}")
        return False
    
    try:
        from Artefact.console import interactive_mode
        print("✓ Console utilities imported")
    except ImportError as e:
        print(f"✗ Failed to import console: {e}")
        return False
    
    return True

def test_hasher():
    """Test the hasher functionality."""
    print("\nTesting hasher functionality...")
    
    try:
        from Artefact.modules.hasher import hash_file, SUPPORTED_ALGORITHMS
        from pathlib import Path
        import tempfile
        
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_file = Path(f.name)
        
        # Test each algorithm
        for algorithm in SUPPORTED_ALGORITHMS.keys():
            result = hash_file(temp_file, algorithm)
            print(f"✓ {algorithm.upper()}: {result}")
        
        # Clean up
        temp_file.unlink()
        print("✓ Hasher functionality working")
        return True
    
    except Exception as e:
        print(f"✗ Hasher test failed: {e}")
        return False

def test_error_handler():
    """Test the error handler."""
    print("\nTesting error handler...")
    
    try:
        from Artefact.error_handler import handle_error, ArtefactError
        
        # Test custom exception
        try:
            raise ArtefactError("Test error")
        except ArtefactError as e:
            handle_error(e, context="test")
        
        print("✓ Error handler working")
        return True
    
    except Exception as e:
        print(f"✗ Error handler test failed: {e}")
        return False

def test_timeline():
    """Test timeline functionality."""
    print("\nTesting timeline functionality...")
    
    try:
        from Artefact.modules.timeline import extract_file_timestamps, TimelineEvent, timeline_to_markdown
        from datetime import datetime
        import tempfile
        import os
        
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content")
            temp_file = f.name
        
        # Extract timestamps
        events = extract_file_timestamps(temp_file)
        print(f"✓ Extracted {len(events)} timeline events")
        
        # Test timeline export
        if events:
            markdown = timeline_to_markdown(events)
            print("✓ Timeline markdown export working")
        
        # Clean up
        os.unlink(temp_file)
        return True
    
    except Exception as e:
        print(f"✗ Timeline test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Artefact Functionality Test ===\n")
    
    tests = [
        test_imports,
        test_hasher,
        test_error_handler,
        test_timeline
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
