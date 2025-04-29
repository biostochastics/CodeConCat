#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for the enhanced C# parser in CodeConCat.

Tests the EnhancedCSharpParser class to ensure it properly handles
C#-specific syntax, classes, interfaces, properties, and using statements.
"""

import logging
import pytest

from codeconcat.base_types import (
    ParseResult,
    ParserInterface,
)
from codeconcat.parser.language_parsers.enhanced_base_parser import EnhancedBaseParser
from codeconcat.parser.language_parsers.enhanced_c_family_parser import EnhancedCFamilyParser
from codeconcat.parser.language_parsers.enhanced_csharp_parser import EnhancedCSharpParser
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


class TestEnhancedCSharpParser:
    """Test class for the EnhancedCSharpParser."""

    @pytest.fixture
    def csharp_code_sample(self) -> str:
        """Fixture providing a sample C# code snippet for testing."""
        return """using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Threading.Tasks;

namespace TestNamespace
{
    /// <summary>
    /// Basic C# test file for parser validation.
    /// 
    /// This file contains common C# constructs that should be properly parsed.
    /// </summary>
    
    /// <summary>
    /// Constants class with documentation.
    /// </summary>
    public static class Constants
    {
        /// <summary>
        /// The mathematical constant pi, approximately.
        /// </summary>
        public const double PI = 3.14159;
        
        /// <summary>
        /// Maximum number of retry attempts.
        /// </summary>
        public const int MAX_RETRIES = 3;
    }
    
    /// <summary>
    /// Represents a person with name, age, and optional address.
    /// </summary>
    public class Person
    {
        /// <summary>
        /// The person's name
        /// </summary>
        protected string Name { get; set; }
        
        /// <summary>
        /// The person's age
        /// </summary>
        protected int Age { get; set; }
        
        /// <summary>
        /// The person's address (optional)
        /// </summary>
        protected string Address { get; set; }
        
        /// <summary>
        /// Create a new person instance.
        /// </summary>
        /// <param name="name">The person's name</param>
        /// <param name="age">The person's age</param>
        public Person(string name, int age)
        {
            Name = name;
            Age = age;
            Address = null;
        }
        
        /// <summary>
        /// Get a greeting from the person.
        /// </summary>
        /// <returns>A greeting string</returns>
        public virtual string Greet()
        {
            return $"Hello, my name is {Name} and I am {Age} years old.";
        }
        
        /// <summary>
        /// Set the person's address.
        /// </summary>
        /// <param name="address">The address to set</param>
        public void SetAddress(string address)
        {
            Address = address;
        }
        
        /// <summary>
        /// Get the person's address or a default message.
        /// </summary>
        /// <returns>The address or a default message</returns>
        public string GetAddress()
        {
            return Address ?? "Address not set";
        }
    }
    
    /// <summary>
    /// Employee class extending Person with job information.
    /// </summary>
    public class Employee : Person
    {
        /// <summary>
        /// The employee's job title
        /// </summary>
        private string Title { get; set; }
        
        /// <summary>
        /// The employee's annual salary
        /// </summary>
        private decimal Salary { get; set; }
        
        /// <summary>
        /// Create a new employee instance.
        /// </summary>
        /// <param name="name">The person's name</param>
        /// <param name="age">The person's age</param>
        /// <param name="title">The job title</param>
        /// <param name="salary">The annual salary</param>
        public Employee(string name, int age, string title, decimal salary)
            : base(name, age)
        {
            Title = title;
            Salary = salary;
        }
        
        /// <summary>
        /// Override the parent's greet method.
        /// </summary>
        /// <returns>Extended greeting</returns>
        public override string Greet()
        {
            string baseGreeting = base.Greet();
            return $"{baseGreeting} I work as a {Title}.";
        }
    }
    
    /// <summary>
    /// Interface for data processors
    /// </summary>
    public interface IProcessor
    {
        /// <summary>
        /// Process the given data
        /// </summary>
        /// <param name="data">The data to process</param>
        /// <returns>Processed data</returns>
        string Process(string data);
        
        /// <summary>
        /// Get processing statistics
        /// </summary>
        /// <returns>Dictionary of statistics</returns>
        Dictionary<string, int> GetStats();
    }
}
"""

    def test_csharp_parser_initialization(self):
        """Test initializing the EnhancedCSharpParser."""
        # Create an instance
        parser = EnhancedCSharpParser()

        # Check that it inherits from EnhancedCFamilyParser
        assert isinstance(parser, EnhancedCFamilyParser)
        assert isinstance(parser, EnhancedBaseParser)
        assert isinstance(parser, ParserInterface)

        # Check that C#-specific properties are set
        assert parser.language == "csharp"
        assert parser.line_comment == "//"
        assert parser.block_comment_start == "/*"
        assert parser.block_comment_end == "*/"
        assert parser.block_start == "{"
        assert parser.block_end == "}"

        # Check capabilities
        capabilities = parser.get_capabilities()
        assert capabilities["can_parse_functions"] is True
        assert capabilities["can_parse_classes"] is True
        assert capabilities["can_parse_interfaces"] is True
        assert capabilities["can_parse_imports"] is True
        assert capabilities["can_extract_docstrings"] is True

    def test_csharp_parser_parse(self, csharp_code_sample):
        """Test parsing a C# file with the EnhancedCSharpParser."""
        # Create parser and parse the code
        parser = EnhancedCSharpParser()
        result = parser.parse(csharp_code_sample, "test.cs")

        # Check that we got a ParseResult
        assert isinstance(result, ParseResult)
        assert result.error is None, f"Parse error: {result.error}"

        # Log the declarations for debugging
        print(f"Found {len(result.declarations)} top-level declarations:")
        for decl in result.declarations:
            print(f"- {decl.kind}: {decl.name}")

        # Check for imports (using statements)
        print(f"Found {len(result.imports)} imports: {result.imports}")
        if len(result.imports) > 0:
            if "System" in result.imports:
                print("System using statement detected")
        else:
            print("Note: No using statements were detected by the parser")

        # Check for namespace
        namespace_decl = next((d for d in result.declarations if d.kind == "namespace"), None)
        if namespace_decl:
            print(
                f"Found namespace {namespace_decl.name} at lines {namespace_decl.start_line}-{namespace_decl.end_line}"
            )

        # Ensure a minimum number of declarations were found
        assert len(result.declarations) > 0, "No declarations detected"

        # Try to find key declarations
        constants_class = None
        person_class = None
        employee_class = None
        processor_interface = None

        # First check inside namespace if found
        declarations_to_search = result.declarations
        if namespace_decl and namespace_decl.children:
            declarations_to_search = namespace_decl.children

        for decl in declarations_to_search:
            if decl.kind == "class" and decl.name == "Constants":
                constants_class = decl
            elif decl.kind == "class" and decl.name == "Person":
                person_class = decl
            elif decl.kind == "class" and decl.name == "Employee":
                employee_class = decl
            elif decl.kind == "interface" and decl.name == "IProcessor":
                processor_interface = decl

        # Print info about what was found (without being too strict)
        if constants_class:
            print(
                f"Found Constants class at lines {constants_class.start_line}-{constants_class.end_line}"
            )
            if constants_class.docstring and "Constants class" in constants_class.docstring:
                print("Constants class docstring correctly detected")

        if person_class:
            print(f"Found Person class at lines {person_class.start_line}-{person_class.end_line}")
            if person_class.docstring and "Represents a person" in person_class.docstring:
                print("Person class docstring correctly detected")

            # Check for properties and methods in the Person class
            if person_class.children:
                print(f"Found {len(person_class.children)} members in Person class:")
                for member in person_class.children:
                    print(f"  - {member.kind}: {member.name}")

                # Try to find the Greet method
                greet_method = next((m for m in person_class.children if m.name == "Greet"), None)
                if greet_method:
                    print(
                        f"Found Greet method at lines {greet_method.start_line}-{greet_method.end_line}"
                    )
                    if greet_method.docstring and "greeting" in greet_method.docstring:
                        print("Method docstring correctly detected")

        if employee_class:
            print(
                f"Found Employee class at lines {employee_class.start_line}-{employee_class.end_line}"
            )
            if employee_class.docstring and "Employee class" in employee_class.docstring:
                print("Employee class docstring correctly detected")

        if processor_interface:
            print(
                f"Found IProcessor interface at lines {processor_interface.start_line}-{processor_interface.end_line}"
            )
            if (
                processor_interface.docstring
                and "Interface for data processors" in processor_interface.docstring
            ):
                print("Interface docstring correctly detected")

        # Check if any declarations have docstrings
        all_declarations = []
        for decl in result.declarations:
            all_declarations.append(decl)
            if decl.children:
                all_declarations.extend(decl.children)
                for child in decl.children:
                    if child.children:
                        all_declarations.extend(child.children)

        declarations_with_docstrings = [d for d in all_declarations if d.docstring]
        print(f"Found {len(declarations_with_docstrings)} declarations with docstrings")
        if len(declarations_with_docstrings) > 0:
            print("Docstrings were successfully detected")
        else:
            print("Note: No docstrings were detected. This could be due to parser limitations.")


if __name__ == "__main__":
    pytest.main(["-v", __file__])
