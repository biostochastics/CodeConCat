#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for the enhanced Python parser in CodeConCat.

Tests the EnhancedPythonParser class to ensure it properly handles 
Python-specific syntax, classes, functions, nested declarations, imports, and docstrings.
"""

import os
import logging
import pytest
from typing import List, Dict, Any, Optional

from codeconcat.base_types import (
    CodeConCatConfig,
    Declaration,
    ParseResult,
    ParserInterface,
)
from codeconcat.parser.language_parsers.enhanced_base_parser import EnhancedBaseParser
from codeconcat.parser.language_parsers.enhanced_python_parser import EnhancedPythonParser
from codeconcat.parser.enable_debug import enable_all_parser_debug_logging

# Enable debug logging for all parsers
enable_all_parser_debug_logging()

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestEnhancedPythonParser:
    """Test class for the EnhancedPythonParser."""
    
    @pytest.fixture
    def python_code_sample(self) -> str:
        """Fixture providing a sample Python code snippet for testing."""
        return '''"""
Module level docstring for a sample Python file.
This file contains common Python constructs that should be properly parsed.
"""

import os
import sys
from typing import List, Dict, Optional, Any
from datetime import datetime

# Constants with documentation
PI = 3.14159  # Mathematical constant pi
MAX_RETRIES = 3  # Maximum number of retry attempts

# Global variables
default_timeout = 30
app_name = "TestApp"

class Person:
    """Represents a human with name and age."""
    
    def __init__(self, name: str, age: int):
        """Initialize a new Person instance.
        
        Args:
            name: The person's name
            age: The person's age
        """
        self.name = name
        self.age = age
        self.address = None
    
    def greet(self) -> str:
        """Return a greeting message from the person.
        
        Returns:
            A greeting string including the person's name
        """
        return f"Hello, my name is {self.name} and I am {self.age} years old."
    
    def set_address(self, address: str) -> None:
        """Set the person's address.
        
        Args:
            address: The address to set
        """
        self.address = address
        
        # Example of a nested function
        def log_change():
            """Log that an address change occurred."""
            print(f"Address changed to {address}")
        
        log_change()
    
    @property
    def info(self) -> Dict[str, Any]:
        """Get basic info about the person.
        
        Returns:
            Dictionary of basic person info
        """
        return {
            "name": self.name,
            "age": self.age,
            "address": self.address or "Not set"
        }


class Employee(Person):
    """Employee extends Person with job-related fields."""
    
    def __init__(self, name: str, age: int, title: str, salary: float):
        """Initialize a new Employee instance.
        
        Args:
            name: The person's name
            age: The person's age
            title: The job title
            salary: The annual salary
        """
        super().__init__(name, age)
        self.title = title
        self.salary = salary
    
    def work_info(self) -> str:
        """Return information about the employee's job.
        
        Returns:
            A string with job details
        """
        return f"I work as a {self.title} and earn {self.salary} per year."
    
    def greet(self) -> str:
        """Override the parent's greet method.
        
        Returns:
            An extended greeting including job info
        """
        base_greeting = super().greet()
        return f"{base_greeting} I work as a {self.title}."


def calculate_stats(numbers: List[int]) -> Dict[str, float]:
    """Calculate statistics for a list of numbers.
    
    Args:
        numbers: List of integers to analyze
        
    Returns:
        Dictionary with min, max, and average values
    """
    if not numbers:
        return {"min": 0, "max": 0, "avg": 0}
    
    return {
        "min": min(numbers),
        "max": max(numbers),
        "avg": sum(numbers) / len(numbers)
    }


def divide(a: int, b: int) -> Optional[int]:
    """Divide two numbers, handling the case of division by zero.
    
    Args:
        a: The dividend
        b: The divisor
        
    Returns:
        The result of a/b or None if b is zero
    """
    try:
        return a // b
    except ZeroDivisionError:
        print("Cannot divide by zero")
        return None


if __name__ == "__main__":
    # Create a person
    p = Person("John", 30)
    p.set_address("123 Main St")
    print(p.greet())
    
    # Create an employee
    e = Employee("Jane", 28, "Software Engineer", 100000)
    print(e.work_info())
    print(e.greet())
    
    # Use standalone functions
    numbers = [3, 7, 2, 9, 5]
    stats = calculate_stats(numbers)
    print(f"Stats: {stats}")
    
    result = divide(10, 2)
    print(f"10 / 2 = {result}")
'''
    
    def test_python_parser_initialization(self):
        """Test initializing the EnhancedPythonParser."""
        # Create an instance
        parser = EnhancedPythonParser()
        
        # Check that it inherits from EnhancedBaseParser
        assert isinstance(parser, EnhancedBaseParser)
        assert isinstance(parser, ParserInterface)
        
        # Check that Python-specific properties are set
        assert parser.language == "python"
        assert parser.line_comment == "#"
        assert parser.block_comment_start == '"""'
        assert parser.block_comment_end == '"""'
        assert parser.block_start == ":"
        assert parser.block_end is None  # Python uses indentation
        
        # Check capabilities
        capabilities = parser.get_capabilities()
        assert capabilities["can_parse_functions"] is True
        assert capabilities["can_parse_classes"] is True
        assert capabilities["can_parse_imports"] is True
        assert capabilities["can_extract_docstrings"] is True
    
    def test_python_parser_parse(self, python_code_sample):
        """Test parsing a Python file with the EnhancedPythonParser."""
        # Create parser and parse the code
        parser = EnhancedPythonParser()
        result = parser.parse(python_code_sample, "test.py")
        
        # Check that we got a ParseResult
        assert isinstance(result, ParseResult)
        assert result.error is None, f"Parse error: {result.error}"
        
        # Log the declarations for debugging
        print(f"Found {len(result.declarations)} top-level declarations:")
        for decl in result.declarations:
            print(f"- {decl.kind}: {decl.name}")
        
        # Check for imports
        print(f"Found {len(result.imports)} imports: {result.imports}")
        assert len(result.imports) > 0, "No imports were detected"
        assert "os" in result.imports, "os import not detected"
        assert "typing" in result.imports, "typing import not detected"
        
        # Ensure a minimum number of declarations were found
        assert len(result.declarations) > 0, "No declarations detected"
        
        # Try to find key declarations
        person_class = None
        employee_class = None
        calculate_stats_func = None
        
        for decl in result.declarations:
            if decl.kind == "class" and decl.name == "Person":
                person_class = decl
            elif decl.kind == "class" and decl.name == "Employee":
                employee_class = decl
            elif decl.kind == "function" and decl.name == "calculate_stats":
                calculate_stats_func = decl
        
        # Check if key declarations were found
        assert person_class is not None, "Person class not found"
        assert employee_class is not None, "Employee class not found"
        assert calculate_stats_func is not None, "calculate_stats function not found"
        
        # Print info about what was found
        print(f"Found Person class at lines {person_class.start_line}-{person_class.end_line}")
        if person_class.docstring:
            assert "Represents a human" in person_class.docstring
            print("Person class docstring correctly detected")
        
        print(f"Found Employee class at lines {employee_class.start_line}-{employee_class.end_line}")
        if employee_class.docstring:
            assert "Employee extends Person" in employee_class.docstring
            print("Employee class docstring correctly detected")
        
        print(f"Found calculate_stats function at lines {calculate_stats_func.start_line}-{calculate_stats_func.end_line}")
        if calculate_stats_func.docstring:
            assert "Calculate statistics" in calculate_stats_func.docstring
            print("Function docstring correctly detected")
        
        # Check for methods in Person class
        if person_class.children:
            print(f"Found {len(person_class.children)} methods in Person class:")
            for method in person_class.children:
                print(f"  - {method.kind}: {method.name}")
            
            # Try to find specific methods
            init_method = next((m for m in person_class.children if m.name == "__init__"), None)
            greet_method = next((m for m in person_class.children if m.name == "greet"), None)
            set_address_method = next((m for m in person_class.children if m.name == "set_address"), None)
            
            assert init_method is not None, "__init__ method not found in Person class"
            assert greet_method is not None, "greet method not found in Person class"
            assert set_address_method is not None, "set_address method not found in Person class"
            
            # Check for nested functions
            if set_address_method.children:
                print(f"Found {len(set_address_method.children)} nested functions in set_address method:")
                for nested_func in set_address_method.children:
                    print(f"  - {nested_func.kind}: {nested_func.name}")
                
                # Try to find specific nested function
                log_change_func = next((f for f in set_address_method.children if f.name == "log_change"), None)
                if log_change_func:
                    print(f"Found nested log_change function at lines {log_change_func.start_line}-{log_change_func.end_line}")
                    if log_change_func.docstring:
                        assert "Log that an address change" in log_change_func.docstring
                        print("Nested function docstring correctly detected")
        
        # Check that at least some declarations have docstrings
        declarations_with_docstrings = [d for d in result.declarations if d.docstring]
        print(f"Found {len(declarations_with_docstrings)} declarations with docstrings")
        assert len(declarations_with_docstrings) > 0, "No docstrings were detected"
    
    def test_python_parser_nested_declarations(self, python_code_sample):
        """Test the Enhanced Python parser's ability to detect nested declarations."""
        # Create parser and parse the code
        parser = EnhancedPythonParser()
        result = parser.parse(python_code_sample, "test.py")
        
        # Check that we got a ParseResult
        assert isinstance(result, ParseResult)
        assert result.error is None, f"Parse error: {result.error}"
        
        # Find all declarations with children (nested declarations)
        declarations_with_children = [d for d in result.declarations if d.children]
        print(f"Found {len(declarations_with_children)} declarations with children (nested declarations)")
        
        # Create a tree of declarations for visualization
        def print_declaration_tree(declaration, indent=0):
            indent_str = "  " * indent
            print(f"{indent_str}- {declaration.kind}: {declaration.name}")
            if declaration.children:
                for child in declaration.children:
                    print_declaration_tree(child, indent + 1)
        
        print("\nDeclaration tree:")
        for decl in result.declarations:
            print_declaration_tree(decl)
        
        # Check that Person class has methods
        person_class = next((d for d in result.declarations if d.kind == "class" and d.name == "Person"), None)
        assert person_class is not None, "Person class not found"
        assert len(person_class.children) > 0, "Person class has no methods (children)"
        
        # Check that set_address method has nested function
        set_address_method = next((m for m in person_class.children if m.name == "set_address"), None)
        assert set_address_method is not None, "set_address method not found in Person class"
        assert len(set_address_method.children) > 0, "set_address method has no nested functions"
        
        # Check that log_change is a nested function in set_address
        log_change_func = next((f for f in set_address_method.children if f.name == "log_change"), None)
        assert log_change_func is not None, "log_change nested function not found in set_address method"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
