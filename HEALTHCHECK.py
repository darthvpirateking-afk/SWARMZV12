# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
SWARMZ Health Check Script

Automated system validation that:
1. Tests module imports
2. Runs test suite
3. Validates plugins
4. Tests core functionality
5. Generates health report
"""

import sys
import os
import importlib
import subprocess
from typing import Dict


class HealthChecker:
    """Comprehensive system health checker."""
    
    def __init__(self):
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
        self.total_checks = 0
        
    def check(self, name: str, func) -> bool:
        """Run a health check and record result."""
        self.total_checks += 1
        try:
            result = func()
            if result:
                self.results["passed"].append(name)
                print(f"  âœ“ {name}")
                return True
            else:
                self.results["failed"].append(name)
                print(f"  âœ— {name}")
                return False
        except Exception as e:
            self.results["failed"].append(f"{name}: {str(e)}")
            print(f"  âœ— {name}: {str(e)}")
            return False
    
    def warning(self, message: str):
        """Record a warning."""
        self.results["warnings"].append(message)
        print(f"  âš  {message}")
    
    def check_imports(self) -> bool:
        """Check that all core modules can be imported."""
        print("\n[1/7] Checking module imports...")
        
        modules = [
            "swarmz",
            "swarmz_cli",
            "examples",
            "test_swarmz",
            "plugins.filesystem",
            "plugins.dataprocessing"
        ]
        
        all_ok = True
        for module_name in modules:
            try:
                importlib.import_module(module_name)
                self.check(f"Import {module_name}", lambda: True)
            except Exception as e:
                self.check(f"Import {module_name}", lambda: False)
                all_ok = False
        
        return all_ok
    
    def check_core_system(self) -> bool:
        """Check core system initialization."""
        print("\n[2/7] Checking core system...")
        
        try:
            from swarmz import SwarmzCore
            
            # Test initialization
            if not self.check("SwarmzCore initialization", lambda: SwarmzCore() is not None):
                return False
            
            swarmz = SwarmzCore()
            
            # Test capabilities listing
            self.check("List capabilities", lambda: len(swarmz.list_capabilities()) > 0)
            
            # Test audit log
            self.check("Audit log access", lambda: isinstance(swarmz.get_audit_log(), list))
            
            return True
            
        except Exception as e:
            print(f"  âœ— Core system error: {e}")
            return False
    
    def check_builtin_tasks(self) -> bool:
        """Check built-in tasks work."""
        print("\n[3/7] Checking built-in tasks...")
        
        try:
            from swarmz import SwarmzCore
            swarmz = SwarmzCore()
            
            # Test echo task
            result = swarmz.execute("echo", message="test")
            self.check("Echo task", lambda: result == "Echo: test")
            
            # Test system_info task
            result = swarmz.execute("system_info")
            self.check("System info task", lambda: isinstance(result, dict) and "platform" in result)
            
            # Test execute_python task
            result = swarmz.execute("execute_python", code="result = 2 + 2")
            self.check("Execute Python task", lambda: result == 4)
            
            return True
            
        except Exception as e:
            print(f"  âœ— Built-in tasks error: {e}")
            return False
    
    def check_plugins(self) -> bool:
        """Check plugin loading and functionality."""
        print("\n[4/7] Checking plugins...")
        
        try:
            from swarmz import SwarmzCore
            swarmz = SwarmzCore()
            
            # Test filesystem plugin
            plugin_path = "plugins/filesystem.py"
            if os.path.exists(plugin_path):
                plugin_name = swarmz.load_plugin(plugin_path)
                self.check("Load filesystem plugin", lambda: plugin_name == "filesystem")
                
                # Test a filesystem task
                tasks = swarmz.list_capabilities()
                self.check("Filesystem tasks registered", lambda: any("fs_" in task for task in tasks))
            else:
                self.warning("Filesystem plugin not found")
            
            # Test data processing plugin
            plugin_path = "plugins/dataprocessing.py"
            if os.path.exists(plugin_path):
                plugin_name = swarmz.load_plugin(plugin_path)
                self.check("Load dataprocessing plugin", lambda: plugin_name == "dataprocessing")
                
                # Test a data processing task
                tasks = swarmz.list_capabilities()
                self.check("Data processing tasks registered", lambda: any("data_" in task for task in tasks))
            else:
                self.warning("Data processing plugin not found")
            
            return True
            
        except Exception as e:
            print(f"  âœ— Plugin error: {e}")
            return False
    
    def check_configuration(self) -> bool:
        """Check configuration loading."""
        print("\n[5/7] Checking configuration...")
        
        # Check config.json exists
        if os.path.exists("config.json"):
            self.check("config.json exists", lambda: True)
            
            try:
                import json
                with open("config.json") as f:
                    config = json.load(f)
                
                self.check("config.json valid JSON", lambda: True)
                self.check("Config has system_name", lambda: "system_name" in config)
                self.check("Config has operator_sovereignty", lambda: "operator_sovereignty" in config)
                
            except Exception as e:
                self.check("config.json parsing", lambda: False)
                return False
        else:
            self.warning("config.json not found (optional)")
        
        return True
    
    def run_test_suite(self) -> bool:
        """Run the complete test suite."""
        print("\n[6/7] Running test suite...")
        
        if not os.path.exists("test_swarmz.py"):
            self.warning("test_swarmz.py not found")
            return False
        
        try:
            # Run tests
            result = subprocess.run(
                [sys.executable, "test_swarmz.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check if tests passed - look for success indicators
            passed = result.returncode == 0 and ("OK" in result.stdout or "Success rate: 100" in result.stdout)
            
            if passed:
                # Extract test count
                for line in result.stdout.split('\n'):
                    if "Ran" in line and "test" in line:
                        print(f"  âœ“ {line.strip()}")
                    elif "Success rate: 100" in line:
                        print(f"  âœ“ {line.strip()}")
                self.check("Test suite passed", lambda: True)
            else:
                print(f"  âœ— Test suite failed")
                print(result.stdout)
                self.check("Test suite passed", lambda: False)
            
            return passed
            
        except subprocess.TimeoutExpired:
            print("  âœ— Test suite timed out")
            self.check("Test suite passed", lambda: False)
            return False
        except Exception as e:
            print(f"  âœ— Test suite error: {e}")
            self.check("Test suite passed", lambda: False)
            return False
    
    def check_file_structure(self) -> bool:
        """Check expected file structure."""
        print("\n[7/7] Checking file structure...")
        
        required_files = [
            "swarmz.py",
            "swarmz_cli.py",
            "README.md"
        ]
        
        for filename in required_files:
            exists = os.path.exists(filename)
            self.check(f"File {filename} exists", lambda e=exists: e)
        
        # Check plugins directory
        plugins_dir = "plugins"
        if os.path.isdir(plugins_dir):
            self.check("Plugins directory exists", lambda: True)
            
            # Check for __init__.py
            init_file = os.path.join(plugins_dir, "__init__.py")
            self.check("plugins/__init__.py exists", lambda: os.path.exists(init_file))
        else:
            self.warning("Plugins directory not found")
        
        return True
    
    def generate_report(self) -> Dict:
        """Generate final health report."""
        passed_count = len(self.results["passed"])
        failed_count = len(self.results["failed"])
        warning_count = len(self.results["warnings"])
        
        success_rate = (passed_count / self.total_checks * 100) if self.total_checks > 0 else 0
        
        print("\n" + "="*60)
        print("HEALTH CHECK REPORT")
        print("="*60)
        print(f"Total Checks: {self.total_checks}")
        print(f"Passed: {passed_count} âœ“")
        print(f"Failed: {failed_count} âœ—")
        print(f"Warnings: {warning_count} âš ")
        print(f"Success Rate: {success_rate:.1f}%")
        print("="*60)
        
        if failed_count > 0:
            print("\nFailed Checks:")
            for failure in self.results["failed"]:
                print(f"  âœ— {failure}")
        
        if warning_count > 0:
            print("\nWarnings:")
            for warning in self.results["warnings"]:
                print(f"  âš  {warning}")
        
        # Overall status
        print("\n" + "="*60)
        if failed_count == 0:
            print("STATUS: âœ“ HEALTHY - All checks passed!")
            status = "HEALTHY"
        elif failed_count <= 2:
            print("STATUS: âš  DEGRADED - Some issues detected")
            status = "DEGRADED"
        else:
            print("STATUS: âœ— UNHEALTHY - Multiple failures detected")
            status = "UNHEALTHY"
        print("="*60)
        
        return {
            "status": status,
            "total_checks": self.total_checks,
            "passed": passed_count,
            "failed": failed_count,
            "warnings": warning_count,
            "success_rate": success_rate,
            "details": self.results
        }


def main():
    """Run health check."""
    print("="*60)
    print("SWARMZ HEALTH CHECK")
    print("="*60)
    print("Validating system integrity and functionality...\n")
    
    checker = HealthChecker()
    
    # Run all checks
    checker.check_imports()
    checker.check_core_system()
    checker.check_builtin_tasks()
    checker.check_plugins()
    checker.check_configuration()
    checker.run_test_suite()
    checker.check_file_structure()
    
    # Generate report
    report = checker.generate_report()
    
    # Exit with appropriate code
    if report["status"] == "HEALTHY":
        sys.exit(0)
    elif report["status"] == "DEGRADED":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()

