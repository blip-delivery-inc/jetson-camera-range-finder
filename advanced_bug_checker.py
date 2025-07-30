#!/usr/bin/env python3
"""
Advanced Bug Checker for Jetson Orin Integration SDK

This script performs deep static analysis, logic validation, and advanced
code quality checks to identify subtle bugs and code mistakes.

Author: Jetson Orin SDK
"""

import sys
import ast
import re
import json
import tempfile
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Set

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AdvancedBugReport:
    """Container for advanced bug reports."""
    
    def __init__(self):
        self.critical_bugs = []
        self.logic_errors = []
        self.race_conditions = []
        self.memory_leaks = []
        self.performance_issues = []
        self.code_smells = []
        self.suggestions = []
        self.total_issues = 0
    
    def add_critical(self, file: str, line: int, message: str, category: str = "CRITICAL"):
        self.critical_bugs.append({
            'file': file,
            'line': line,
            'message': message,
            'category': category,
            'severity': 'CRITICAL'
        })
        self.total_issues += 1
    
    def add_logic_error(self, file: str, line: int, message: str):
        self.logic_errors.append({
            'file': file,
            'line': line,
            'message': message,
            'severity': 'LOGIC_ERROR'
        })
        self.total_issues += 1
    
    def add_race_condition(self, file: str, line: int, message: str):
        self.race_conditions.append({
            'file': file,
            'line': line,
            'message': message,
            'severity': 'RACE_CONDITION'
        })
        self.total_issues += 1
    
    def add_memory_leak(self, file: str, line: int, message: str):
        self.memory_leaks.append({
            'file': file,
            'line': line,
            'message': message,
            'severity': 'MEMORY_LEAK'
        })
        self.total_issues += 1
    
    def add_performance_issue(self, file: str, line: int, message: str):
        self.performance_issues.append({
            'file': file,
            'line': line,
            'message': message,
            'severity': 'PERFORMANCE'
        })
        self.total_issues += 1
    
    def add_code_smell(self, file: str, line: int, message: str):
        self.code_smells.append({
            'file': file,
            'line': line,
            'message': message,
            'severity': 'CODE_SMELL'
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
        logger.info(f"\n{'='*70}")
        logger.info(f"ADVANCED BUG CHECK SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Critical Bugs: {len(self.critical_bugs)}")
        logger.info(f"Logic Errors: {len(self.logic_errors)}")
        logger.info(f"Race Conditions: {len(self.race_conditions)}")
        logger.info(f"Memory Leaks: {len(self.memory_leaks)}")
        logger.info(f"Performance Issues: {len(self.performance_issues)}")
        logger.info(f"Code Smells: {len(self.code_smells)}")
        logger.info(f"Suggestions: {len(self.suggestions)}")
        logger.info(f"Total Issues: {self.total_issues}")
        
        if self.critical_bugs:
            logger.error(f"\n🚨 CRITICAL BUGS:")
            for bug in self.critical_bugs:
                logger.error(f"  {bug['file']}:{bug['line']} - {bug['message']} ({bug['category']})")
        
        if self.logic_errors:
            logger.error(f"\n🧠 LOGIC ERRORS:")
            for error in self.logic_errors:
                logger.error(f"  {error['file']}:{error['line']} - {error['message']}")
        
        if self.race_conditions:
            logger.warning(f"\n🏃 RACE CONDITIONS:")
            for race in self.race_conditions:
                logger.warning(f"  {race['file']}:{race['line']} - {race['message']}")
        
        if self.memory_leaks:
            logger.warning(f"\n💾 MEMORY LEAKS:")
            for leak in self.memory_leaks:
                logger.warning(f"  {leak['file']}:{leak['line']} - {leak['message']}")
        
        if self.performance_issues:
            logger.warning(f"\n⚡ PERFORMANCE ISSUES:")
            for perf in self.performance_issues:
                logger.warning(f"  {perf['file']}:{perf['line']} - {perf['message']}")
        
        if self.code_smells:
            logger.info(f"\n👃 CODE SMELLS:")
            for smell in self.code_smells:
                logger.info(f"  {smell['file']}:{smell['line']} - {smell['message']}")
        
        if self.suggestions:
            logger.info(f"\n💡 SUGGESTIONS:")
            for suggestion in self.suggestions:
                logger.info(f"  {suggestion['file']}:{suggestion['line']} - {suggestion['message']}")
        
        return len(self.critical_bugs) == 0 and len(self.logic_errors) == 0


def check_logic_errors(file_path: str, report: AdvancedBugReport):
    """Check for logical errors and inconsistencies."""
    logger.info(f"Checking logic for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Check for unreachable code
        for i, line in enumerate(lines, 1):
            if 'return' in line and i < len(lines):
                # Check if there's code after return
                next_lines = lines[i:]
                for j, next_line in enumerate(next_lines):
                    if next_line.strip() and not next_line.strip().startswith('#'):
                        if 'def ' not in next_line and 'class ' not in next_line:
                            report.add_logic_error(file_path, i + j + 1, "Unreachable code after return statement")
                        break
        
        # Check for infinite loops
        for i, line in enumerate(lines, 1):
            if 'while True:' in line:
                # Look for break or return in the loop
                loop_content = content[content.find(line):]
                if 'break' not in loop_content and 'return' not in loop_content:
                    report.add_logic_error(file_path, i, "Potential infinite loop without exit condition")
        
        # Check for dead code (unused variables)
        tree = ast.parse(content)
        defined_vars = set()
        used_vars = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_vars.add(target.id)
            elif isinstance(node, ast.Name):
                used_vars.add(node.id)
        
        unused_vars = defined_vars - used_vars
        for var in unused_vars:
            if not var.startswith('_') and var not in ['self', 'cls']:
                report.add_code_smell(file_path, 0, f"Unused variable: {var}")
        
        # Check for redundant conditions
        for i, line in enumerate(lines, 1):
            if 'if ' in line and ' and ' in line:
                conditions = line.split(' and ')
                for condition in conditions:
                    if condition.strip() in ['True', 'False']:
                        report.add_logic_error(file_path, i, f"Redundant condition: {condition.strip()}")
        
    except Exception as e:
        report.add_critical(file_path, 0, f"Could not analyze logic: {str(e)}")


def check_race_conditions(file_path: str, report: AdvancedBugReport):
    """Check for potential race conditions."""
    logger.info(f"Checking race conditions for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for shared mutable state
        if 'self.' in content and 'threading' in content:
            # Look for shared attributes that might be modified
            shared_patterns = [
                r'self\.\w+\s*=\s*\w+',  # Assignment to self attributes
                r'self\.\w+\s*\+=',       # Increment operations
                r'self\.\w+\s*-=',        # Decrement operations
                r'self\.\w+\.append',     # List modifications
                r'self\.\w+\.extend',     # List modifications
                r'self\.\w+\.update',     # Dict modifications
            ]
            
            for pattern in shared_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    if 'threading.Lock' not in content:
                        report.add_race_condition(file_path, line_num, f"Shared mutable state without locking: {match.group()}")
        
        # Check for global variables in threaded code
        if 'threading' in content and 'global ' in content:
            report.add_race_condition(file_path, 0, "Global variables used in threaded code")
        
        # Check for file operations without proper locking
        if 'open(' in content and 'threading' in content:
            report.add_race_condition(file_path, 0, "File operations in threaded code without proper synchronization")
        
    except Exception as e:
        report.add_critical(file_path, 0, f"Could not analyze race conditions: {str(e)}")


def check_memory_leaks(file_path: str, report: AdvancedBugReport):
    """Check for potential memory leaks."""
    logger.info(f"Checking memory leaks for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for unclosed resources
        resource_patterns = [
            (r'cv2\.VideoCapture\(', 'VideoCapture'),
            (r'serial\.Serial\(', 'Serial connection'),
            (r'threading\.Thread\(', 'Thread'),
            (r'socket\.socket\(', 'Socket'),
            (r'open\(', 'File handle')
        ]
        
        for pattern, resource_name in resource_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                # Check if there's a corresponding close/release
                close_patterns = [
                    r'\.release\(\)',
                    r'\.close\(\)',
                    r'\.shutdown\(\)',
                    r'\.join\(\)'
                ]
                
                found_close = False
                for close_pattern in close_patterns:
                    if re.search(close_pattern, content[match.start():]):
                        found_close = True
                        break
                
                if not found_close:
                    report.add_memory_leak(file_path, line_num, f"{resource_name} may not be properly closed")
        
        # Check for large data structures that might grow indefinitely
        if 'list(' in content or 'dict(' in content:
            # Look for append operations in loops
            if 'for ' in content and '.append(' in content:
                report.add_memory_leak(file_path, 0, "Potential unbounded list growth in loop")
        
        # Check for circular references
        if 'self.' in content and '=' in content:
            # Look for self-referential assignments
            self_ref_pattern = r'self\.\w+\s*=\s*self'
            if re.search(self_ref_pattern, content):
                report.add_memory_leak(file_path, 0, "Potential circular reference detected")
        
    except Exception as e:
        report.add_critical(file_path, 0, f"Could not analyze memory leaks: {str(e)}")


def check_performance_issues(file_path: str, report: AdvancedBugReport):
    """Check for performance issues."""
    logger.info(f"Checking performance for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for inefficient patterns
        inefficient_patterns = [
            (r'for.*in.*range\(len\(', 'Inefficient loop with range(len())'),
            (r'\.append\(.*\)\s*in\s*loop', 'List append in loop - consider list comprehension'),
            (r'string\s*\+\s*string', 'String concatenation in loop - consider join()'),
            (r'if.*in.*list', 'Linear search in list - consider using set'),
            (r'\.keys\(\)\s*in\s*for', 'Unnecessary .keys() call in for loop'),
            (r'\.values\(\)\s*in\s*for', 'Unnecessary .values() call in for loop'),
        ]
        
        for pattern, message in inefficient_patterns:
            if re.search(pattern, content):
                report.add_performance_issue(file_path, 0, message)
        
        # Check for nested loops
        loop_count = content.count('for ') + content.count('while ')
        if loop_count > 3:
            report.add_performance_issue(file_path, 0, f"Multiple loops detected ({loop_count}) - potential performance issue")
        
        # Check for expensive operations in loops
        expensive_ops = ['open(', 'cv2.imread(', 'json.load(', 'requests.get(']
        for op in expensive_ops:
            if op in content and ('for ' in content or 'while ' in content):
                report.add_performance_issue(file_path, 0, f"Expensive operation {op} in loop")
        
        # Check for redundant computations
        if 'import ' in content and 'import ' in content:
            imports = re.findall(r'import (\w+)', content)
            if len(imports) != len(set(imports)):
                report.add_performance_issue(file_path, 0, "Duplicate imports detected")
        
    except Exception as e:
        report.add_critical(file_path, 0, f"Could not analyze performance: {str(e)}")


def check_code_smells(file_path: str, report: AdvancedBugReport):
    """Check for code smells and anti-patterns."""
    logger.info(f"Checking code smells for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Check for long functions
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.body) > 20:
                    report.add_code_smell(file_path, node.lineno, f"Long function '{node.name}' ({len(node.body)} lines)")
        
        # Check for long lines
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                report.add_code_smell(file_path, i, f"Long line ({len(line)} characters)")
        
        # Check for magic numbers
        magic_numbers = re.findall(r'\b\d{3,}\b', content)
        for num in magic_numbers:
            if int(num) > 100 and num not in ['1000', '1024', '2048', '4096']:
                report.add_code_smell(file_path, 0, f"Magic number: {num}")
        
        # Check for commented code
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('#') and any(keyword in line for keyword in ['def ', 'class ', 'if ', 'for ', 'while ']):
                report.add_code_smell(file_path, i, "Commented code detected")
        
        # Check for inconsistent naming
        if 'camelCase' in content or 'PascalCase' in content:
            report.add_code_smell(file_path, 0, "Inconsistent naming convention detected")
        
        # Check for deep nesting
        nesting_level = 0
        for line in lines:
            if line.strip().startswith(('if ', 'for ', 'while ', 'try:', 'except:', 'finally:', 'with ')):
                nesting_level += 1
            elif line.strip().startswith(('else:', 'elif ')):
                pass
            else:
                nesting_level = max(0, nesting_level - 1)
            
            if nesting_level > 4:
                report.add_code_smell(file_path, 0, "Deep nesting detected")
                break
        
    except Exception as e:
        report.add_critical(file_path, 0, f"Could not analyze code smells: {str(e)}")


def check_api_consistency(file_path: str, report: AdvancedBugReport):
    """Check for API consistency and design issues."""
    logger.info(f"Checking API consistency for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Check for consistent return types
        return_types = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Analyze return statements
                returns = []
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Return):
                        if stmt.value:
                            returns.append(type(stmt.value).__name__)
                        else:
                            returns.append('None')
                
                if len(set(returns)) > 2:  # Allow None and one other type
                    report.add_code_smell(file_path, node.lineno, f"Function '{node.name}' has inconsistent return types")
        
        # Check for parameter consistency
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for too many parameters
                if len(node.args.args) > 5:
                    report.add_code_smell(file_path, node.lineno, f"Function '{node.name}' has many parameters ({len(node.args.args)})")
        
        # Check for method naming consistency
        method_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_names.append(node.name)
        
        # Check for inconsistent naming patterns
        if method_names:
            patterns = [name.split('_') for name in method_names]
            if len(set(len(pattern) for pattern in patterns)) > 2:
                report.add_code_smell(file_path, 0, "Inconsistent method naming patterns")
        
    except Exception as e:
        report.add_critical(file_path, 0, f"Could not analyze API consistency: {str(e)}")


def check_error_handling_patterns(file_path: str, report: AdvancedBugReport):
    """Check for error handling patterns and issues."""
    logger.info(f"Checking error handling for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Check for missing error handling in critical operations
        critical_ops = [
            'open(', 'cv2.VideoCapture', 'serial.Serial', 'json.load', 'json.dump',
            'requests.get', 'requests.post', 'socket.socket', 'threading.Thread'
        ]
        
        for op in critical_ops:
            if op in content:
                # Check if there's error handling around this operation
                op_index = content.find(op)
                if op_index != -1:
                    # Look for try-except in the surrounding context
                    context_start = max(0, op_index - 500)
                    context_end = min(len(content), op_index + 500)
                    context = content[context_start:context_end]
                    
                    if 'try:' not in context or 'except' not in context:
                        line_num = content[:op_index].count('\n') + 1
                        report.add_logic_error(file_path, line_num, f"Critical operation {op} without error handling")
        
        # Check for exception swallowing
        for i, line in enumerate(lines, 1):
            if 'except:' in line and 'pass' in line:
                report.add_logic_error(file_path, i, "Exception swallowed with bare except and pass")
        
        # Check for proper exception hierarchy
        for i, line in enumerate(lines, 1):
            if 'except Exception as e:' in line:
                # Check if it's followed by specific exception handling
                next_lines = lines[i:i+5]
                if not any('except ' in next_line for next_line in next_lines):
                    report.add_suggestion(file_path, i, "Consider catching specific exceptions before general Exception")
        
    except Exception as e:
        report.add_critical(file_path, 0, f"Could not analyze error handling: {str(e)}")


def check_resource_management(file_path: str, report: AdvancedBugReport):
    """Check for resource management issues."""
    logger.info(f"Checking resource management for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for proper context manager usage
        if 'open(' in content:
            # Count open() calls vs with statements
            open_calls = content.count('open(')
            with_statements = content.count('with ')
            
            if open_calls > with_statements:
                report.add_memory_leak(file_path, 0, "File operations without context managers")
        
        # Check for proper cleanup in __init__ and __del__
        if '__init__' in content:
            # Check if __init__ properly initializes resources
            if 'self.' in content and '=' in content:
                # Look for resource initialization
                resource_patterns = ['cv2.VideoCapture', 'serial.Serial', 'threading.Thread']
                for pattern in resource_patterns:
                    if pattern in content:
                        # Check if there's cleanup in __del__ or close method
                        if '__del__' not in content and 'close(' not in content:
                            report.add_memory_leak(file_path, 0, f"Resource {pattern} initialized but no cleanup method found")
        
        # Check for proper exception handling in cleanup
        if '__del__' in content or 'close(' in content:
            if 'try:' not in content or 'except' not in content:
                report.add_logic_error(file_path, 0, "Cleanup method without error handling")
        
    except Exception as e:
        report.add_critical(file_path, 0, f"Could not analyze resource management: {str(e)}")


def check_threading_safety(file_path: str, report: AdvancedBugReport):
    """Check for threading safety issues."""
    logger.info(f"Checking threading safety for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for thread-unsafe operations
        if 'threading' in content:
            # Look for shared state modifications
            shared_patterns = [
                r'self\.\w+\s*=\s*\w+',  # Direct assignment
                r'self\.\w+\s*\+=',       # Increment
                r'self\.\w+\s*-=',        # Decrement
                r'self\.\w+\.append',     # List modification
                r'self\.\w+\.extend',     # List modification
                r'self\.\w+\.update',     # Dict modification
            ]
            
            for pattern in shared_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    # Check if there's proper synchronization
                    if 'threading.Lock' not in content and 'threading.RLock' not in content:
                        report.add_race_condition(file_path, line_num, f"Thread-unsafe operation: {match.group()}")
        
        # Check for proper thread cleanup
        if 'threading.Thread' in content:
            if '.join()' not in content:
                report.add_memory_leak(file_path, 0, "Threads created but not joined")
        
        # Check for deadlock potential
        if 'threading.Lock' in content and 'threading.Lock' in content:
            # Multiple locks without proper ordering
            report.add_race_condition(file_path, 0, "Multiple locks detected - potential deadlock")
        
    except Exception as e:
        report.add_critical(file_path, 0, f"Could not analyze threading safety: {str(e)}")


def check_data_validation(file_path: str, report: AdvancedBugReport):
    """Check for data validation issues."""
    logger.info(f"Checking data validation for {file_path}...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Check for missing input validation
        input_patterns = [
            r'def \w+\([^)]*\):',
            r'input\(',
            r'cv2\.VideoCapture\(',
            r'serial\.Serial\(',
        ]
        
        for pattern in input_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                # Check if there's validation after this
                context = content[match.start():match.start() + 1000]
                if not any(validation in context for validation in ['if ', 'assert ', 'isinstance(', 'len(']):
                    report.add_logic_error(file_path, line_num, f"Missing input validation for {pattern}")
        
        # Check for division by zero
        for i, line in enumerate(lines, 1):
            if '/' in line and re.search(r'/\s*[a-zA-Z_][a-zA-Z0-9_]*', line):
                # Check if divisor is validated
                if 'if ' not in line and 'assert ' not in line:
                    report.add_logic_error(file_path, i, "Potential division by zero - validate divisor")
        
        # Check for array bounds
        for i, line in enumerate(lines, 1):
            if '[' in line and ']' in line:
                # Look for array access
                if re.search(r'\[[a-zA-Z_][a-zA-Z0-9_]*\]', line):
                    # Check if index is validated
                    if 'if ' not in line and 'assert ' not in line:
                        report.add_logic_error(file_path, i, "Array access without bounds checking")
        
    except Exception as e:
        report.add_critical(file_path, 0, f"Could not analyze data validation: {str(e)}")


def run_advanced_bug_check():
    """Run advanced bug checking on all SDK files."""
    logger.info("Starting advanced bug check...")
    
    report = AdvancedBugReport()
    
    # Files to check
    python_files = ['camera.py', 'lidar.py', 'main.py']
    
    for file_path in python_files:
        if not Path(file_path).exists():
            report.add_critical(file_path, 0, "File not found")
            continue
        
        logger.info(f"\n--- Advanced Analysis of {file_path} ---")
        
        # Run all advanced checks
        check_logic_errors(file_path, report)
        check_race_conditions(file_path, report)
        check_memory_leaks(file_path, report)
        check_performance_issues(file_path, report)
        check_code_smells(file_path, report)
        check_api_consistency(file_path, report)
        check_error_handling_patterns(file_path, report)
        check_resource_management(file_path, report)
        check_threading_safety(file_path, report)
        check_data_validation(file_path, report)
    
    # Generate summary
    return report.summary()


if __name__ == "__main__":
    success = run_advanced_bug_check()
    sys.exit(0 if success else 1)