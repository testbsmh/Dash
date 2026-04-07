#!/usr/bin/env python3
"""
Backend testing script for WorkspaceONE Desktop App
Tests Python modules, imports, configuration, and dependencies
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

class DesktopAppTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
    def run_test(self, name, test_func):
        """Run a single test"""
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            result = test_func()
            if result:
                self.tests_passed += 1
                print(f"✅ Passed - {name}")
                return True
            else:
                print(f"❌ Failed - {name}")
                return False
        except Exception as e:
            print(f"❌ Failed - {name}: {str(e)}")
            return False

    def test_python_imports(self):
        """Test that all Python modules can be imported"""
        try:
            # Add the desktop_app directory to Python path
            sys.path.insert(0, self.base_dir)
            
            # Test main.py imports
            import main
            print("  ✓ main.py imported successfully")
            
            # Test config.py imports
            import config
            print("  ✓ config.py imported successfully")
            
            # Test api.py imports
            import api
            print("  ✓ api.py imported successfully")
            
            return True
        except ImportError as e:
            print(f"  ❌ Import error: {e}")
            return False
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            return False

    def test_config_class(self):
        """Test Config class functionality"""
        try:
            sys.path.insert(0, self.base_dir)
            from config import Config
            
            # Create a temporary directory for testing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Mock the config directory
                original_config_dir = None
                config_instance = Config()
                original_config_dir = config_instance.config_dir
                
                # Override config directory for testing
                test_config_dir = Path(temp_dir) / 'test_config'
                config_instance.config_dir = test_config_dir
                config_instance.config_file = test_config_dir / 'config.json'
                
                # Test saving configuration
                test_config = {
                    'clientId': 'test_client_id',
                    'clientSecret': 'test_secret',
                    'tokenUrl': 'https://test.example.com/token'
                }
                
                result = config_instance.save(test_config)
                if not result:
                    print("  ❌ Config save returned False")
                    return False
                
                print("  ✓ Config save successful")
                
                # Test that config file was created
                if not config_instance.config_file.exists():
                    print("  ❌ Config file was not created")
                    return False
                
                print("  ✓ Config file created")
                
                # Test loading configuration
                loaded_config = config_instance.get_all()
                if loaded_config.get('clientId') != 'test_client_id':
                    print("  ❌ Config not loaded correctly")
                    return False
                
                print("  ✓ Config loaded correctly")
                
                # Test get method
                client_id = config_instance.get('clientId')
                if client_id != 'test_client_id':
                    print("  ❌ Config get method failed")
                    return False
                
                print("  ✓ Config get method works")
                
                return True
                
        except Exception as e:
            print(f"  ❌ Config test error: {e}")
            return False

    def test_api_class(self):
        """Test API class initialization"""
        try:
            sys.path.insert(0, self.base_dir)
            from api import WS1API
            from config import Config
            
            # Create a mock config
            config = Config()
            config.config = {
                'tokenUrl': 'https://auth.na1.data.vmwservices.com/oauth/token',
                'clientId': 'test_client',
                'clientSecret': 'test_secret',
                'intelBase': 'https://api.na1.data.workspaceone.com'
            }
            
            # Test API initialization
            api = WS1API(config)
            
            if not hasattr(api, 'config'):
                print("  ❌ API missing config attribute")
                return False
            
            if not hasattr(api, 'access_token'):
                print("  ❌ API missing access_token attribute")
                return False
            
            if not hasattr(api, 'token_expiry'):
                print("  ❌ API missing token_expiry attribute")
                return False
            
            print("  ✓ API class initialized with required attributes")
            
            # Test that methods exist
            if not hasattr(api, 'get_token'):
                print("  ❌ API missing get_token method")
                return False
            
            if not hasattr(api, 'fetch_intelligence_data'):
                print("  ❌ API missing fetch_intelligence_data method")
                return False
            
            if not hasattr(api, 'fetch_assignments'):
                print("  ❌ API missing fetch_assignments method")
                return False
            
            print("  ✓ API class has all required methods")
            
            return True
            
        except Exception as e:
            print(f"  ❌ API test error: {e}")
            return False

    def test_html_file(self):
        """Test that HTML file exists and is valid"""
        try:
            html_path = os.path.join(self.base_dir, 'index.html')
            
            if not os.path.exists(html_path):
                print("  ❌ index.html file not found")
                return False
            
            print("  ✓ index.html file exists")
            
            # Read and validate basic HTML structure
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                print("  ❌ index.html is empty")
                return False
            
            # Check for basic HTML structure
            if '<!DOCTYPE html>' not in content:
                print("  ❌ Missing DOCTYPE declaration")
                return False
            
            if '<html' not in content:
                print("  ❌ Missing html tag")
                return False
            
            if '<head>' not in content:
                print("  ❌ Missing head section")
                return False
            
            if '<body>' not in content:
                print("  ❌ Missing body section")
                return False
            
            print("  ✓ HTML file has valid structure")
            
            # Check for WorkspaceONE specific content
            if 'WorkspaceONE' not in content:
                print("  ❌ Missing WorkspaceONE content")
                return False
            
            if 'pywebview' not in content:
                print("  ❌ Missing pywebview integration")
                return False
            
            print("  ✓ HTML file contains expected content")
            
            return True
            
        except Exception as e:
            print(f"  ❌ HTML test error: {e}")
            return False

    def test_build_script(self):
        """Test PyInstaller build script syntax"""
        try:
            build_path = os.path.join(self.base_dir, 'build.py')
            
            if not os.path.exists(build_path):
                print("  ❌ build.py file not found")
                return False
            
            print("  ✓ build.py file exists")
            
            # Test syntax by compiling
            with open(build_path, 'r') as f:
                content = f.read()
            
            try:
                compile(content, build_path, 'exec')
                print("  ✓ build.py has valid Python syntax")
            except SyntaxError as e:
                print(f"  ❌ build.py syntax error: {e}")
                return False
            
            # Check for PyInstaller import
            if 'PyInstaller' not in content:
                print("  ❌ Missing PyInstaller import")
                return False
            
            print("  ✓ build.py contains PyInstaller import")
            
            # Check for main function
            if 'def build(' not in content:
                print("  ❌ Missing build function")
                return False
            
            print("  ✓ build.py has build function")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Build script test error: {e}")
            return False

    def test_dependencies(self):
        """Test that required dependencies are available"""
        try:
            requirements_path = os.path.join(self.base_dir, 'requirements.txt')
            
            if not os.path.exists(requirements_path):
                print("  ❌ requirements.txt not found")
                return False
            
            print("  ✓ requirements.txt exists")
            
            # Read requirements
            with open(requirements_path, 'r') as f:
                requirements = f.read().strip().split('\n')
            
            required_packages = []
            for req in requirements:
                if req.strip() and not req.strip().startswith('#'):
                    package_name = req.split('>=')[0].split('==')[0].strip()
                    required_packages.append(package_name)
            
            print(f"  ✓ Found {len(required_packages)} required packages")
            
            # Test imports for each package
            missing_packages = []
            for package in required_packages:
                try:
                    if package == 'pywebview':
                        import webview
                        print(f"  ✓ {package} is available")
                    elif package == 'requests':
                        import requests
                        print(f"  ✓ {package} is available")
                    elif package == 'pyinstaller':
                        import PyInstaller
                        print(f"  ✓ {package} is available")
                    else:
                        __import__(package)
                        print(f"  ✓ {package} is available")
                except ImportError:
                    missing_packages.append(package)
                    print(f"  ❌ {package} is missing")
            
            if missing_packages:
                print(f"  ❌ Missing packages: {', '.join(missing_packages)}")
                return False
            
            print("  ✅ All required dependencies are available")
            return True
            
        except Exception as e:
            print(f"  ❌ Dependencies test error: {e}")
            return False

    def test_main_api_class(self):
        """Test the API class in main.py"""
        try:
            sys.path.insert(0, self.base_dir)
            from main import API
            
            # Test API class initialization
            api = API()
            
            if not hasattr(api, 'config'):
                print("  ❌ Main API missing config attribute")
                return False
            
            if not hasattr(api, 'ws1_api'):
                print("  ❌ Main API missing ws1_api attribute")
                return False
            
            print("  ✓ Main API class initialized correctly")
            
            # Test methods exist
            required_methods = ['get_config', 'save_config', 'fetch_data', 'fetch_assignments']
            for method in required_methods:
                if not hasattr(api, method):
                    print(f"  ❌ Main API missing {method} method")
                    return False
            
            print("  ✓ Main API class has all required methods")
            
            # Test get_config method
            config = api.get_config()
            if not isinstance(config, dict):
                print("  ❌ get_config should return a dictionary")
                return False
            
            print("  ✓ get_config method works")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Main API test error: {e}")
            return False

def main():
    """Main test runner"""
    print("🚀 Starting WorkspaceONE Desktop App Backend Tests")
    print("=" * 60)
    
    tester = DesktopAppTester()
    
    # Run all tests
    tests = [
        ("Python Module Imports", tester.test_python_imports),
        ("Config Class Functionality", tester.test_config_class),
        ("API Class Initialization", tester.test_api_class),
        ("Main API Class", tester.test_main_api_class),
        ("HTML File Validation", tester.test_html_file),
        ("Build Script Syntax", tester.test_build_script),
        ("Required Dependencies", tester.test_dependencies),
    ]
    
    for test_name, test_func in tests:
        tester.run_test(test_name, test_func)
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Desktop app backend is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())