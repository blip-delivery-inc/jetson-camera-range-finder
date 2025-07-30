#!/usr/bin/env python3
"""
Comprehensive Bug Checker for Jetson Orin Integration SDK

This script performs static analysis, syntax checking, and logical validation
to identify potential bugs and issues in the SDK code.

Author: Jetson Orin SDK
"""

import sys
import ast
import re
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BugReport:
    """Container for bug reports."""
    
    def __init__(self):
        self.critical_bugs = []
        self.warnings = []
        self.suggestions = []
        self.total_issues = 0
    
    def add_critical(self, file: str, line: int, message: str):
        self.critical_bugs.append({
            'file': file,
            'line': line,
            'message': message,
            'severity': 'CRITICAL'
        })
        self.total_issues += 1
    
    def add_warning(self, file: str, line: int, message: str):
        self.warnings.append({
            'file': file,
            'line': line,
            'message': message,
            'severity': 'WARNING'
        })
        self.total_issues += 1
    
    def add_suggestion(self, file: str, line: int, message: str):
        self.suggestions.append({
            'file': file,
            'line': line,
            'message': message,
            'severity': 'SUGGESTION'
        })
        self.total_issues += 1
    
    def summary(self):
        logger.info(f"\n{'='*60}")
        logger.info(f"BUG CHECK SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Critical Bugs: {len(self.critical_bugs)}")
        logger.info(f"Warnings: {len(self.warnings)}")
        logger.info(f"Suggestions: {len(self.suggestions)}")
        logger.info(f"Total Issues: {self.total_issues}")
        
        if self.critical_bugs:
            logger.error(f"\n🚨 CRITICAL BUGS:")
            for bug in self.critical_bugs:
                logger.error(f"  {bug['file']}:{bug['line']} - {bug['message']}")
        
        if self.warnings:
            logger.warning(f"\n⚠️  WARNINGS:")
            for warning in self.warnings:
                logger.warning(f"  {warning['file']}:{warning['line']} - {warning['message']}")
        
        if self.suggestions:
            logger.info(f"\n💡 SUGGESTIONS:")
            for suggestion in self.suggestions:
                logger.info(f"  {suggestion['file']}:{suggestion['line']} - {suggestion['message']}")
        
        return len(self.critical_bugs) == 0


def check_syntax_errors(file_path: str, report: BugReport) -> bool:
    """Check for Python syntax errors."""
    logger.info(f"Checking syntax for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Try to compile the code
        ast.parse(content)
        return True
    except SyntaxError as e:
        report.add_critical(file_path, e.lineno or 0, f"Syntax error: {e.msg}")
        return False
    except Exception as e:
        report.add_critical(file_path, 0, f"Parse error: {str(e)}")
        return False


def check_import_issues(file_path: str, report: BugReport):
    """Check for import-related issues."""
    logger.info(f"Checking imports for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for unused imports
        tree = ast.parse(content)
        imports = []
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
        
        # Check for potentially problematic imports
        problematic_imports = ['cv2', 'serial', 'numpy']
        for imp in imports:
            if imp in problematic_imports:
                # Check if there's a try-except block around imports
                if 'try:' in content and 'except ImportError:' in content:
                    continue
                else:
                    report.add_warning(file_path, 0, f"Import {imp} may fail on some systems - consider adding try-except")
        
    except Exception as e:
        report.add_warning(file_path, 0, f"Could not analyze imports: {str(e)}")


def check_error_handling(file_path: str, report: BugReport):
    """Check for proper error handling."""
    logger.info(f"Checking error handling for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Check for bare except clauses
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*except\s*:', line):
                report.add_warning(file_path, i, "Bare except clause - should specify exception type")
        
        # Check for missing error handling in critical operations
        critical_ops = ['open(', 'cv2.VideoCapture', 'serial.Serial', 'json.load', 'json.dump']
        for i, line in enumerate(lines, 1):
            for op in critical_ops:
                if op in line and 'try:' not in content[:content.find(line)]:
                    # Check if this line is in a try block
                    try_start = content.rfind('try:', 0, content.find(line))
                    if try_start == -1 or content.find('except', try_start, content.find(line)) == -1:
                        report.add_warning(file_path, i, f"Critical operation {op} may need error handling")
        
    except Exception as e:
        report.add_warning(file_path, 0, f"Could not analyze error handling: {str(e)}")


def check_resource_management(file_path: str, report: BugReport):
    """Check for proper resource management."""
    logger.info(f"Checking resource management for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Check for file operations without context managers
        for i, line in enumerate(lines, 1):
            if 'open(' in line and 'with ' not in line and 'as ' in line:
                # This might be a file operation without context manager
                if 'f.close()' not in content:
                    report.add_warning(file_path, i, "File operation without context manager - consider using 'with' statement")
        
        # Check for potential resource leaks
        resource_patterns = [
            (r'cv2\.VideoCapture\(', 'VideoCapture'),
            (r'serial\.Serial\(', 'Serial connection'),
            (r'threading\.Thread\(', 'Thread')
        ]
        
        for pattern, resource_name in resource_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                # Check if there's a corresponding close/release
                close_pattern = r'\.release\(\)|\.close\(\)'
                if not re.search(close_pattern, content[match.start():]):
                    report.add_warning(file_path, line_num, f"{resource_name} may not be properly closed")
        
    except Exception as e:
        report.add_warning(file_path, 0, f"Could not analyze resource management: {str(e)}")


def check_data_validation(file_path: str, report: BugReport):
    """Check for data validation issues."""
    logger.info(f"Checking data validation for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Check for potential division by zero
        for i, line in enumerate(lines, 1):
            if '/' in line and re.search(r'/\s*[a-zA-Z_][a-zA-Z0-9_]*', line):
                # Check if divisor is validated
                if 'if' not in line and 'assert' not in line:
                    report.add_warning(file_path, i, "Potential division by zero - validate divisor")
        
        # Check for potential index errors
        for i, line in enumerate(lines, 1):
            if '[' in line and ']' in line:
                # Look for array/list access
                if re.search(r'\[[a-zA-Z_][a-zA-Z0-9_]*\]', line):
                    report.add_suggestion(file_path, i, "Consider validating array index before access")
        
        # Check for potential None access
        for i, line in enumerate(lines, 1):
            if '.' in line and re.search(r'[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*', line):
                report.add_suggestion(file_path, i, "Consider checking for None before attribute access")
        
    except Exception as e:
        report.add_warning(file_path, 0, f"Could not analyze data validation: {str(e)}")


def check_threading_issues(file_path: str, report: BugReport):
    """Check for threading-related issues."""
    logger.info(f"Checking threading for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for potential race conditions
        if 'threading' in content:
            # Look for shared resources without locks
            shared_patterns = ['self.', 'global ']
            for pattern in shared_patterns:
                if pattern in content and 'threading.Lock' not in content:
                    report.add_warning(file_path, 0, "Shared resources detected without explicit locking")
        
        # Check for proper thread cleanup
        if 'threading.Thread' in content and '.join()' not in content:
            report.add_warning(file_path, 0, "Threads created but not joined - potential resource leak")
        
    except Exception as e:
        report.add_warning(file_path, 0, f"Could not analyze threading: {str(e)}")


def check_security_issues(file_path: str, report: BugReport):
    """Check for potential security issues."""
    logger.info(f"Checking security for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for potential command injection
        dangerous_patterns = [
            (r'os\.system\(', 'os.system'),
            (r'subprocess\.call\(', 'subprocess.call'),
            (r'eval\(', 'eval'),
            (r'exec\(', 'exec')
        ]
        
        for pattern, func_name in dangerous_patterns:
            if re.search(pattern, content):
                report.add_critical(file_path, 0, f"Potentially dangerous function {func_name} detected")
        
        # Check for hardcoded credentials
        credential_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        
        for pattern in credential_patterns:
            if re.search(pattern, content):
                report.add_critical(file_path, 0, "Hardcoded credentials detected")
        
    except Exception as e:
        report.add_warning(file_path, 0, f"Could not analyze security: {str(e)}")


def check_performance_issues(file_path: str, report: BugReport):
    """Check for potential performance issues."""
    logger.info(f"Checking performance for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for inefficient patterns
        inefficient_patterns = [
            (r'for.*in.*range\(len\(', 'Inefficient loop with range(len())'),
            (r'\.append\(.*\)\s*in\s*loop', 'List append in loop - consider list comprehension'),
            (r'string\s*\+\s*string', 'String concatenation in loop - consider join()')
        ]
        
        for pattern, message in inefficient_patterns:
            if re.search(pattern, content):
                report.add_suggestion(file_path, 0, message)
        
        # Check for potential memory leaks
        if 'while True:' in content and 'break' not in content:
            report.add_warning(file_path, 0, "Infinite loop detected - ensure proper exit condition")
        
    except Exception as e:
        report.add_warning(file_path, 0, f"Could not analyze performance: {str(e)}")


def check_configuration_issues(file_path: str, report: BugReport):
    """Check for configuration-related issues."""
    logger.info(f"Checking configuration for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for hardcoded paths
        hardcoded_paths = [
            r'/dev/video\d+',
            r'/dev/tty[A-Z]+\d+',
            r'/tmp/',
            r'/home/'
        ]
        
        for pattern in hardcoded_paths:
            if re.search(pattern, content):
                report.add_suggestion(file_path, 0, f"Hardcoded path detected: {pattern}")
        
        # Check for magic numbers
        magic_numbers = re.findall(r'\b\d{4,}\b', content)
        for num in magic_numbers:
            if int(num) > 1000:  # Likely a magic number
                report.add_suggestion(file_path, 0, f"Magic number detected: {num}")
        
    except Exception as e:
        report.add_warning(file_path, 0, f"Could not analyze configuration: {str(e)}")


def check_documentation_issues(file_path: str, report: BugReport):
    """Check for documentation issues."""
    logger.info(f"Checking documentation for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for functions without docstrings
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    report.add_suggestion(file_path, node.lineno, f"Function '{node.name}' missing docstring")
            elif isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    report.add_suggestion(file_path, node.lineno, f"Class '{node.name}' missing docstring")
        
        # Check for TODO/FIXME comments
        todo_patterns = [r'TODO', r'FIXME', r'XXX', r'HACK']
        for pattern in todo_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                report.add_warning(file_path, 0, f"TODO/FIXME comment detected: {pattern}")
        
    except Exception as e:
        report.add_warning(file_path, 0, f"Could not analyze documentation: {str(e)}")


def check_json_validation(file_path: str, report: BugReport):
    """Check for JSON-related issues."""
    logger.info(f"Checking JSON handling for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for JSON operations without error handling
        json_ops = ['json.load(', 'json.dump(', 'json.loads(', 'json.dumps(']
        for op in json_ops:
            if op in content:
                # Check if there's error handling around JSON operations
                if 'try:' not in content or 'except' not in content:
                    report.add_warning(file_path, 0, f"JSON operation {op} without error handling")
        
        # Check for potential JSON injection
        if 'json.loads(' in content and 'input(' in content:
            report.add_critical(file_path, 0, "Potential JSON injection - validate input before parsing")
        
    except Exception as e:
        report.add_warning(file_path, 0, f"Could not analyze JSON handling: {str(e)}")


def check_file_operations(file_path: str, report: BugReport):
    """Check for file operation issues."""
    logger.info(f"Checking file operations for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for potential file path issues
        if 'Path(' in content:
            # Check for proper path handling
            if 'exists()' not in content and 'mkdir' in content:
                report.add_warning(file_path, 0, "Directory creation without existence check")
        
        # Check for potential file permission issues
        if 'open(' in content and 'w' in content:
            report.add_suggestion(file_path, 0, "File write operation - consider permission handling")
        
        # Check for potential file size issues
        if 'read(' in content and 'size' not in content:
            report.add_suggestion(file_path, 0, "File read operation - consider size limits")
        
    except Exception as e:
        report.add_warning(file_path, 0, f"Could not analyze file operations: {str(e)}")


def run_comprehensive_bug_check():
    """Run comprehensive bug checking on all SDK files."""
    logger.info("Starting comprehensive bug check...")
    
    report = BugReport()
    
    # Files to check
    python_files = ['camera.py', 'lidar.py', 'main.py']
    
    for file_path in python_files:
        if not Path(file_path).exists():
            report.add_critical(file_path, 0, "File not found")
            continue
        
        logger.info(f"\n--- Checking {file_path} ---")
        
        # Run all checks
        check_syntax_errors(file_path, report)
        check_import_issues(file_path, report)
        check_error_handling(file_path, report)
        check_resource_management(file_path, report)
        check_data_validation(file_path, report)
        check_threading_issues(file_path, report)
        check_security_issues(file_path, report)
        check_performance_issues(file_path, report)
        check_configuration_issues(file_path, report)
        check_documentation_issues(file_path, report)
        check_json_validation(file_path, report)
        check_file_operations(file_path, report)
    
    # Generate summary
    return report.summary()


if __name__ == "__main__":
    success = run_comprehensive_bug_check()
    sys.exit(0 if success else 1)