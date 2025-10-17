#!/usr/bin/env python3
"""
Test runner for SmartRoommate+ application
Run this script to execute all tests
"""

import subprocess
import sys
import os

def run_tests():
    """Run all tests with pytest"""
    print("🧪 Running SmartRoommate+ Test Suite")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Test commands
    test_commands = [
        {
            "name": "Unit Tests",
            "command": ["python", "-m", "pytest", "tests/test_app.py", "-v", "--tb=short"],
            "description": "Testing core application functionality"
        },
        {
            "name": "Matching Engine Tests", 
            "command": ["python", "-m", "pytest", "tests/test_matching_engine.py", "-v", "--tb=short"],
            "description": "Testing AI matching algorithms"
        },
        {
            "name": "Database Tests",
            "command": ["python", "-m", "pytest", "tests/test_database.py", "-v", "--tb=short"],
            "description": "Testing database operations"
        },
        {
            "name": "Schema Validation Tests",
            "command": ["python", "-m", "pytest", "tests/test_schemas.py", "-v", "--tb=short"],
            "description": "Testing data validation"
        },
        {
            "name": "Integration Tests",
            "command": ["python", "-m", "pytest", "tests/test_integration.py", "-v", "--tb=short"],
            "description": "Testing end-to-end functionality"
        },
        {
            "name": "Performance Tests",
            "command": ["python", "-m", "pytest", "tests/test_performance.py", "-v", "--tb=short"],
            "description": "Testing application performance"
        }
    ]
    
    # Run all tests
    all_tests_command = ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "--color=yes"]
    
    print("🚀 Running All Tests...")
    print("-" * 30)
    
    try:
        result = subprocess.run(all_tests_command, capture_output=True, text=True)
        
        print("📊 Test Results:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  Warnings/Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ All tests passed successfully!")
            return True
        else:
            print("❌ Some tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_specific_test(test_file):
    """Run a specific test file"""
    print(f"🧪 Running {test_file}")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            "python", "-m", "pytest", f"tests/{test_file}", "-v", "--tb=short", "--color=yes"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def run_coverage():
    """Run tests with coverage report"""
    print("📊 Running Tests with Coverage")
    print("=" * 50)
    
    try:
        # Install coverage if not available
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest-cov"], check=True)
        
        result = subprocess.run([
            "python", "-m", "pytest", "tests/", "--cov=backend", "--cov-report=html", "--cov-report=term", "-v"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        print("📈 Coverage report generated in htmlcov/index.html")
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running coverage: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "coverage":
            success = run_coverage()
        elif command.endswith(".py"):
            success = run_specific_test(command)
        else:
            print(f"Unknown command: {command}")
            print("Available commands:")
            print("  python test_runner.py          # Run all tests")
            print("  python test_runner.py coverage # Run with coverage")
            print("  python test_runner.py test_app.py # Run specific test")
            success = False
    else:
        success = run_tests()
    
    sys.exit(0 if success else 1)

