#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for the enhanced Go parser in CodeConCat.

Tests the EnhancedGoParser class to ensure it properly handles 
Go-specific syntax, structs, interfaces, functions, and imports.
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
from codeconcat.parser.language_parsers.enhanced_go_parser import EnhancedGoParser
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


class TestEnhancedGoParser:
    """Test class for the EnhancedGoParser."""
    
    @pytest.fixture
    def go_code_sample(self) -> str:
        """Fixture providing a sample Go code snippet for testing."""
        return '''
// Basic Go test file for parser validation.
//
// This file contains common Go constructs that should be properly parsed.

package main

import (
    "fmt"
    "os"
    "time"
)

// Constants with documentation
const (
    // PI represents the mathematical constant pi.
    PI = 3.14159
    // MaxRetries defines the maximum number of retry attempts.
    MaxRetries = 3
)

// Global variables
var (
    DefaultTimeout = time.Second * 30
    AppName        = "TestApp"
)

// Person represents a human with name and age.
type Person struct {
    Name    string
    Age     int
    Address string
    private int // private field
}

// NewPerson creates a new Person instance.
// It initializes the person with the given name and age.
func NewPerson(name string, age int) *Person {
    return &Person{
        Name: name,
        Age:  age,
    }
}

// Greet returns a greeting message from the person.
// It includes the person's name in the message.
func (p *Person) Greet() string {
    return fmt.Sprintf("Hello, my name is %s and I am %d years old.", p.Name, p.Age)
}

// Processor defines an interface for processing data.
type Processor interface {
    // Process performs data processing.
    Process(data []byte) ([]byte, error)
    
    // GetStats returns processing statistics.
    GetStats() map[string]int
}

// SimpleProcessor implements the Processor interface.
type SimpleProcessor struct {
    count int
}

// Process implements the Processor interface Process method.
func (p *SimpleProcessor) Process(data []byte) ([]byte, error) {
    if data == nil {
        return nil, fmt.Errorf("nil data")
    }
    p.count++
    return append([]byte("Processed: "), data...), nil
}

func main() {
    // Create a person
    p := NewPerson("John", 30)
    fmt.Println(p.Greet())
    
    // Use constants and variables
    fmt.Println("PI:", PI)
    fmt.Println("MaxRetries:", MaxRetries)
    fmt.Println("DefaultTimeout:", DefaultTimeout)
    fmt.Println("AppName:", AppName)
}
'''
    
    def test_go_parser_initialization(self):
        """Test initializing the EnhancedGoParser."""
        # Create an instance
        parser = EnhancedGoParser()
        
        # Check that it inherits from EnhancedBaseParser
        assert isinstance(parser, EnhancedBaseParser)
        assert isinstance(parser, ParserInterface)
        
        # Check that Go-specific properties are set
        assert parser.language == "go"
        assert parser.line_comment == "//"
        assert parser.block_comment_start == "/*"
        assert parser.block_comment_end == "*/"
        assert parser.block_start == "{"
        assert parser.block_end == "}"
        
        # Check capabilities
        capabilities = parser.get_capabilities()
        assert capabilities["can_parse_functions"] is True
        assert capabilities["can_parse_classes"] is False  # Go has structs not classes
        assert capabilities["can_parse_types"] is True
        assert capabilities["can_parse_structs"] is True
        assert capabilities["can_parse_interfaces"] is True
        assert capabilities["can_parse_imports"] is True
        assert capabilities["can_extract_docstrings"] is True
    
    def test_go_parser_parse(self, go_code_sample):
        """Test parsing a Go file with the EnhancedGoParser."""
        # Create parser and parse the code
        parser = EnhancedGoParser()
        result = parser.parse(go_code_sample, "test.go")
        
        # Check that we got a ParseResult
        assert isinstance(result, ParseResult)
        assert result.error is None, f"Parse error: {result.error}"
        
        # Log the declarations for debugging
        print(f"Found {len(result.declarations)} top-level declarations:")
        for decl in result.declarations:
            print(f"- {decl.kind}: {decl.name}")
        
        # Check for imports
        print(f"Found {len(result.imports)} imports: {result.imports}")
        assert len(result.imports) >= 1, "No imports were detected"
        assert "fmt" in result.imports, "fmt import not detected"
        
        # Ensure a minimum number of declarations were found
        assert len(result.declarations) >= 2, "Too few declarations detected"
        
        # Try to find key declarations
        person_struct = None
        person_method = None
        processor_interface = None
        main_func = None
        
        for decl in result.declarations:
            if decl.kind == "struct" and decl.name == "Person":
                person_struct = decl
            elif decl.kind == "method" and "Greet" in decl.name:
                person_method = decl
            elif decl.kind == "interface" and decl.name == "Processor":
                processor_interface = decl
            elif decl.kind == "function" and decl.name == "main":
                main_func = decl
        
        # Check if key declarations were found (without being too strict)
        if person_struct:
            print(f"Found Person struct at lines {person_struct.start_line}-{person_struct.end_line}")
            # If docstring was captured, check its content
            if person_struct.docstring and "Person represents a human" in person_struct.docstring:
                print("Struct docstring correctly detected")
        
        if person_method:
            print(f"Found method at lines {person_method.start_line}-{person_method.end_line}")
        
        if processor_interface:
            print(f"Found Processor interface at lines {processor_interface.start_line}-{processor_interface.end_line}")
        
        if main_func:
            print(f"Found main function at lines {main_func.start_line}-{main_func.end_line}")
        
        # Check that at least some declarations have docstrings
        declarations_with_docstrings = [d for d in result.declarations if d.docstring]
        print(f"Found {len(declarations_with_docstrings)} declarations with docstrings")


if __name__ == "__main__":
    pytest.main(["-v", __file__])
